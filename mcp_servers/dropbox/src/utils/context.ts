import { AsyncLocalStorage } from 'async_hooks';
import { Dropbox } from 'dropbox';

// Create AsyncLocalStorage for request context
export const asyncLocalStorage = new AsyncLocalStorage<{
    dropboxClient: Dropbox;
}>();

// Helper function to get Dropbox client from context
export function getDropboxClient() {
    return asyncLocalStorage.getStore()!.dropboxClient;
}
