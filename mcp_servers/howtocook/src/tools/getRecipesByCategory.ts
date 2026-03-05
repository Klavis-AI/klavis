import { z } from "zod";
import { Recipe } from "../types/index.js";
import { simplifyRecipe } from "../utils/recipeUtils.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export function registerGetRecipesByCategoryTool(server: McpServer, recipes: Recipe[], categories: string[]) {
  server.tool(
    "mcp_howtocook_getRecipesByCategory",
    `根据分类查询菜谱，可选分类有: ${categories.join(', ')}`,
    {
      category: z.enum(categories as [string, ...string[]])
                .describe('菜谱分类名称，如水产、早餐、荤菜、主食等')
    },
    async ({ category }: { category: string }) => {
      const filteredRecipes = recipes.filter((recipe) => recipe.category === category);
      // 返回简化版的菜谱数据
      const simplifiedRecipes = filteredRecipes.map(simplifyRecipe);
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