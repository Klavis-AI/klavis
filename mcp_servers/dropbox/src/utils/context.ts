import { AsyncLocalStorage } from 'async_hooks';
import { Dropbox } from 'dropbox';

// Create AsyncLocalStorage for request context
export const asyncLocalStorage = new AsyncLocalStorage<{
    dropboxClient: Dropbox | null;
}>();

// Helper function to get Dropbox client from context
export function getDropboxClient() {
    const client = asyncLocalStorage.getStore()?.dropboxClient;
    if (!client) {
        throw new Error('Access token is missing. Provide it via x-auth-token header or set DROPBOX_ACCESS_TOKEN in the environment.');
    }
    return client;
}
