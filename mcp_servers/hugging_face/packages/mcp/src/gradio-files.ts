import { z } from 'zod';
import { listFiles } from '@huggingface/hub';
import { formatBytes, escapeMarkdown } from './utilities.js';
import { HfApiError } from './hf-api-call.js';
import { explain } from './error-messages.js';

// Define the FileWithUrl interface
interface FileWithUrl {
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

const TEXT_EXTENSIONS = new Set([
	'.txt',
	'.md',
	'json',
	'xml',
	'.csv',
	'.tsv',
	'yaml',
	'.yml',
	'.html',
	'.css',
	'.js',
	'.py',
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

function isTextFile(path: string): boolean {
	return TEXT_EXTENSIONS.has(getFileExtension(path));
}

function matchesFileType(file: FileWithUrl, fileType: 'all' | 'image' | 'audio' | 'text'): boolean {
	switch (fileType) {
		case 'all':
			return true;
		case 'image':
			return isImageFile(file.path);
		case 'audio':
			return isAudioFile(file.path);
		case 'text':
			return isTextFile(file.path);
		default:
			return true;
	}
}

// Tool configuration
export const GRADIO_FILES_TOOL_CONFIG = {
	name: 'gradio_files',
	description:
		'List available URLs that can be used for Gradio File Inputs. Use when an input is requested and an explicit URL has not been provided.', // This will be dynamically set with username
	schema: z.object({
		fileType: z.enum(['all', 'image', 'audio', 'text']).optional().default('all').describe('Filter by type'),
	}),
	annotations: {
		title: 'Gradio Files List',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: true,
	},
} as const;

export const GRADIO_FILES_PROMPT_CONFIG = {
	name: 'Available Gradio Input Files',
	description: 'Returns a list of files and their URLs to use as Gradio File Inputs.',
	schema: z.object({}),
};

// Define parameter types
export type GradioFilesParams = z.infer<typeof GRADIO_FILES_TOOL_CONFIG.schema>;

/**
 * Service for listing files in Hugging Face Spaces
 */
export class GradioFilesTool {
	private readonly accessToken: string;
	private readonly datasetname: string;

	constructor(hfToken: string, username: string) {
		this.accessToken = hfToken;
		this.datasetname = `${username}/gradio-files`;
	}

	/**
	 * Get all files in a space with their URLs
	 */
	async getGradioFiles(): Promise<FileWithUrl[]> {
		try {
			const files: FileWithUrl[] = [];

			// List all files recursively
			for await (const file of listFiles({
				repo: { type: 'dataset', name: this.datasetname },
				recursive: false, // root directory only for now,
				expand: true, // Get last commit info
				...(this.accessToken && { credentials: { accessToken: this.accessToken } }),
			})) {
				if (file.type === 'file') {
					// Exclude .gitattributes and .gitignore files
					const fileName = file.path.split('/').pop() || file.path;
					if (fileName === '.gitattributes' || fileName === '.gitignore') {
						continue;
					}

					files.push({
						path: file.path,
						size: file.size,
						type: file.type,
						url: this.constructFileUrl(file.path),
						sizeFormatted: formatBytes(file.size),
						lastModified: file.lastCommit?.date,
						lfs: !!file.lfs,
					});
				}
			}

			return files.sort((a, b) => a.path.localeCompare(b.path));
		} catch (error) {
			if (error instanceof HfApiError) {
				throw explain(error, `Failed to list files for dataset "${this.datasetname}"`);
			}
			throw error;
		}
	}

	/**
	 * Construct the URL for a file
	 */
	private constructFileUrl(filePath: string): string {
		return `https://huggingface.co/datasets/${this.datasetname}/resolve/main/${filePath}`;
	}

	/**
	 * Generate detailed markdown report with files grouped by directory
	 */
	async generateDetailedMarkdown(fileType: 'all' | 'image' | 'audio' | 'text' = 'all'): Promise<string> {
		const allFiles = await this.getGradioFiles();
		const files = allFiles.filter((file) => matchesFileType(file, fileType));

		let markdown = `# Available Gradio Input files in : ${this.datasetname}\n\n`;
		if (fileType !== 'all') {
			markdown += `**Filter**: ${fileType} files only\n`;
		}

		// Handle empty results
		if (files.length === 0) {
			if (fileType !== 'all') {
				markdown += `No ${fileType} files found in this space.\n`;
			} else {
				markdown += `No files found in this space.\n`;
			}
			return markdown;
		}

		// Generate table
		markdown += `## All Files\n\n`;
		markdown += `| Name | Size | Type | Last Modified | Gradio File Input |\n`;
		markdown += `|------|------|------|---------------|-----|\n`;

		for (const file of files) {
			const fileName = file.path.split('/').pop() || file.path;
			const icon = this.getFileIcon(fileName);
			const lastMod = file.lastModified ? new Date(file.lastModified).toLocaleDateString() : '-';

			markdown += `| ${escapeMarkdown(fileName)} | ${file.sizeFormatted} | ${icon} ${file.type} | ${lastMod} | ${file.url} |\n`;
		}

		return markdown;
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
