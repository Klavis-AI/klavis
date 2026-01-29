import { z } from 'zod';
import { listFiles, spaceInfo } from '@huggingface/hub';
import { formatBytes, escapeMarkdown } from './utilities.js';
import { HfApiError } from './hf-api-call.js';
import { explain } from './error-messages.js';

// Define the FileWithUrl interface
export interface FileWithUrl {
	path: string;
	size: number;
	type: 'file' | 'directory' | 'unknown';
	url: string;
	sizeFormatted: string;
	lastModified?: string;
	lfs: boolean;
}

// File type detection helpers
const IMAGE_EXTENSIONS = new Set([
	'.jpg',
	'.jpeg',
	'.png',
	'.gif',
	'.bmp',
	'.tiff',
	'.tif',
	'.webp',
	'.svg',
	'.ico',
	'.heic',
	'.heif',
]);

const AUDIO_EXTENSIONS = new Set([
	'.mp3',
	'.wav',
	'.flac',
	'.aac',
	'.ogg',
	'.m4a',
	'.wma',
	'.opus',
	'.aiff',
	'.au',
	'.ra',
]);

function getFileExtension(path: string): string {
	const lastDot = path.lastIndexOf('.');
	return lastDot === -1 ? '' : path.substring(lastDot).toLowerCase();
}

function isImageFile(path: string): boolean {
	return IMAGE_EXTENSIONS.has(getFileExtension(path));
}

function isAudioFile(path: string): boolean {
	return AUDIO_EXTENSIONS.has(getFileExtension(path));
}

function matchesFileType(file: FileWithUrl, fileType: 'all' | 'image' | 'audio'): boolean {
	switch (fileType) {
		case 'all':
			return true;
		case 'image':
			return isImageFile(file.path);
		case 'audio':
			return isAudioFile(file.path);
		default:
			return true;
	}
}

// Tool configuration
export const SPACE_FILES_TOOL_CONFIG = {
	name: 'space_files',
	description: '', // This will be dynamically set with username
	schema: z.object({
		spaceName: z.string().optional().describe('Space identifier in format "username/spacename"'),
		fileType: z
			.enum(['all', 'image', 'audio'])
			.optional()
			.default('all')
			.describe('Filter files by type: all (default), image, or audio files only'),
	}),
	annotations: {
		title: 'Space Files List',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: true,
	},
} as const;

// Define parameter types
export type SpaceFilesParams = z.infer<typeof SPACE_FILES_TOOL_CONFIG.schema>;

/**
 * Service for listing files in Hugging Face Spaces
 */
export class SpaceFilesTool {
	private readonly accessToken?: string;
	private readonly username?: string;

	constructor(hfToken?: string, username?: string) {
		this.accessToken = hfToken;
		this.username = username;
	}

	static createToolConfig(username?: string): typeof SPACE_FILES_TOOL_CONFIG {
		const description = username
			? `Defaults to ${username}/filedrop. List files in a static Hugging Face Space. Use the URL for specifying Files inputs to Gradio endpoints or downloading files`
			: `List all files in a static Hugging Face Space. Use the URL for specifying Files inputs to Gradio endpoints or downloading files.`;
		return {
			...SPACE_FILES_TOOL_CONFIG,
			description: description as '',
		};
	}

	/**
	 * Get all files in a space with their URLs
	 */
	async getSpaceFilesWithUrls(spaceName: string): Promise<FileWithUrl[]> {
		try {
			// Get space info to determine subdomain
			const space = await spaceInfo({
				name: spaceName,
				additionalFields: ['subdomain'],
				...(this.accessToken && { accessToken: this.accessToken }),
			});

			// Check if it's a static space
			if (space.sdk !== 'static') {
				throw new Error(
					`Space "${spaceName}" is not a static space (found: ${space.sdk}). This tool only works with static spaces.`
				);
			}

			const files: FileWithUrl[] = [];

			// List all files recursively
			for await (const file of listFiles({
				repo: { type: 'space', name: spaceName },
				recursive: true,
				expand: true, // Get last commit info
				...(this.accessToken && { credentials: { accessToken: this.accessToken } }),
			})) {
				if (file.type === 'file') {
					files.push({
						path: file.path,
						size: file.size,
						type: file.type,
						url: this.constructFileUrl(spaceName, file.path),
						sizeFormatted: formatBytes(file.size),
						lastModified: file.lastCommit?.date,
						lfs: !!file.lfs,
					});
				}
			}

			return files.sort((a, b) => a.path.localeCompare(b.path));
		} catch (error) {
			if (error instanceof HfApiError) {
				throw explain(error, `Failed to list files for space "${spaceName}"`);
			}
			throw error;
		}
	}

	/**
	 * Construct the URL for a file
	 */
	private constructFileUrl(spaceName: string, filePath: string): string {
		return `https://huggingface.co/spaces/${spaceName}/resolve/main/${filePath}`;
	}

	/**
	 * Generate detailed markdown report with files grouped by directory
	 */
	async generateDetailedMarkdown(spaceName: string, fileType: 'all' | 'image' | 'audio' = 'all'): Promise<string> {
		const allFiles = await this.getSpaceFilesWithUrls(spaceName);
		const files = allFiles.filter((file) => matchesFileType(file, fileType));

		let markdown = `# Files in Space: ${spaceName}\n\n`;
		if (fileType !== 'all') {
			markdown += `**Filter**: ${fileType} files only\n`;
		}
		markdown += `**Total Files**: ${files.length}\n`;
		markdown += `**Total Size**: ${formatBytes(files.reduce((sum, f) => sum + f.size, 0))}\n\n`;

		// Handle empty results
		if (files.length === 0) {
			if (fileType !== 'all') {
				markdown += `No ${fileType} files found in this space.\n`;
			} else {
				markdown += `No files found in this space.\n`;
			}
			return markdown;
		}

		// Group files by directory
		const byDirectory = files.reduce(
			(acc, file) => {
				const dir = file.path.includes('/') ? file.path.substring(0, file.path.lastIndexOf('/')) : '/';
				if (!acc[dir]) acc[dir] = [];
				acc[dir].push(file);
				return acc;
			},
			{} as Record<string, FileWithUrl[]>
		);

		// Generate table
		markdown += `## All Files\n\n`;
		markdown += `| File Path | Size | Type | Last Modified | URL |\n`;
		markdown += `|-----------|------|------|---------------|-----|\n`;

		// Sort directories and output files
		const sortedDirs = Object.keys(byDirectory).sort();
		for (const dir of sortedDirs) {
			const dirFiles = byDirectory[dir];
			if (!dirFiles) continue;

			if (dir !== '/' && dirFiles.length > 0) {
				markdown += `| **📁 ${escapeMarkdown(dir)}/** | | | | |\n`;
			}

			for (const file of dirFiles) {
				const fileName = file.path.split('/').pop() || file.path;
				const indent = dir === '/' ? '' : '&nbsp;&nbsp;&nbsp;&nbsp;';
				const icon = this.getFileIcon(fileName);
				const lastMod = file.lastModified ? new Date(file.lastModified).toLocaleDateString() : '-';

				markdown += `| ${indent}${icon} ${escapeMarkdown(fileName)} | ${file.sizeFormatted} | ${file.lfs ? 'LFS' : 'Regular'} | ${lastMod} | ${file.url} |\n`;
			}
		}

		// Add direct access examples
		markdown += `\n## Direct Access Examples\n\n`;
		markdown += `\`\`\`bash\n`;

		// Show a few example URLs
		const examples = files.slice(0, 2);
		for (const file of examples) {
			markdown += `# Download ${file.path}\n`;
			markdown += `curl -L -O ${file.url}\n\n`;
		}
		markdown += `\`\`\`\n`;
		markdown += '## Use the URL when specifying Files inputs for Gradio endpoints.\n\n';
		markdown += 'This space is accessible via `git` with `git clone https://huggingface.co/spaces/' + spaceName + '`\n';
		return markdown;
	}

	/**
	 * Generate simple markdown table without grouping
	 */
	async generateSimpleMarkdown(spaceName: string, fileType: 'all' | 'image' | 'audio' = 'all'): Promise<string> {
		const allFiles = await this.getSpaceFilesWithUrls(spaceName);
		const files = allFiles.filter((file) => matchesFileType(file, fileType));

		let markdown = `# Files in ${spaceName}\n\n`;
		if (fileType !== 'all') {
			markdown += `**Filter**: ${fileType} files only\n\n`;
		}
		markdown += `| File Name | Path | Size | URL |\n`;
		markdown += `|-----------|------|------|-----|\n`;

		for (const file of files) {
			const fileName = file.path.split('/').pop() || file.path;
			const icon = this.getFileIcon(fileName);
			markdown += `| ${icon} ${escapeMarkdown(fileName)} | ${escapeMarkdown(file.path)} | ${file.sizeFormatted} | [Link](${file.url}) |\n`;
		}

		return markdown;
	}

	/**
	 * List files with the specified format
	 */
	async listFiles(params: SpaceFilesParams): Promise<string> {
		const { fileType = 'all' } = params;

		// Use provided spaceName or default to username/filedrop
		const spaceName = params.spaceName || (this.username ? `${this.username}/filedrop` : 'filedrop');

		return this.generateDetailedMarkdown(spaceName, fileType);
	}

	/**
	 * Get file icon based on extension
	 */
	private getFileIcon(filename: string): string {
		const ext = filename.split('.').pop()?.toLowerCase();
		const iconMap: Record<string, string> = {
			py: '🐍',
			js: '📜',
			ts: '📘',
			md: '📝',
			txt: '📄',
			json: '📊',
			yaml: '⚙️',
			yml: '⚙️',
			png: '🖼️',
			jpg: '🖼️',
			jpeg: '🖼️',
			gif: '🖼️',
			svg: '🎨',
			mp4: '🎬',
			mp3: '🎵',
			pdf: '📕',
			zip: '📦',
			tar: '📦',
			gz: '📦',
			html: '🌐',
			css: '🎨',
			ipynb: '📓',
			csv: '📊',
			parquet: '🗄️',
			safetensors: '🤖',
			bin: '💾',
			pkl: '🥒',
			h5: '🗃️',
		};

		return iconMap[ext || ''] || '📄';
	}
}
