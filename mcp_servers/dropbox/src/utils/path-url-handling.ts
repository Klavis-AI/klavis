/**
 * Utilities for handling Dropbox paths and URLs
 */

/**
 * Checks if a path represents a folder (ends with /)
 * @param path - The path to check
 * @returns True if the path represents a folder, false otherwise
 */
export function isFolderPath(path: string): boolean {
    return path.endsWith('/');
}

/**
 * Converts a dropbox:// resource URI to a file path
 * @param uri - The dropbox:// URI to convert
 * @returns The file path
 * @throws Error if the URI is invalid
 */
export function dropboxResourceUriToPath(uri: string): string {
    if (!uri.startsWith('dropbox://')) {
        throw new Error('Invalid dropbox resource URI. Must start with dropbox://');
    }

    let path = uri.replace('dropbox://', '').trimEnd();

    // Ensure the path starts with /
    if (!path.startsWith('/')) {
        path = `/${path}`;
    }

    return path;
}

/**
 * Converts a file path to a dropbox:// resource URI
 * @param path - The file path to convert
 * @returns The dropbox:// resource URI
 */
export function pathToDropboxResourceUri(path: string): string {
    // Ensure the path starts with /
    if (!path.startsWith('/')) {
        path = `/${path}`;
    }

    return `dropbox://${path.startsWith('/') ? path.slice(1) : path}`;
}

/**
 * Extracts the filename from a file path
 * @param path - The file path to extract filename from
 * @returns The filename
 * @throws Error if the path represents a folder
 */
export function getFilenameFromPath(path: string): string {
    if (isFolderPath(path)) {
        throw new Error('Cannot extract filename from folder path. Path represents a folder.');
    }

    const parts = path.split('/');
    const filename = parts[parts.length - 1];

    return filename;
}
