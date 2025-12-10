/**
 * Provides search functionality for documentation using Trieve.
 * Exports functions to fetch search configuration and register the search tool.
 */

import axios, { AxiosResponse } from "axios";
import { TrieveSDK } from "trieve-ts-sdk";
import { z } from "zod";
import { SUBDOMAIN, SERVER_URL } from "./config.readonly.js";
import { formatErr, throwOnAxiosError } from "./utils.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { InitializationConfiguration } from "./types.js";

const DEFAULT_BASE_URL = "https://api.mintlifytrieve.com";

/**
 * Fetches search configuration and OpenAPI data for a given subdomain.
 * @param subdomain - Subdomain to fetch config for.
 * @returns The initialization configuration.
 */
export async function fetchSearchConfigurationAndOpenApi(
  subdomain: string
): Promise<InitializationConfiguration> {
  try {
    const response: AxiosResponse<InitializationConfiguration> =
      await axios.get(`${SERVER_URL}/api/mcp/config/${subdomain}`, {
        validateStatus: () => true,
      });

    throwOnAxiosError(response, "Failed to fetch MCP config");
    return response.data;
  } catch (err) {
    const friendlyError = formatErr(err).replace(
      "Request failed with status code 404",
      `${subdomain} not found`
    );
    throw new Error(friendlyError);
  }
}

interface TrieveChunk {
  chunk: {
    metadata: {
      title: string;
    };
    chunk_html: string;
    link: string;
  };
}

interface SearchResult {
  title: string;
  content: string;
  link: string;
}

/**
 * Queries Trieve and returns formatted search results.
 * @param query - The search string.
 * @param config - Trieve configuration values.
 * @returns Array of search results.
 */
async function search(
  query: string,
  config: InitializationConfiguration
): Promise<SearchResult[]> {
  const trieve = new TrieveSDK({
    apiKey: config.trieveApiKey,
    datasetId: config.trieveDatasetId,
    baseUrl: DEFAULT_BASE_URL,
  });

  const data = await trieve.autocomplete({
    page_size: 10,
    query,
    search_type: "fulltext",
    extend_results: true,
    score_threshold: 1,
  });

  if (!data?.chunks?.length) {
    throw new Error("No results found");
  }

  return data.chunks.map(({ chunk }: TrieveChunk) => ({
    title: chunk.metadata.title,
    content: chunk.chunk_html,
    link: chunk.link,
  }));
}

/**
 * Registers the "search" tool to the MCP server for querying documentation.
 * @param server - The MCP server instance.
 */
export async function createSearchTool(server: McpServer): Promise<void> {
  const config = await fetchSearchConfigurationAndOpenApi(SUBDOMAIN);

  server.tool(
    "search",
    `Search across the ${config.name} documentation to fetch relevant context for a given query.`,
    { query: z.string() },
    async ({ query }: { query: string }) => {
      const results = await search(query, config);

      const content = results.map(({ title, content, link }) => ({
        type: "text" as const,
        text: `Title: ${title}\nContent: ${content}\nLink: ${link}`,
      }));

      return { content };
    }
  );
}
