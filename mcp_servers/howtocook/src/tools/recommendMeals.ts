import { z } from "zod";
import { Recipe, MealPlan, SimpleRecipe, DayPlan } from "../types/index.js";
import { simplifyRecipe, processRecipeIngredients, categorizeIngredients } from "../utils/recipeUtils.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export function registerRecommendMealsTool(server: McpServer, recipes: Recipe[]) {
  server.tool(
    "mcp_howtocook_recommendMeals",
    "根据用户的忌口、过敏原、人数智能推荐菜谱，创建一周的膳食计划以及大致的购物清单",
    {
      allergies: z.array(z.string()).optional()
                 .describe('过敏原列表，如["大蒜", "虾"]'),
      avoidItems: z.array(z.string()).optional()
                  .describe('忌口食材列表，如["葱", "姜"]'),
      peopleCount: z.number().int().min(1).max(10)
                   .describe('用餐人数，1-10之间的整数')
    },
    async ({ allergies = [], avoidItems = [], peopleCount }: { 
      allergies?: string[], 
      avoidItems?: string[], 
      peopleCount: number 
    }) => {
      // 过滤掉含有忌口和过敏原的菜谱
      const filteredRecipes = recipes.filter((recipe) => {
        // 检查是否包含过敏原或忌口食材
        const hasAllergiesOrAvoidItems = recipe.ingredients?.some((ingredient) => {
          const name = ingredient.name?.toLowerCase() || '';
          return allergies.some(allergy => name.includes(allergy.toLowerCase())) || 
                 avoidItems.some(item => name.includes(item.toLowerCase()));
        });
        
        return !hasAllergiesOrAvoidItems;
      });

      // 将菜谱按分类分组
      const recipesByCategory: Record<string, Recipe[]> = {};
      const targetCategories = ['水产', '早餐', '荤菜', '主食'];
      
      filteredRecipes.forEach((recipe) => {
        if (targetCategories.includes(recipe.category)) {
          if (!recipesByCategory[recipe.category]) {
            recipesByCategory[recipe.category] = [];
          }
          recipesByCategory[recipe.category].push(recipe);
        }
      });

      // 创建每周膳食计划
      const mealPlan: MealPlan = {
        weekdays: [],
        weekend: [],
        groceryList: {
          ingredients: [],
          shoppingPlan: {
            fresh: [],
            pantry: [],
            spices: [],
            others: []
          }
        }
      };

      // 用于跟踪已经选择的菜谱，以便后续处理食材信息
      const selectedRecipes: Recipe[] = [];

      // 周一至周五
      for (let i = 0; i < 5; i++) {
        const dayPlan: DayPlan = {
          day: ['周一', '周二', '周三', '周四', '周五'][i],
          breakfast: [],
          lunch: [],
          dinner: []
        };

        // 早餐 - 根据人数推荐1-2个早餐菜单
        const breakfastCount = Math.max(1, Math.ceil(peopleCount / 5));
        for (let j = 0; j < breakfastCount && recipesByCategory['早餐'] && recipesByCategory['早餐'].length > 0; j++) {
          const breakfastIndex = Math.floor(Math.random() * recipesByCategory['早餐'].length);
          const selectedRecipe = recipesByCategory['早餐'][breakfastIndex];
          selectedRecipes.push(selectedRecipe);
          dayPlan.breakfast.push(simplifyRecipe(selectedRecipe));
          // 避免重复，从候选列表中移除
          recipesByCategory['早餐'] = recipesByCategory['早餐'].filter((_, idx) => idx !== breakfastIndex);
        }

        // 午餐和晚餐的菜谱数量，根据人数确定
        const mealCount = Math.max(2, Math.ceil(peopleCount / 3));
        
        // 午餐
        for (let j = 0; j < mealCount; j++) {
          // 随机选择菜系：主食、水产、蔬菜、荤菜等
          const categories = ['主食', '水产', '荤菜', '素菜', '甜品'];
          let selectedCategory = categories[Math.floor(Math.random() * categories.length)];
          
          // 如果该分类没有菜谱或已用完，尝试其他分类
          while (!recipesByCategory[selectedCategory] || recipesByCategory[selectedCategory].length === 0) {
            selectedCategory = categories[Math.floor(Math.random() * categories.length)];
            if (categories.every(cat => !recipesByCategory[cat] || recipesByCategory[cat].length === 0)) {
              break; // 所有分类都没有可用菜谱，退出循环
            }
          }
          
          if (recipesByCategory[selectedCategory] && recipesByCategory[selectedCategory].length > 0) {
            const index = Math.floor(Math.random() * recipesByCategory[selectedCategory].length);
            const selectedRecipe = recipesByCategory[selectedCategory][index];
            selectedRecipes.push(selectedRecipe);
            dayPlan.lunch.push(simplifyRecipe(selectedRecipe));
            // 避免重复，从候选列表中移除
            recipesByCategory[selectedCategory] = recipesByCategory[selectedCategory].filter((_, idx) => idx !== index);
          }
        }
        
        // 晚餐
        for (let j = 0; j < mealCount; j++) {
          // 随机选择菜系，与午餐类似但可添加汤羹
          const categories = ['主食', '水产', '荤菜', '素菜', '甜品', '汤羹'];
          let selectedCategory = categories[Math.floor(Math.random() * categories.length)];
          
          // 如果该分类没有菜谱或已用完，尝试其他分类
          while (!recipesByCategory[selectedCategory] || recipesByCategory[selectedCategory].length === 0) {
            selectedCategory = categories[Math.floor(Math.random() * categories.length)];
            if (categories.every(cat => !recipesByCategory[cat] || recipesByCategory[cat].length === 0)) {
              break; // 所有分类都没有可用菜谱，退出循环
            }
          }
          
          if (recipesByCategory[selectedCategory] && recipesByCategory[selectedCategory].length > 0) {
            const index = Math.floor(Math.random() * recipesByCategory[selectedCategory].length);
            const selectedRecipe = recipesByCategory[selectedCategory][index];
            selectedRecipes.push(selectedRecipe);
            dayPlan.dinner.push(simplifyRecipe(selectedRecipe));
            // 避免重复，从候选列表中移除
            recipesByCategory[selectedCategory] = recipesByCategory[selectedCategory].filter((_, idx) => idx !== index);
          }
        }

        mealPlan.weekdays.push(dayPlan);
      }

      // 周六和周日
      for (let i = 0; i < 2; i++) {
        const dayPlan: DayPlan = {
          day: ['周六', '周日'][i],
          breakfast: [],
          lunch: [],
          dinner: []
        };

        // 早餐 - 根据人数推荐菜品，至少2个菜品，随人数增加
        const breakfastCount = Math.max(2, Math.ceil(peopleCount / 3));
        for (let j = 0; j < breakfastCount && recipesByCategory['早餐'] && recipesByCategory['早餐'].length > 0; j++) {
          const breakfastIndex = Math.floor(Math.random() * recipesByCategory['早餐'].length);
          const selectedRecipe = recipesByCategory['早餐'][breakfastIndex];
          selectedRecipes.push(selectedRecipe);
          dayPlan.breakfast.push(simplifyRecipe(selectedRecipe));
          recipesByCategory['早餐'] = recipesByCategory['早餐'].filter((_, idx) => idx !== breakfastIndex);
        }

        // 计算工作日的基础菜品数量
        const weekdayMealCount = Math.max(2, Math.ceil(peopleCount / 3));
        // 周末菜品数量：比工作日多1-2个菜，随人数增加
        const weekendAddition = peopleCount <= 4 ? 1 : 2; // 4人以下多1个菜，4人以上多2个菜
        const mealCount = weekdayMealCount + weekendAddition;

        const getMeals = (count: number): SimpleRecipe[] => {
          const result: SimpleRecipe[] = [];
          const categories = ['荤菜', '水产'];
          
          // 尽量平均分配不同分类的菜品
          for (let j = 0; j < count; j++) {
            const category = categories[j % categories.length];
            if (recipesByCategory[category] && recipesByCategory[category].length > 0) {
              const index = Math.floor(Math.random() * recipesByCategory[category].length);
              const selectedRecipe = recipesByCategory[category][index];
              selectedRecipes.push(selectedRecipe);
              result.push(simplifyRecipe(selectedRecipe));
              recipesByCategory[category] = recipesByCategory[category].filter((_, idx) => idx !== index);
            } else if (recipesByCategory['主食'] && recipesByCategory['主食'].length > 0) {
              // 如果没有足够的荤菜或水产，使用主食
              const index = Math.floor(Math.random() * recipesByCategory['主食'].length);
              const selectedRecipe = recipesByCategory['主食'][index];
              selectedRecipes.push(selectedRecipe);
              result.push(simplifyRecipe(selectedRecipe));
              recipesByCategory['主食'] = recipesByCategory['主食'].filter((_, idx) => idx !== index);
            }
          }
          
          return result;
        };

        dayPlan.lunch = getMeals(mealCount);
        dayPlan.dinner = getMeals(mealCount);

        mealPlan.weekend.push(dayPlan);
      }

      // 统计食材清单，收集所有菜谱的所有食材
      const ingredientMap = new Map<string, {
        totalQuantity: number | null,
        unit: string | null,
        recipeCount: number,
        recipes: string[]
      }>();

      // 处理所有菜谱
      selectedRecipes.forEach(recipe => processRecipeIngredients(recipe, ingredientMap));
      
      // 整理食材清单
      for (const [name, info] of ingredientMap.entries()) {
        mealPlan.groceryList.ingredients.push({
          name,
          totalQuantity: info.totalQuantity,
          unit: info.unit,
          recipeCount: info.recipeCount,
          recipes: info.recipes
        });
      }

      // 对食材按使用频率排序
      mealPlan.groceryList.ingredients.sort((a, b) => b.recipeCount - a.recipeCount);

      // 生成购物计划，根据食材类型进行分类
      categorizeIngredients(mealPlan.groceryList.ingredients, mealPlan.groceryList.shoppingPlan);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(mealPlan, null, 2),
          },
        ],
      };
    }
  );
} 