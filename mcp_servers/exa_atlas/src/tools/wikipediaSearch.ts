import { z } from "zod";
import axios from "axios";
import { toolRegistry, API_CONFIG, getApiKey } from "./config.js";
import { ExaSearchRequest, ExaSearchResponse } from "../types.js";
import { createRequestLogger } from "../utils/logger.js";

// Register the Wikipedia search tool
toolRegistry["wikipedia_search_exa"] = {
  name: "wikipedia_search_exa",
  description: "Search Wikipedia using Exa AI - performs searches specifically within Wikipedia.org and returns relevant content from Wikipedia pages.",
  schema: {
    query: z.string().describe("Search query for Wikipedia"),
    numResults: z.number().optional().describe("Number of search results to return (default: 5)")
  },
  handler: async ({ query, numResults }, extra) => {
    const requestId = `wikipedia_search_exa-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const logger = createRequestLogger(requestId, 'wikipedia_search_exa');
    
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

      const searchRequest: ExaSearchRequest = {
        query,
        type: "auto",
        includeDomains: ["wikipedia.org"],
        numResults: numResults || API_CONFIG.DEFAULT_NUM_RESULTS,
        contents: {
          text: {
            maxCharacters: API_CONFIG.DEFAULT_MAX_CHARACTERS
          },
          livecrawl: 'always'
        }
      };
      
      logger.log("Sending request to Exa API for Wikipedia search");
      
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
            text: "No Wikipedia search results found. Please try a different query."
          }]
        };
      }

      logger.log(`Found ${response.data.results.length} Wikipedia results`);
      
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
            text: `Wikipedia search error (${statusCode}): ${errorMessage}`
          }],
          isError: true,
        };
      }
      
      // Handle generic errors
      return {
        content: [{
          type: "text" as const,
          text: `Wikipedia search error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true,
      };
    } 
  },
  enabled: false
}; 