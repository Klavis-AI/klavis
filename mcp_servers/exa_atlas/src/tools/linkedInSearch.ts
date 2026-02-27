import { z } from "zod";
import axios from "axios";
import { toolRegistry, API_CONFIG, getApiKey } from "./config.js";
import { ExaSearchRequest, ExaSearchResponse } from "../types.js";
import { createRequestLogger } from "../utils/logger.js";

// Register the LinkedIn search tool
toolRegistry["linkedin_search"] = {
  name: "linkedin_search",
  description: "Search LinkedIn for companies using Exa AI. Simply include company URL, or company name, with 'company page' appended in your query.",
  schema: {
    query: z.string().describe("Search query for LinkedIn (e.g., <url> company page OR <company name> company page)"),
    numResults: z.number().optional().describe("Number of search results to return (default: 5)")
  },
  handler: async ({ query, numResults }, extra) => {
    const requestId = `linkedin_search-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const logger = createRequestLogger(requestId, 'linkedin_search');
    
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

      // Create search request
      const searchRequest: ExaSearchRequest = {
        query,
        type: "auto",
        includeDomains: ["linkedin.com"],
        numResults: numResults || API_CONFIG.DEFAULT_NUM_RESULTS,
        contents: {
          text: {
            maxCharacters: API_CONFIG.DEFAULT_MAX_CHARACTERS
          },
          livecrawl: 'always'
        }
      };
      
      logger.log("Sending request to Exa API");
      
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
            text: "No LinkedIn results found. Please try a different query."
          }]
        };
      }

      logger.log(`Found ${response.data.results.length} LinkedIn results`);
      
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
            text: `LinkedIn search error (${statusCode}): ${errorMessage}`
          }],
          isError: true,
        };
      }
      
      // Handle generic errors
      return {
        content: [{
          type: "text" as const,
          text: `LinkedIn search error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true,
      };
    }
  },
  enabled: false
}; 