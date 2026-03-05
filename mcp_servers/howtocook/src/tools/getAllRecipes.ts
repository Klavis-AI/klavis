import { z } from "zod";
import { Recipe } from "../types/index.js";
import { simplifyRecipeNameOnly } from "../utils/recipeUtils.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export function registerGetAllRecipesTool(server: McpServer, recipes: Recipe[]) {
  server.tool(
    "mcp_howtocook_getAllRecipes",
    "获取所有菜谱",
    {
      'no_param': z.string().optional()
                       .describe('无参数')
    },
    async () => {
      // 返回更简化版的菜谱数据，只包含name和description
      const simplifiedRecipes = recipes.map(simplifyRecipeNameOnly);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(simplifiedRecipes, null, 2),
          },
        ],
      };
    }
  );
} 