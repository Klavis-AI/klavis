import { BaseTool } from './base.js';

export class ResearchTool extends BaseTool {
  async execute(args: any): Promise<{ content: Array<{ type: string; text: string }>; isError: boolean }> {
    try {
      const messages = this.validateMessagesArray(args.messages);
      const result = await this.client.performChatCompletion(messages, "sonar-deep-research", {
        tool: "perplexity_research",
        extra: {
          depth: args.depth,
          format: args.format
        }
      });
      return this.createSuccessResponse(result);
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
}
