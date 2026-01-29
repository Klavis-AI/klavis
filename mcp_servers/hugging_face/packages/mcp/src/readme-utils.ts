/**
 * Utility functions for fetching and processing README files from Hugging Face repositories
 */

// Maximum number of characters to include from a README
const DEFAULT_MAX_README_CHARS = 10_000;

/**
 * Fetches README content from a Hugging Face repository
 * 
 * @param repoName The resolved repository name (e.g., 'rajpurkar/squad', 'openai-community/gpt2')
 * @param type The repository type ('models' or 'datasets')
 * @param includeYaml Whether to include YAML frontmatter (default: false)
 * @returns Promise<string | null> The README content or null if not found/error
 */
export async function fetchReadmeContent(
	repoName: string,
	type: 'models' | 'datasets',
	includeYaml: boolean = false
): Promise<string | null> {
	try {
		// Construct the URL based on repository type
		const baseUrl = type === 'datasets' 
			? `https://huggingface.co/datasets/${repoName}`
			: `https://huggingface.co/${repoName}`;
		
		const url = `${baseUrl}/resolve/main/README.md`;

		const response = await fetch(url);
		
		if (!response.ok) {
			if (response.status === 404) {
				// README doesn't exist, return null silently
				return null;
			}
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		let content = await response.text();

		// If includeYaml is false, strip YAML frontmatter
		if (!includeYaml) {
			content = stripYamlFrontmatter(content);
		}

		// Truncate overly long READMEs to a sensible default size
		if (content.length > DEFAULT_MAX_README_CHARS) {
			const truncated = content.slice(0, DEFAULT_MAX_README_CHARS);
			content = `${truncated}\n\n[... truncated to ~${DEFAULT_MAX_README_CHARS.toString()} characters — full README: ${baseUrl}]`;
		}

		// Return null if content is empty after processing
		if (!content.trim()) {
			return null;
		}

		return content;
	} catch (error) {
		// Log error for debugging but don't throw - README is optional
		console.error(`Failed to fetch README for ${repoName}:`, error);
		return null;
	}
}

/**
 * Strips YAML frontmatter from markdown content
 * 
 * @param content The full markdown content
 * @returns The content with YAML frontmatter removed
 */
function stripYamlFrontmatter(content: string): string {
	// Match YAML frontmatter: starts with ---, ends with ---
	const yamlPattern = /^(\s*---[\r\n]+)([\S\s]*?)([\r\n]+---(\r\n|\n|$))/;
	const match = content.match(yamlPattern);
	
	if (match) {
		// Return everything after the closing ---
		return content.substring(match[0].length);
	}
	
	// No YAML frontmatter found, return original content
	return content;
}
