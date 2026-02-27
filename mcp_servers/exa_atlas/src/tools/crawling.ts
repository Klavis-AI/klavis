import { z } from "zod";
import axios from "axios";
import { toolRegistry, API_CONFIG, getApiKey } from "./config.js";
import { ExaCrawlRequest } from "../types.js";
import { createRequestLogger } from "../utils/logger.js";

// Register the crawling tool
toolRegistry["crawling"] = {
  name: "crawling",
  description: "Extract content from specific URLs using Exa AI - performs targeted crawling of web pages to retrieve their full content. Useful for reading articles, PDFs, or any web page when you have the exact URL. Returns the complete text content of the specified URL.",
  schema: {
    url: z.string().describe("The URL to crawl (e.g., 'exa.ai')")
  },
  handler: async ({ url }, extra) => {
    const requestId = `crawling-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const logger = createRequestLogger(requestId, 'crawling');
    
    logger.start(url);
    
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

      const crawlRequest: ExaCrawlRequest = {
        ids: [url],
        text: true,
        livecrawl: 'always'
      };
      
      logger.log(`Crawling URL: ${url}`);
      logger.log("Sending crawling request to Exa API");
      
      const response = await axiosInstance.post(
        '/contents',
        crawlRequest,
        { timeout: 25000 }
      );
      
      logger.log("Received crawling response from Exa API");

      if (!response.data || !response.data.results || response.data.results.length === 0) {
        logger.log("Warning: Empty or invalid response from Exa API for crawling");
        return {
          content: [{
            type: "text" as const,
            text: "No content found at the specified URL. Please check the URL and try again."
          }]
        };
      }

      logger.log(`Successfully crawled content from URL`);
      
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
            text: `Crawling error (${statusCode}): ${errorMessage}`
          }],
          isError: true,
        };
      }
      
      // Handle generic errors
      return {
        content: [{
          type: "text" as const,
          text: `Crawling error: ${error instanceof Error ? error.message : String(error)}`
        }],
        isError: true,
      };
    }
  },
  enabled: false  // Disabled by default
}; 