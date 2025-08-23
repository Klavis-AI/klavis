# Perplexity MCP Server

A Model Context Protocol (MCP) server for Perplexity AI, implemented in TypeScript.

## Features

- Exposes Perplexity tools via MCP: Ask, Research, Reason
- Endpoints:
  - `/sse` - Server-Sent Events endpoint for real-time communication
  - `/messages/` - SSE message handling endpoint
  - `/mcp` - StreamableHTTP endpoint for direct API calls

## Setup

### Prerequisites
- Node.js 18+ and npm
- Perplexity API key

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```
2. Copy `.env.example` to `.env` and set your `PERPLEXITY_API_KEY`.
3. Build and run:
   ```bash
   npm run build
   npm start
   ```

### Docker

1. Build the Docker image:
   ```bash
   docker build -t perplexity-mcp-server .
   ```
2. Run the container:
   ```bash
   docker run -e PERPLEXITY_API_KEY=your_key -p 5000:5000 perplexity-mcp-server
   ```

## API Endpoints

- `/sse` - Server-Sent Events endpoint for real-time communication
- `/messages/` - SSE message handling endpoint
- `/mcp` - StreamableHTTP endpoint for direct API calls

## Tool Usage Examples

### Ask
```json
{
  "name": "perplexity_ask",
  "arguments": {
    "messages": [
      { "role": "user", "content": "What is the capital of France?" }
    ]
  }
}
```

### Research
```json
{
  "name": "perplexity_research",
  "arguments": {
    "messages": [
      { "role": "user", "content": "Explain quantum computing." }
    ]
  }
}
```

### Reason
```json
{
  "name": "perplexity_reason",
  "arguments": {
    "messages": [
      { "role": "user", "content": "Why is the sky blue?" }
    ]
  }
}
```

## Perplexity tools (overview)

This MCP server exposes six Perplexity tools. Below are short descriptions, typical inputs, primary uses, and how they differ from each other.

- perplexity_ask
  - Description: General-purpose conversational Q&A. Produces concise, direct answers to single-turn or multi-turn user questions.
  - Inputs: `messages` array (chat-style user/system messages).
  - Best for: Straightforward factual questions, follow-ups, and conversational interactions where a short answer is desired.

- perplexity_search
  - Description: Query-focused web/search tool that prioritizes retrieving factual information and citations from web sources.
  - Inputs: `messages` array; typically a search-style prompt.
  - Best for: Looking up facts, news, or references; when source citations and retrieval fidelity matter.

- perplexity_research
  - Description: Deeper investigative mode that gathers supporting evidence, multiple sources, and structured context for complex topics.
  - Inputs: `messages` array; can be multi-part research prompts.
  - Best for: Long-form explanations, literature reviews, comparative analysis, and situations that need multiple corroborating sources.

- perplexity_reason
  - Description: Reasoning-focused tool that emphasizes chain-of-thought and causal explanations rather than surface-level answers.
  - Inputs: `messages` array where prompts request explanations or stepwise reasoning.
  - Best for: Causal questions, problem solving, explanations that benefit from stepwise logic.

- perplexity_summary
  - Description: Condenses long text or aggregated results into concise summaries with optional citation handling.
  - Inputs: Text or `messages` containing content to summarize; options may control citation limits.
  - Best for: Summarizing articles, long threads, or research findings into digestible bullets or short paragraphs.

- perplexity_code_assistant
  - Description: Developer-oriented tool tuned for coding tasks: generating, explaining, or fixing code with contextual awareness.
  - Inputs: `messages` array including code snippets or coding instructions; can run with `verbose` option for more detail.
  - Best for: Code generation, refactors, debugging help, and code explanations.

### How they differ (quick comparison)

- Focus: `ask` = general answers, `search` = retrieval/citations, `research` = multi-source investigation, `reason` = logical explanations, `summary` = condensation, `code_assistant` = code-centric.
- Response style: `ask` and `summary` favor concise outputs; `research` and `reason` favor detailed, structured outputs; `search` includes source citations; `code_assistant` returns code + explanations.
- Latency & cost: `research` and `search` often incur higher latency (external retrieval) and may request more tokens/calls; `ask`, `summary`, and `reason` are typically faster for short prompts. `code_assistant` may be verbose depending on the task.
- Best input shape: All tools accept the MCP `messages` array; prefer search/research prompts to be phrased as queries, and code_assistant prompts to include language/context and sample code where relevant.
- Citations & evidence: `search` and `research` prioritize citing sources; `summary` can include citations if supplied; `ask`, `reason`, and `code_assistant` may provide fewer explicit citations unless asked.

Use the tool whose intent matches your goal: retrieval+citation -> `perplexity_search`/`perplexity_research`; explanation/logic -> `perplexity_reason`; concise Q&A -> `perplexity_ask`; summarization -> `perplexity_summary`; coding -> `perplexity_code_assistant`.


@Priyanshuthapliyal2005