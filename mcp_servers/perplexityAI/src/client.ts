import { Message, PerplexityOptions } from './types.js';
import { AsyncLocalStorage } from "async_hooks";

// Create AsyncLocalStorage for request context
export const asyncLocalStorage = new AsyncLocalStorage<{
  perplexity_token: string;
}>();

export function getPerplexityToken() {
  // First check if env var exists
  if (process.env.PERPLEXITY_API_KEY) {
    return process.env.PERPLEXITY_API_KEY;
  }
  // Fall back to token from request context
  const store = asyncLocalStorage.getStore();
  return store?.perplexity_token;
}

export class PerplexityClient {
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  // Update token if needed
  refreshToken() {
    const token = getPerplexityToken();
    if (token) {
      this.apiKey = token;
      return true;
    }
    return false;
  }

  async performChatCompletion(
    messages: Message[],
    model: string = "sonar-pro",
    options: PerplexityOptions = {}
  ): Promise<string> {
    this.refreshToken();

    // Compose system prompt based on tool to better differentiate behavior
    // Ensure proper message alternation for Perplexity API
    const promptMessages = [...messages];

    // Insert a single leading system message depending on the tool
    let systemMessage = { role: "system", content: "You are a helpful assistant." };
    if (options.tool === "perplexity_search") {
      systemMessage = { role: "system", content: "You are a lightweight factual search assistant focusing on quick, concise results with citations." };
    } else if (options.tool === "perplexity_research") {
      systemMessage = { role: "system", content: "You are a deep research assistant. Perform multi-step evidence-based analysis and provide detailed citations and a clear summary." };
    } else if (options.tool === "perplexity_reason") {
      systemMessage = { role: "system", content: "You are a reasoning expert AI designed for multi-step problem solving and clear logical explanations. Include chain-of-thought if verbose=true." };
    }

    // Normalize messages to follow Perplexity alternation rules:
    // 1. Start with system message (optional)
    // 2. Then alternate user/assistant messages
    // 3. Merge consecutive user messages into one
    const normalized: Message[] = [systemMessage];
    
    // Process all non-system messages, merging consecutive user messages
    const nonSystemMessages = promptMessages.filter(msg => msg.role !== "system");
    let currentUserContent: string[] = [];
    
    for (const msg of nonSystemMessages) {
      if (msg.role === "user" || msg.role === "tool") {
        // Treat tool messages as user messages for alternation purposes
        currentUserContent.push(msg.content);
      } else if (msg.role === "assistant") {
        // If we have accumulated user content, add it first
        if (currentUserContent.length > 0) {
          normalized.push({ 
            role: "user", 
            content: currentUserContent.join("\n\n") 
          });
          currentUserContent = [];
        }
        // Add assistant message
        normalized.push(msg);
      }
    }
    
    // Add any remaining user content
    if (currentUserContent.length > 0) {
      normalized.push({ 
        role: "user", 
        content: currentUserContent.join("\n\n") 
      });
    }

    // Use normalized messages as the payload
    const finalMessages = normalized;

    const url = new URL("https://api.perplexity.ai/chat/completions");
    const body: Record<string, any> = {
      model,
      messages: finalMessages,
    };

    if (options.max_citations) body.max_citations = options.max_citations;
    if (options.extra) body.extra = options.extra;

    let response;
    try {
      response = await fetch(url.toString(), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(body),
      });
    } catch (error) {
      throw new Error(`Network error while calling Perplexity API: ${error}`);
    }
    if (!response.ok) {
      let errorText;
      try {
        errorText = await response.text();
      } catch {
        errorText = "Unable to parse error response";
      }
      throw new Error(
        `Perplexity API error: ${response.status} ${response.statusText}\n${errorText}`
      );
    }
    let data;
    try {
      data = await response.json();
    } catch (jsonError) {
      throw new Error(`Failed to parse JSON response from Perplexity API: ${jsonError}`);
    }

    // Safely extract choices content
    const messageContent = data?.choices?.[0]?.message?.content ?? JSON.stringify(data);

    // Post-process citations according to options
    let output = messageContent;
    if (data.citations && Array.isArray(data.citations) && data.citations.length > 0) {
      const max = options.max_citations ?? data.citations.length;
      output += "\n\nCitations:\n";
      data.citations.slice(0, max).forEach((citation: string, index: number) => {
        output += `[${index + 1}] ${citation}\n`;
      });
    }
    return output;
  }
}
