import { BaseTool } from './base.js';

export class AskTool extends BaseTool {
  async execute(args: any): Promise<{ content: Array<{ type: string; text: string }>; isError: boolean }> {
    try {
      const messages = this.validateMessagesArray(args.messages);
      const result = await this.client.performChatCompletion(messages, "sonar-pro", {
        tool: "perplexity_ask",
        max_citations: args.max_citations
      });
      return this.createSuccessResponse(result);
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
}
