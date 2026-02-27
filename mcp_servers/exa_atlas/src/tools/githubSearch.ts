import { z } from "zod";
import axios from "axios";
import { toolRegistry, API_CONFIG, getApiKey } from "./config.js";
import { ExaSearchRequest, ExaSearchResponse } from "../types.js";
import { createRequestLogger } from "../utils/logger.js";

// Register the GitHub search tool
toolRegistry["github_search"] = {
  name: "github_search",
  description: "Search GitHub repositories using Exa AI - performs real-time searches on GitHub.com to find relevant repositories and GitHub accounts.",
  schema: {
    query: z.string().describe("Search query for GitHub repositories, or Github account, or code"),
    numResults: z.number().optional().describe("Number of search results to return (default: 5)")
  },
  handler: async ({ query, numResults }, extra) => {
    const requestId = `github_search-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const logger = createRequestLogger(requestId, 'github_search');
    
    logger.start(query);
    
    try {
      // Create a fresh axios instance for each request
      const axiosInstance = axios.create({
        baseURL: API_CONFIG.BASE_URL,
        headers: {
          'accept': 'application/json',
          'content-type': 'application/json',
          'x-api-key': getApiKey()
        },
        timeout: 25000
      });

      // Prefix the query with "exa.ai GitHub:" to focus on GitHub results
      const githubQuery = query.toLowerCase().includes('github') ? query : `exa.ai GitHub: ${query}`;
      
      const searchRequest: ExaSearchRequest = {
        query: githubQuery,
        type: "auto",
        includeDomains: ["github.com"],
        numResults: numResults || API_CONFIG.DEFAULT_NUM_RESULTS,
        contents: {
          text: true,
          livecrawl: 'always'
        }
      };
      
      logger.log("Sending request to Exa API for GitHub search");
      
      const response = await axiosInstance.post<ExaSearchResponse>(
        API_CONFIG.ENDPOINTS.SEARCH,
        searchRequest,
        { timeout: 25000 }
      );
      
      logger.log("Received response from Exa API");

      if (!response.data || !response.data.results) {
        logger.log("Warning: Empty or invalid response from Exa API");
        return {
          content: [{
            type: "text" as const,
            text: "No GitHub results found. Please try a different query."
          }]
        };
      }

      logger.log(`Found ${response.data.results.length} GitHub results`);
      
      const result = {
        content: [{
          type: "text" as const,
          text: JSON.stringify(response.data, null, 2)
        }]
      };
      
      logger.complete();
      return result;
    } catch (error) {
      logger.error(error);
      
      if (axios.isAxiosError(error)) {
        // Handle Axios errors specifically
        const statusCode = error.response?.status || 'unknown';
        const errorMessage = error.response?.data?.message || error.message;
        
        logger.log(`Axios error (${statusCode}): ${errorMessage}`);
        return {
          content: [{
            type: "text" as const,
            text: `GitHub search error (${statusCode}): ${errorMessage}`
          }],
          isError: true,
        };
      }
      
      // Handle generic errors
      return {
        content: [{
          type: "text" as const,
          text: `GitHub search error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true,
      };
    }
  },
  enabled: false
}; 