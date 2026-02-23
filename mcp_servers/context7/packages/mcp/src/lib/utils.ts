import { SearchResponse, SearchResult } from "./types.js";

function getSourceReputationLabel(
  sourceReputation?: number
): "High" | "Medium" | "Low" | "Unknown" {
  if (sourceReputation === undefined || sourceReputation < 0) return "Unknown";
  if (sourceReputation >= 7) return "High";
  if (sourceReputation >= 4) return "Medium";
  return "Low";
}

export function formatSearchResult(result: SearchResult): string {
  const formattedResult = [
    `- Title: ${result.title}`,
    `- Context7-compatible library ID: ${result.id}`,
    `- Description: ${result.description}`,
  ];

  if (result.totalSnippets !== -1 && result.totalSnippets !== undefined) {
    formattedResult.push(`- Code Snippets: ${result.totalSnippets}`);
  }

  const reputationLabel = getSourceReputationLabel(result.trustScore);
  formattedResult.push(`- Source Reputation: ${reputationLabel}`);

  if (result.benchmarkScore !== undefined && result.benchmarkScore > 0) {
    formattedResult.push(`- Benchmark Score: ${result.benchmarkScore}`);
  }

  if (result.versions !== undefined && result.versions.length > 0) {
    formattedResult.push(`- Versions: ${result.versions.join(", ")}`);
  }

  return formattedResult.join("\n");
}

export function formatSearchResults(searchResponse: SearchResponse): string {
  if (!searchResponse.results || searchResponse.results.length === 0) {
    return "No documentation libraries found matching your query.";
  }

  const formattedResults = searchResponse.results.map(formatSearchResult);
  return formattedResults.join("\n----------\n");
}

export function extractClientInfoFromUserAgent(
  userAgent: string | undefined
): { ide?: string; version?: string } | undefined {
  if (!userAgent) return undefined;
  const match = userAgent.match(/^([^\/\s]+)\/([^\s(]+)/);
  if (match) {
    return { ide: match[1], version: match[2] };
  }
  return undefined;
}
