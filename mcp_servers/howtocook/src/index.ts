#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { Command } from 'commander';
import { createServer } from 'http';
import { fetchRecipes, getAllCategories } from "./data/recipes.js";
import { registerGetAllRecipesTool } from "./tools/getAllRecipes.js";
import { registerGetRecipeByIdTool } from "./tools/getRecipeById.js";
import { registerGetRecipesByCategoryTool } from "./tools/getRecipesByCategory.js";
import { registerRecommendMealsTool } from "./tools/recommendMeals.js";
import { registerWhatToEatTool } from "./tools/whatToEat.js";
import { Recipe } from './types/index.js';

// 全局变量存储数据
let recipes: Recipe[] = [];
let categories: string[] = [];

// 命令行参数处理
const program = new Command()
  .option("--transport <stdio|http|sse>", "transport type", "stdio")
  .option("--port <number>", "port for HTTP/SSE transport", "3000")
  .parse(process.argv);

const cliOptions = program.opts<{
  transport: string;
  port: string;
}>();

const allowedTransports = ["stdio", "http", "sse"];
if (!allowedTransports.includes(cliOptions.transport)) {
  console.error(
    `Invalid --transport value: '${cliOptions.transport}'. Must be one of: stdio, http, sse.`
  );
  process.exit(1);
}

const TRANSPORT_TYPE = (cliOptions.transport || "stdio") as "stdio" | "http" | "sse";
const PORT = parseInt(cliOptions.port, 10);
//  SSE transports 
const sseTransports: Record<string, SSEServerTransport> = {};
// 创建MCP服务器实例
function createServerInstance(): McpServer {
  const server = new McpServer({
    name: 'howtocook-mcp',
    version: '0.1.1',
  }, {
    capabilities: {
      logging: {},
    },
  });

  // 注册所有工具
  registerGetAllRecipesTool(server, recipes);
  registerGetRecipesByCategoryTool(server, recipes, categories);
  registerRecommendMealsTool(server, recipes);
  registerWhatToEatTool(server, recipes);
  registerGetRecipeByIdTool(server, recipes);

  return server;
}

// 加载菜谱数据
async function loadRecipeData() {
  try {
    recipes = await fetchRecipes();
    categories = getAllCategories(recipes);
    console.log(`📚 已加载 ${recipes.length} 个菜谱`);
  } catch (error) {
    console.error('加载菜谱数据失败:', error);
    recipes = [];
    categories = [];
    throw error;
  }
}

// 启动服务的主函数
async function main() {
  // 加载菜谱数据
  await loadRecipeData();

  if (TRANSPORT_TYPE === "http" || TRANSPORT_TYPE === "sse") {
    const httpServer = createServer(async (req, res) => {
      const url = new URL(req.url || "", `http://${req.headers.host}`).pathname;

      // 设置 CORS 头
      res.setHeader("Access-Control-Allow-Origin", "*");
      res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS,DELETE");
      res.setHeader("Access-Control-Allow-Headers", "Content-Type, MCP-Session-Id, mcp-session-id");

      // 处理预检请求
      if (req.method === "OPTIONS") {
        res.writeHead(200);
        res.end();
        return;
      }

      try {
        // 为每个请求创建新的服务器实例
        const requestServer = createServerInstance();

        if (url === "/mcp") {
          const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
          });
          await requestServer.connect(transport);
          await transport.handleRequest(req, res);
        }else if (url === "/sse" && req.method === "GET") {
          // Create new SSE transport for GET request
          const sseTransport = new SSEServerTransport("/messages", res);
          // Store the transport by session ID
          sseTransports[sseTransport.sessionId] = sseTransport;
          // Clean up transport when connection closes
          res.on("close", () => {
            delete sseTransports[sseTransport.sessionId];
          });
          await requestServer.connect(sseTransport);
        } else if (url === "/messages" && req.method === "POST") {
          // Get session ID from query parameters
          const sessionId =
            new URL(req.url || "", `http://${req.headers.host}`).searchParams.get("sessionId") ??
            "";

          if (!sessionId) {
            res.writeHead(400);
            res.end("Missing sessionId parameter");
            return;
          }

          // Get existing transport for this session
          const sseTransport = sseTransports[sessionId];
          if (!sseTransport) {
            res.writeHead(400);
            res.end(`No transport found for sessionId: ${sessionId}`);
            return;
          }

          // Handle the POST message with the existing transport
          await sseTransport.handlePostMessage(req, res);
        }  
        else if (url === "/health") {
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ status: "ok", transport: TRANSPORT_TYPE }));
        } else if (url === "/info") {
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({
            name: "HowToCook MCP Server",
            version: "0.1.1",
            transport: TRANSPORT_TYPE,
            endpoints: {
              mcp: "/mcp",
              sse: "/sse",
              health: "/health",
              info: "/info"
            },
            recipeCount: recipes.length
          }));
        } else {
          res.writeHead(404);
          res.end("Not found");
        }
      } catch (error) {
        console.error("处理请求时出错:", error);
        if (!res.headersSent) {
          res.writeHead(500);
          res.end("Internal Server Error");
        }
      }
    });

    httpServer.listen(PORT, () => {
      console.log(`🚀 HowToCook MCP ${TRANSPORT_TYPE.toUpperCase()} 服务器启动成功`);
      if(TRANSPORT_TYPE === "http"){
        console.log(`🔗 MCP 端点: http://localhost:${PORT}/mcp`);
      }else if(TRANSPORT_TYPE === "sse"){
        console.log(`🔗 MCP 端点: http://localhost:${PORT}/sse`);
      }
      console.log(`💡 健康检查: http://localhost:${PORT}/health`);
      console.log(`ℹ️  服务器信息: http://localhost:${PORT}/info`);
    });
  } else {
    // stdio 模式
    const server = createServerInstance();
    const transport = new StdioServerTransport();
    try {
      await server.connect(transport);
      console.log('HowToCook MCP STDIO 服务器启动成功');
    } catch (error) {
      console.error('服务器启动失败:', error);
      process.exit(1);
    }
  }
}

// 优雅关闭
process.on('SIGINT', async () => {
  console.log('\n正在关闭服务器...');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n收到终止信号，正在关闭服务器...');
  process.exit(0);
});

// 启动服务器
main().catch((error) => {
  console.error('启动服务器失败:', error);
  process.exit(1);
});

