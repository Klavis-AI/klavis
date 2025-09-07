import { Message, PerplexityOptions } from '../types.js';
import { PerplexityClient } from '../client.js';

export abstract class BaseTool {
  protected client: PerplexityClient;

  constructor(client: PerplexityClient) {
    this.client = client;
  }

  abstract execute(args: any): Promise<{ content: Array<{ type: string; text: string }>; isError: boolean }>;

  protected createSuccessResponse(text: string) {
    return {
      content: [{ type: "text", text }],
      isError: false,
    };
  }

  protected createErrorResponse(error: string) {
    return {
      content: [{ type: "text", text: `Error: ${error}` }],
      isError: true,
    };
  }

  protected validateMessagesArray(messages: any): Message[] {
    if (!Array.isArray(messages)) {
      throw new Error("'messages' must be an array");
    }
    return messages as Message[];
  }
}
