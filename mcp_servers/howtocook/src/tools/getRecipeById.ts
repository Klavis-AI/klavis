import { z } from "zod";
import { Recipe } from "../types/index.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export function registerGetRecipeByIdTool(server: McpServer, recipes: Recipe[]) {
  server.tool(
    "mcp_howtocook_getRecipeById",
    "根据菜谱名称或ID查询指定菜谱的完整详情，包括食材、步骤等",
    {
      query: z.string().describe('菜谱名称或ID，支持模糊匹配菜谱名称')
    },
    async ({ query }: { query: string }) => {
      // 首先尝试精确匹配ID
      let foundRecipe = recipes.find(recipe => recipe.id === query);
      
      // 如果没有找到，尝试精确匹配名称
      if (!foundRecipe) {
        foundRecipe = recipes.find(recipe => recipe.name === query);
      }
      
      // 如果还没有找到，尝试模糊匹配名称
      if (!foundRecipe) {
        foundRecipe = recipes.find(recipe => 
          recipe.name.toLowerCase().includes(query.toLowerCase())
        );
      }
      
      // 如果仍然没有找到，返回所有可能的匹配项（最多5个）
      if (!foundRecipe) {
        const possibleMatches = recipes.filter(recipe => 
          recipe.name.toLowerCase().includes(query.toLowerCase()) ||
          recipe.description.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 5);
        
        if (possibleMatches.length === 0) {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  error: "未找到匹配的菜谱",
                  query: query,
                  suggestion: "请检查菜谱名称是否正确，或尝试使用关键词搜索"
                }, null, 2),
              },
            ],
          };
        }
        
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                message: "未找到精确匹配，以下是可能的匹配项：",
                query: query,
                possibleMatches: possibleMatches.map(recipe => ({
                  id: recipe.id,
                  name: recipe.name,
                  description: recipe.description,
                  category: recipe.category
                }))
              }, null, 2),
            },
          ],
        };
      }
      
      // 返回找到的完整菜谱信息
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(foundRecipe, null, 2),
          },
        ],
      };
    }
  );
}