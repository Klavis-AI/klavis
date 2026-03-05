import { z } from "zod";
import { Recipe, DishRecommendation } from "../types/index.js";
import { simplifyRecipe } from "../utils/recipeUtils.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export function registerWhatToEatTool(server: McpServer, recipes: Recipe[]) {
  server.tool(
    "mcp_howtocook_whatToEat",
    "不知道吃什么？根据人数直接推荐适合的菜品组合",
    {
      peopleCount: z.number().int().min(1).max(10)
                   .describe('用餐人数，1-10之间的整数，会根据人数推荐合适数量的菜品')
    },
    async ({ peopleCount }: { peopleCount: number }) => {
      // 根据人数计算荤素菜数量
      const vegetableCount = Math.floor((peopleCount + 1) / 2);
      const meatCount = Math.ceil((peopleCount + 1) / 2);
      
      // 获取所有荤菜
      let meatDishes = recipes.filter((recipe) => 
        recipe.category === '荤菜' || recipe.category === '水产'
      );
      
      // 获取其他可能的菜品（当做素菜）
      let vegetableDishes = recipes.filter((recipe) => 
        recipe.category !== '荤菜' && recipe.category !== '水产' && 
        recipe.category !== '早餐' && recipe.category !== '主食'
      );
      
      // 特别处理：如果人数超过8人，增加鱼类荤菜
      let recommendedDishes: Recipe[] = [];
      let fishDish: Recipe | null = null;
      
      if (peopleCount > 8) {
        const fishDishes = recipes.filter((recipe) => recipe.category === '水产');
        if (fishDishes.length > 0) {
          fishDish = fishDishes[Math.floor(Math.random() * fishDishes.length)];
          recommendedDishes.push(fishDish);
        }
      }
      
      // 打乱肉类优先级顺序，增加随机性
      const meatTypes = ['猪肉', '鸡肉', '牛肉', '羊肉', '鸭肉', '鱼肉'];
      // 使用 Fisher-Yates 洗牌算法打乱数组
      for (let i = meatTypes.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [meatTypes[i], meatTypes[j]] = [meatTypes[j], meatTypes[i]];
      }
      
      const selectedMeatDishes: Recipe[] = [];
      
      // 需要选择的荤菜数量
      const remainingMeatCount = fishDish ? meatCount - 1 : meatCount;
      
      // 尝试按照随机化的肉类优先级选择荤菜
      for (const meatType of meatTypes) {
        if (selectedMeatDishes.length >= remainingMeatCount) break;
        
        const meatTypeOptions = meatDishes.filter((dish) => {
          // 检查菜品的材料是否包含这种肉类
          return dish.ingredients?.some((ingredient) => {
            const name = ingredient.name?.toLowerCase() || '';
            return name.includes(meatType.toLowerCase());
          });
        });
        
        if (meatTypeOptions.length > 0) {
          // 随机选择一道这种肉类的菜
          const selected = meatTypeOptions[Math.floor(Math.random() * meatTypeOptions.length)];
          selectedMeatDishes.push(selected);
          // 从可选列表中移除，避免重复选择
          meatDishes = meatDishes.filter((dish) => dish.id !== selected.id);
        }
      }
      
      // 如果通过肉类筛选的荤菜不够，随机选择剩余的
      while (selectedMeatDishes.length < remainingMeatCount && meatDishes.length > 0) {
        const randomIndex = Math.floor(Math.random() * meatDishes.length);
        selectedMeatDishes.push(meatDishes[randomIndex]);
        meatDishes.splice(randomIndex, 1);
      }
      
      // 随机选择素菜
      const selectedVegetableDishes: Recipe[] = [];
      while (selectedVegetableDishes.length < vegetableCount && vegetableDishes.length > 0) {
        const randomIndex = Math.floor(Math.random() * vegetableDishes.length);
        selectedVegetableDishes.push(vegetableDishes[randomIndex]);
        vegetableDishes.splice(randomIndex, 1);
      }
      
      // 合并推荐菜单
      recommendedDishes = recommendedDishes.concat(selectedMeatDishes, selectedVegetableDishes);
      
      // 构建推荐结果
      const recommendationDetails: DishRecommendation = {
        peopleCount,
        meatDishCount: selectedMeatDishes.length + (fishDish ? 1 : 0),
        vegetableDishCount: selectedVegetableDishes.length,
        dishes: recommendedDishes.map(simplifyRecipe),
        message: `为${peopleCount}人推荐的菜品，包含${selectedMeatDishes.length + (fishDish ? 1 : 0)}个荤菜和${selectedVegetableDishes.length}个素菜。`
      };
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(recommendationDetails, null, 2),
          },
        ],
      };
    }
  );
}