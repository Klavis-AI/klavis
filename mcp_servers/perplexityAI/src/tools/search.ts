import { BaseTool } from './base.js';

export class SearchTool extends BaseTool {
  async execute(args: any): Promise<{ content: Array<{ type: string; text: string }>; isError: boolean }> {
    try {
      const messages = this.validateMessagesArray(args.messages);
      const result = await this.client.performChatCompletion(messages, "sonar-pro", {
        tool: "perplexity_search",
        extra: {
          domains: args.domains,
          date_from: args.date_from,
          date_to: args.date_to,
          max_results: args.max_results
        }
      });
      return this.createSuccessResponse(result);
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
}
