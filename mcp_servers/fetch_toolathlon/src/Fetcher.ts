import { JSDOM, VirtualConsole } from "jsdom";
import TurndownService from "turndown";
import { RequestPayload } from "./types.js";

// Max response body size: 5MB to prevent OOM on huge pages
const MAX_RESPONSE_SIZE = 5 * 1024 * 1024;

export class Fetcher {
  private static async _fetch({
    url,
    headers,
  }: RequestPayload): Promise<Response> {
    try {
      const response = await fetch(url, {
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
          ...headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      return response;
    } catch (e: unknown) {
      if (e instanceof Error) {
        throw new Error(`Failed to fetch ${url}: ${e.message}`);
      } else {
        throw new Error(`Failed to fetch ${url}: Unknown error`);
      }
    }
  }

  /**
   * Read response body as text with a size limit to prevent OOM.
   */
  private static async _readText(response: Response): Promise<string> {
    const contentLength = response.headers.get("content-length");
    if (contentLength && parseInt(contentLength, 10) > MAX_RESPONSE_SIZE) {
      throw new Error(
        `Response too large (${contentLength} bytes). Max allowed: ${MAX_RESPONSE_SIZE} bytes.`
      );
    }

    const reader = response.body?.getReader();
    if (!reader) {
      return await response.text();
    }

    const chunks: Uint8Array[] = [];
    let totalSize = 0;
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      totalSize += value.byteLength;
      if (totalSize > MAX_RESPONSE_SIZE) {
        reader.cancel();
        throw new Error(
          `Response too large (>${MAX_RESPONSE_SIZE} bytes). Truncated to prevent out-of-memory.`
        );
      }
      chunks.push(value);
    }

    return chunks.map((chunk) => decoder.decode(chunk, { stream: true })).join("") +
      decoder.decode();
  }

  /**
   * Create a JSDOM instance with a virtual console that suppresses CSS parse errors.
   */
  private static _createDOM(html: string): JSDOM {
    const virtualConsole = new VirtualConsole();
    // Swallow all jsdom internal errors (CSS parse errors, etc.)
    virtualConsole.on("error", () => {});
    virtualConsole.on("warn", () => {});
    virtualConsole.on("info", () => {});
    virtualConsole.on("dir", () => {});

    // Strip <style> tags before parsing to avoid CSS parse errors and reduce memory
    const strippedHtml = html.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "");

    return new JSDOM(strippedHtml, { virtualConsole });
  }

  static async html(requestPayload: RequestPayload) {
    try {
      const response = await this._fetch(requestPayload);
      const html = await this._readText(response);
      return { content: [{ type: "text" as const, text: html }], isError: false };
    } catch (error) {
      return {
        content: [{ type: "text" as const, text: (error as Error).message }],
        isError: true,
      };
    }
  }

  static async json(requestPayload: RequestPayload) {
    try {
      const response = await this._fetch(requestPayload);
      const text = await this._readText(response);
      const json = JSON.parse(text);
      return {
        content: [{ type: "text" as const, text: JSON.stringify(json) }],
        isError: false,
      };
    } catch (error) {
      return {
        content: [{ type: "text" as const, text: (error as Error).message }],
        isError: true,
      };
    }
  }

  static async txt(requestPayload: RequestPayload) {
    try {
      const response = await this._fetch(requestPayload);
      const html = await this._readText(response);

      const dom = this._createDOM(html);
      const document = dom.window.document;

      const scripts = document.getElementsByTagName("script");
      Array.from(scripts).forEach((script) => script.remove());

      const text = document.body.textContent || "";
      const normalizedText = text.replace(/\s+/g, " ").trim();

      // Close the JSDOM window to free memory
      dom.window.close();

      return {
        content: [{ type: "text" as const, text: normalizedText }],
        isError: false,
      };
    } catch (error) {
      return {
        content: [{ type: "text" as const, text: (error as Error).message }],
        isError: true,
      };
    }
  }

  static async markdown(requestPayload: RequestPayload) {
    try {
      const response = await this._fetch(requestPayload);
      const html = await this._readText(response);

      // Strip <style> tags before conversion to avoid CSS parse errors in turndown
      const strippedHtml = html.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "");

      const turndownService = new TurndownService();
      const markdown = turndownService.turndown(strippedHtml);
      return { content: [{ type: "text" as const, text: markdown }], isError: false };
    } catch (error) {
      return {
        content: [{ type: "text" as const, text: (error as Error).message }],
        isError: true,
      };
    }
  }
}
