import { Recipe, SimpleRecipe, NameOnlyRecipe, Ingredient } from '../types/index.js';

// 创建简化版的Recipe数据
export function simplifyRecipe(recipe: Recipe): SimpleRecipe {
  return {
    id: recipe.id,
    name: recipe.name,
    description: recipe.description,
    ingredients: recipe.ingredients.map((ingredient: Ingredient) => ({
      name: ingredient.name,
      text_quantity: ingredient.text_quantity
    }))
  };
}

// 创建只包含name和description的Recipe数据
export function simplifyRecipeNameOnly(recipe: Recipe): NameOnlyRecipe {
  return {
    name: recipe.name,
    description: recipe.description
  };
}

// 处理食材清单，收集菜谱的所有食材
export function processRecipeIngredients(recipe: Recipe, ingredientMap: Map<string, {
  totalQuantity: number | null,
  unit: string | null,
  recipeCount: number,
  recipes: string[]
}>) {
  recipe.ingredients?.forEach((ingredient: Ingredient) => {
    const key = ingredient.name.toLowerCase();
    
    if (!ingredientMap.has(key)) {
      ingredientMap.set(key, {
        totalQuantity: ingredient.quantity,
        unit: ingredient.unit,
        recipeCount: 1,
        recipes: [recipe.name]
      });
    } else {
      const existing = ingredientMap.get(key)!;
      
      // 对于有明确数量和单位的食材，进行汇总
      if (existing.unit && ingredient.unit && existing.unit === ingredient.unit && existing.totalQuantity !== null && ingredient.quantity !== null) {
        existing.totalQuantity += ingredient.quantity;
      } else {
        // 否则保留 null，表示数量不确定
        existing.totalQuantity = null;
        existing.unit = null;
      }
      
      existing.recipeCount += 1;
      if (!existing.recipes.includes(recipe.name)) {
        existing.recipes.push(recipe.name);
      }
    }
  });
}

// 根据食材类型进行分类
export function categorizeIngredients(ingredients: Array<{
  name: string,
  totalQuantity: number | null,
  unit: string | null,
  recipeCount: number,
  recipes: string[]
}>, shoppingPlan: {
  fresh: string[],
  pantry: string[],
  spices: string[],
  others: string[]
}) {
  const spiceKeywords = ['盐', '糖', '酱油', '醋', '料酒', '香料', '胡椒', '孜然', '辣椒', '花椒', '姜', '蒜', '葱', '调味'];
  const freshKeywords = ['肉', '鱼', '虾', '蛋', '奶', '菜', '菠菜', '白菜', '青菜', '豆腐', '生菜', '水产', '豆芽', '西红柿', '番茄', '水果', '香菇', '木耳', '蘑菇'];
  const pantryKeywords = ['米', '面', '粉', '油', '酒', '醋', '糖', '盐', '酱', '豆', '干', '罐头', '方便面', '面条', '米饭', '意大利面', '燕麦'];

  ingredients.forEach(ingredient => {
    const name = ingredient.name.toLowerCase();
    
    if (spiceKeywords.some(keyword => name.includes(keyword))) {
      shoppingPlan.spices.push(ingredient.name);
    } else if (freshKeywords.some(keyword => name.includes(keyword))) {
      shoppingPlan.fresh.push(ingredient.name);
    } else if (pantryKeywords.some(keyword => name.includes(keyword))) {
      shoppingPlan.pantry.push(ingredient.name);
    } else {
      shoppingPlan.others.push(ingredient.name);
    }
  });
} 