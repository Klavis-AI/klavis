import { BaseTool } from './base.js';

export class CodeAssistantTool extends BaseTool {
  async execute(args: any): Promise<{ content: Array<{ type: string; text: string }>; isError: boolean }> {
    try {
      if (typeof args.code !== "string") {
        throw new Error("'code' must be a string");
      }

      const systemPrompt = {
        role: "system",
        content: "You are an expert programming assistant. Help debug, improve, or explain the given code. Provide relevant examples if needed.",
      };
      
      const conversation: Array<{ role: string; content: string }> = [systemPrompt];

      conversation.push({
        role: "user",
        content: `Code snippet:\n${args.code}`,
      });

      if (args.question) {
        conversation.push({ role: "user", content: `Question: ${args.question}` });
      }

      if (args.language) {
        conversation.push({ role: "user", content: `Programming language: ${args.language}` });
      }

      const result = await this.client.performChatCompletion(
        conversation,
        "sonar-pro",
        { tool: "perplexity_code_assistant", verbose: true }
      );
      
  return this.createSuccessResponse(result);
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
}
