/*
* The Headers class was supported in Node.js starting with version 18, which was released on April 19, 2022.
* We need to have a polyfill ready to work for old Node versions.
* See more at https://github.com/makenotion/notion-mcp-server/issues/32
* */
class PolyfillHeaders {
  private headers: Map<string, string[]> = new Map();

  constructor(init?: Record<string, string>) {
    if (init) {
      Object.entries(init).forEach(([key, value]) => {
        this.append(key, value);
      });
    }
  }

  public append(name: string, value: string): void {
    const key = name.toLowerCase();

    if (!this.headers.has(key)) {
      this.headers.set(key, []);
    }

    this.headers.get(key)!.push(value);
  }

  public get(name: string): string | null {
    const key = name.toLowerCase();

    if (!this.headers.has(key)) {
      return null;
    }

    return this.headers.get(key)!.join(', ');
  }
}

const GlobalHeaders = typeof global !== 'undefined' && 'Headers' in global
  ? (global as any).Headers
  : undefined;

export const Headers = (GlobalHeaders || PolyfillHeaders);
