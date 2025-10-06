import { BaseTool } from './base.js';

export class SummaryTool extends BaseTool {
  async execute(args: any): Promise<{ content: Array<{ type: string; text: string }>; isError: boolean }> {
    try {
      if (!Array.isArray(args.documents)) {
        throw new Error("'documents' must be an array of strings");
      }

      const systemPrompt = {
        role: "system",
        content: "You are an expert summarizer. Summarize the following documents clearly and concisely. Include citations where relevant.",
      };
      
      const conversation: Array<{ role: string; content: string }> = [systemPrompt];
      
      args.documents.forEach((doc: string, index: number) => {
        conversation.push({
          role: "user",
          content: `Document ${index + 1}:\n${doc}`,
        });
      });

      const result = await this.client.performChatCompletion(
        conversation,
        "sonar-deep-research",
        { tool: "perplexity_summary", max_citations: undefined }
      );
      
  return this.createSuccessResponse(result);
    } catch (error) {
      return this.createErrorResponse(error instanceof Error ? error.message : String(error));
    }
  }
}
