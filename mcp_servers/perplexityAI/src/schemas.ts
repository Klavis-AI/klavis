// @ts-ignore
import { Tool } from "@modelcontextprotocol/sdk/types.js";

export const PERPLEXITY_ASK_TOOL: Tool = {
  name: "perplexity_ask",
  description:
    "General conversational Q&A using Sonar Pro. Returns helpful, citation-aware conversational responses.",
  inputSchema: {
    type: "object",
    properties: {
      messages: {
        type: "array",
        items: {
          type: "object",
          properties: {
            role: { type: "string", description: "Role of the message (e.g., system, user, assistant)" },
            content: { type: "string", description: "The content of the message" },
          },
          required: ["role", "content"],
        },
        description: "Array of conversation messages",
      },
      max_citations: { type: "number", description: "Optional maximum number of citations to return" },
    },
    required: ["messages"],
  },
};

export const PERPLEXITY_RESEARCH_TOOL: Tool = {
  name: "perplexity_research",
  description:
    "In-depth research using Sonar Deep Research. Returns synthesized reports with detailed citations and optional export formats.",
  inputSchema: {
    type: "object",
    properties: {
      messages: PERPLEXITY_ASK_TOOL.inputSchema.properties!.messages,
      depth: { type: "number", description: "Research depth (1-5) - higher yields more thorough answers" },
      format: { type: "string", description: "Output format: 'summary' | 'full' | 'report'" },
    },
    required: ["messages"],
  },
};

export const PERPLEXITY_SEARCH_TOOL: Tool = {
  name: "perplexity_search",
  description:
    "Fast factual search using Sonar (search-optimized). Supports domain filters and date ranges for concise results.",
  inputSchema: {
    type: "object",
    properties: {
      messages: PERPLEXITY_ASK_TOOL.inputSchema.properties!.messages,
      domains: { type: "array", items: { type: "string" }, description: "Optional preferred domains to search (e.g., ['wikipedia.org'])" },
      date_from: { type: "string", description: "Optional start date for search results (YYYY-MM-DD)" },
      date_to: { type: "string", description: "Optional end date for search results (YYYY-MM-DD)" },
      max_results: { type: "number", description: "Optional max number of search results to consider" },
    },
    required: ["messages"],
  },
};

export const PERPLEXITY_REASON_TOOL: Tool = {
  name: "perplexity_reason",
  description:
    "Multi-step reasoning using Sonar Reasoning Pro. Returns chain-of-thought style explanations and final answers; configurable verbosity.",
  inputSchema: {
    type: "object",
    properties: {
      messages: PERPLEXITY_ASK_TOOL.inputSchema.properties!.messages,
      verbose: { type: "boolean", description: "If true, include step-by-step reasoning in the response" },
    },
    required: ["messages"],
  },
};

export const PERPLEXITY_SUMMARY_TOOL: Tool = {
  name: "perplexity_summary",
  description:
    "Summarizes one or more documents or blocks of text concisely with citations if relevant.",
  inputSchema: {
    type: "object",
    properties: {
      documents: {
        type: "array",
        items: { type: "string" },
        description: "Array of text documents to summarize.",
      },
    },
    required: ["documents"],
  },
};

export const PERPLEXITY_CODE_ASSISTANT_TOOL: Tool = {
  name: "perplexity_code_assistant",
  description:
    "Provides coding help, explanations, debugging, and code improvements in a given programming language.",
  inputSchema: {
    type: "object",
    properties: {
      code: {
        type: "string",
        description: "The code snippet for the assistant to analyze or improve.",
      },
      question: {
        type: "string",
        description: "Optional question or request about the code.",
      },
      language: {
        type: "string",
        description: "Programming language of the code (optional).",
      },
    },
    required: ["code"],
  },
};

export const ALL_TOOLS = [
  PERPLEXITY_ASK_TOOL,
  PERPLEXITY_SEARCH_TOOL,
  PERPLEXITY_RESEARCH_TOOL,
  PERPLEXITY_REASON_TOOL,
  PERPLEXITY_SUMMARY_TOOL,
  PERPLEXITY_CODE_ASSISTANT_TOOL,
];
