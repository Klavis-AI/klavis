// Polyfill for fetch Response.buffer() method - fixes compatibility with modern Node.js/Bun
// This addresses the same issue fixed in https://github.com/dropbox/dropbox-sdk-js/pull/1138
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
