import { BaseTool } from './base.js';

export class ReasonTool extends BaseTool {
  async execute(args: any): Promise<{ content: Array<{ type: string; text: string }>; isError: boolean }> {
    try {
      const messages = this.validateMessagesArray(args.messages);
      const result = await this.client.performChatCompletion(messages, "sonar-reasoning-pro", {
        tool: "perplexity_reason",
        verbose: args.verbose
      });
      return this.createSuccessResponse(result);
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
}
