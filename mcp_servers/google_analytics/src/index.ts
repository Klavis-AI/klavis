#!/usr/bin/env node
import { BetaAnalyticsDataClient, protos } from "@google-analytics/data";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import dotenv from "dotenv"
dotenv.config()
import express, { Request, Response } from 'express';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';

type RunReportRequest = protos.google.analytics.data.v1beta.RunReportRequest;

function validateEnvironment(): void {
  const requiredEnvVars = [
    "GOOGLE_CLIENT_EMAIL",
    "GOOGLE_PRIVATE_KEY",
    "GA_PROPERTY_ID",
  ];

  const missingVars = requiredEnvVars.filter(
    (varName) => !process.env[varName],
  );

  if (missingVars.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missingVars.join(", ")}`,
    );
  }
}

//   try {
//     validateEnvironment();

//     console.error('✅ Environment variables loaded.');
//     console.error('🚀 Starting Google Analytics MCP server...');
//   } catch (err) {
//     console.error('❌ Server crashed:', err);
//     process.exit(1);
//   }
// });

// Validate date format (YYYY-MM-DD)
function validateDateFormat(date: string): boolean {
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRegex.test(date)) {
    return false;
  }

  const parsedDate = new Date(date);
  return parsedDate.toISOString().split("T")[0] === date;
}

// Validate date range
function validateDateRange(startDate: string, endDate: string): void {
  if (!validateDateFormat(startDate)) {
    throw new McpError(
      ErrorCode.InvalidParams,
      `Invalid startDate format. Expected YYYY-MM-DD, got: ${startDate}`,
    );
  }

  if (!validateDateFormat(endDate)) {
    throw new McpError(
      ErrorCode.InvalidParams,
      `Invalid endDate format. Expected YYYY-MM-DD, got: ${endDate}`,
    );
  }

  if (new Date(startDate) > new Date(endDate)) {
    throw new McpError(
      ErrorCode.InvalidParams,
      "startDate cannot be after endDate",
    );
  }
}

// Initialize environment validation
validateEnvironment();

// Initialize the Google Analytics Data client
const analyticsDataClient = new BetaAnalyticsDataClient({
  credentials: {
    client_email: process.env.GOOGLE_CLIENT_EMAIL as string,
    private_key: process.env.GOOGLE_PRIVATE_KEY as string,
  },
});

const propertyId = process.env.GA_PROPERTY_ID as string;

// Create the server
const server = new Server(
  {
    name: "google-analytics-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  },
);

// Validate and fetch analytics data
async function fetchAnalyticsData(
  reportConfig: Partial<Omit<RunReportRequest, "property">> & {
    dateRanges: RunReportRequest["dateRanges"];
    dimensions?: RunReportRequest["dimensions"];
    metrics?: RunReportRequest["metrics"];
  },
) {
  try {
    const [response] = await analyticsDataClient.runReport({
      property: `properties/${propertyId}`,
      ...reportConfig,
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(response, null, 2),
        },
      ],
    };
  } catch (error) {
    // Handle Google Analytics API errors
    if (error instanceof Error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Google Analytics API error: ${error.message}`,
      );
    }
    throw new McpError(ErrorCode.InternalError, "An unexpected error occurred");
  }
}

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "runReport",
        description: "Run a report to get analytics data",
        inputSchema: {
          type: "object",
          properties: {
            startDate: {
              type: "string",
              description: "Start date in YYYY-MM-DD format",
            },
            endDate: {
              type: "string",
              description: "End date in YYYY-MM-DD format",
            },
            dimensions: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  name: { type: "string" },
                },
                required: ["name"],
              },
              description: "Dimensions to group by (e.g., page, country)",
            },
            metrics: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  name: { type: "string" },
                },
                required: ["name"],
              },
              description: "Metrics to include in the report",
            },
            dimensionFilter: {
              type: "object",
              description: "Filter for dimensions",
            },
          },
          required: ["startDate", "endDate", "metrics", "dimensions"],
        },
      },
      {
        name: "getPageViews",
        description: "Get page view metrics for a specific date range",
        inputSchema: {
          type: "object",
          properties: {
            startDate: {
              type: "string",
              description: "Start date in YYYY-MM-DD format",
            },
            endDate: {
              type: "string",
              description: "End date in YYYY-MM-DD format",
            },
            dimensions: {
              type: "array",
              items: { type: "string" },
              description: "Dimensions to group by (e.g., page, country)",
            },
          },
          required: ["startDate", "endDate"],
        },
      },
      {
        name: "getActiveUsers",
        description: "Get active users metrics for a specific date range",
        inputSchema: {
          type: "object",
          properties: {
            startDate: {
              type: "string",
              description: "Start date in YYYY-MM-DD format",
            },
            endDate: {
              type: "string",
              description: "End date in YYYY-MM-DD format",
            },
          },
          required: ["startDate", "endDate"],
        },
      },
      {
        name: "getEvents",
        description: "Get event metrics for a specific date range",
        inputSchema: {
          type: "object",
          properties: {
            startDate: {
              type: "string",
              description: "Start date in YYYY-MM-DD format",
            },
            endDate: {
              type: "string",
              description: "End date in YYYY-MM-DD format",
            },
            eventName: {
              type: "string",
              description: "Specific event name to filter by (optional)",
            },
          },
          required: ["startDate", "endDate"],
        },
      },
      {
        name: "getUserBehavior",
        description:
          "Get user behavior metrics like session duration and bounce rate",
        inputSchema: {
          type: "object",
          properties: {
            startDate: {
              type: "string",
              description: "Start date in YYYY-MM-DD format",
            },
            endDate: {
              type: "string",
              description: "End date in YYYY-MM-DD format",
            },
          },
          required: ["startDate", "endDate"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "runReport": {
        const {
          startDate,
          endDate,
          dimensions = [],
          metrics = [],
          dimensionFilter,
        } = args as {
          startDate: string;
          endDate: string;
          dimensions?: { name: string }[];
          metrics?: { name: string }[];
          dimensionFilter?: object;
        };

        validateDateRange(startDate, endDate);

        return fetchAnalyticsData({
          dateRanges: [{ startDate, endDate }],
          dimensions,
          metrics,
          ...(dimensionFilter && { dimensionFilter }),
        });
      }
      case "getPageViews": {
        const {
          startDate,
          endDate,
          dimensions = ["page"],
        } = args as {
          startDate: string;
          endDate: string;
          dimensions?: string[];
        };

        validateDateRange(startDate, endDate);

        return fetchAnalyticsData({
          dateRanges: [{ startDate, endDate }],
          dimensions: dimensions.map((dimension) => ({ name: dimension })),
          metrics: [{ name: "screenPageViews" }],
        });
      }

      case "getActiveUsers": {
        const { startDate, endDate } = args as {
          startDate: string;
          endDate: string;
        };

        validateDateRange(startDate, endDate);

        return fetchAnalyticsData({
          dateRanges: [{ startDate, endDate }],
          metrics: [{ name: "activeUsers" }, { name: "newUsers" }],
          dimensions: [{ name: "date" }],
        });
      }

      case "getEvents": {
        const { startDate, endDate, eventName } = args as {
          startDate: string;
          endDate: string;
          eventName?: string;
        };

        validateDateRange(startDate, endDate);

        return fetchAnalyticsData({
          dateRanges: [{ startDate, endDate }],
          dimensions: [{ name: "eventName" }, { name: "date" }],
          metrics: [{ name: "eventCount" }],
          ...(eventName && {
            dimensionFilter: {
              filter: {
                fieldName: "eventName",
                stringFilter: { value: eventName },
              },
            },
          }),
        });
      }

      case "getUserBehavior": {
        const { startDate, endDate } = args as {
          startDate: string;
          endDate: string;
        };

        validateDateRange(startDate, endDate);

        return fetchAnalyticsData({
          dateRanges: [{ startDate, endDate }],
          metrics: [
            { name: "averageSessionDuration" },
            { name: "bounceRate" },
            { name: "sessionsPerUser" },
          ],
          dimensions: [{ name: "date" }],
        });
      }

      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
  } catch (error) {
    if (error instanceof McpError) {
      throw error;
    }

    throw new McpError(ErrorCode.InternalError, "An unexpected error occurred");
  }
});

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

const app = express();
app.use(express.json());

app.post('/mcp', async (req: Request, res: Response) => {
  // No access token required for service account, but you could add auth here if needed
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
    res.on('close', () => {
      console.log('Request closed');
      transport.close();
      server.close();
    });
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: Response) => {
  console.log('Received GET MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

  const PORT = process.env.PORT || 5000;
  app.listen(PORT, () => {
    console.log(`Google Analytics MCP server running on port ${PORT}`);
  });

