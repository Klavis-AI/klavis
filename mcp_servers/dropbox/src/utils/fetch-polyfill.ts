// Polyfill for fetch Response.buffer() method - fixes compatibility with modern Node.js/Bun
// 
// This addresses a compatibility issue where the Dropbox SDK expects the fetch Response object
// to have a buffer() method, which was available in older versions of node-fetch but not in
// the native fetch implementation in modern Node.js (18+) or Bun.
//
// The Dropbox SDK uses response.buffer() for file downloads, but native fetch only provides
// response.arrayBuffer(). This polyfill adds the missing buffer() method by converting
// arrayBuffer() results to Node.js Buffer objects.
//
// Related issues:
// - https://github.com/dropbox/dropbox-sdk-js/issues/1135
// - https://github.com/dropbox/dropbox-sdk-js/pull/1138 (similar fix)
//
// Without this patch, file download operations (like download_file tool) would fail with:
// "TypeError: response.buffer is not a function"
export function patchFetchResponse() {
    const originalFetch = global.fetch;
    if (originalFetch) {
        global.fetch = async function (...args: Parameters<typeof fetch>) {
            const response = await originalFetch.apply(this, args);

            // Add buffer() method if it doesn't exist (for compatibility with Dropbox SDK)
            if (!('buffer' in response) && typeof response.arrayBuffer === 'function') {
                (response as any).buffer = function () {
                    return this.arrayBuffer().then((data: ArrayBuffer) => Buffer.from(data));
                };
            }

            return response;
        };
    }
}
