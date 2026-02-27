import { z } from "zod";
import axios from "axios";
import { toolRegistry, API_CONFIG, getApiKey } from "./config.js";
import { ExaSearchRequest, ExaSearchResponse } from "../types.js";
import { createRequestLogger } from "../utils/logger.js";

// Register the competitor finder tool
toolRegistry["competitor_finder"] = {
  name: "competitor_finder",
  description: "Find competitors of a company using Exa AI - performs targeted searches to identify businesses that offer similar products or services. Describe what the company does (without mentioning its name) and optionally provide the company's website to exclude it from results.",
  schema: {
    query: z.string().describe("Describe what the company/product in a few words (e.g., 'web search API', 'AI image generation', 'cloud storage service'). Keep it simple. Do not include the company name."),
    excludeDomain: z.string().optional().describe("Optional: The company's website to exclude from results (e.g., 'exa.ai')"),
    numResults: z.number().optional().describe("Number of competitors to return (default: 10)")
  },
  handler: async ({ query, excludeDomain, numResults }, extra) => {
    const requestId = `competitor_finder-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const logger = createRequestLogger(requestId, 'competitor_finder');
    
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
        numResults: numResults || 10,
        contents: {
          text: {
            maxCharacters: API_CONFIG.DEFAULT_MAX_CHARACTERS
          },
          livecrawl: 'always'
        }
      };
      
      // Add exclude domain if provided
      if (excludeDomain) {
        searchRequest.excludeDomains = [excludeDomain];
        logger.log(`Excluding domain: ${excludeDomain}`);
      }
      
      logger.log(`Finding competitors for: ${query}`);
      logger.log("Sending competitor finder request to Exa API");
      
      const response = await axiosInstance.post<ExaSearchResponse>(
        API_CONFIG.ENDPOINTS.SEARCH,
        searchRequest,
        { timeout: 25000 }
      );
      
      logger.log("Received competitor finder response from Exa API");

      if (!response.data || !response.data.results) {
        logger.log("Warning: Empty or invalid response from Exa API for competitor finder");
        return {
          content: [{
            type: "text" as const,
            text: "No competitors found. Please try a different query."
          }]
        };
      }

      logger.log(`Found ${response.data.results.length} potential competitors`);
      
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
            text: `Competitor finder error (${statusCode}): ${errorMessage}`
          }],
          isError: true,
        };
      }
      
      // Handle generic errors
      return {
        content: [{
          type: "text" as const,
          text: `Competitor finder error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true,
      };
    }
  },
  enabled: false  // Disabled by default
}; 