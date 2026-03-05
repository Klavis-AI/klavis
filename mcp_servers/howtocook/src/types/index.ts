// 定义菜谱的类型接口
export interface Ingredient {
  name: string;
  quantity: number | null;
  unit: string | null;
  text_quantity: string;
  notes: string;
}

export interface Step {
  step: number;
  description: string;
}

export interface Recipe {
  id: string;
  name: string;
  description: string;
  source_path: string;
  image_path: string | null;
  category: string;
  difficulty: number;
  tags: string[];
  servings: number;
  ingredients: Ingredient[];
  steps: Step[];
  prep_time_minutes: number | null;
  cook_time_minutes: number | null;
  total_time_minutes: number | null;
  additional_notes: string[];
}

// 添加简化版的Recipe接口，只包含id、name和description
export interface SimpleRecipe {
  id: string;
  name: string;
  description: string;
  ingredients: {
    name: string;
    text_quantity: string;
  }[];
}

// 更简化的Recipe接口，只包含name和description，用于getAllRecipes
export interface NameOnlyRecipe {
  name: string;
  description: string;
}

// 定义膳食计划相关接口
export interface MealPlan {
  weekdays: Array<DayPlan>;
  weekend: Array<DayPlan>;
  groceryList: GroceryList;
}

export interface DayPlan {
  day: string;
  breakfast: SimpleRecipe[];
  lunch: SimpleRecipe[];
  dinner: SimpleRecipe[];
}

export interface GroceryList {
  ingredients: Array<{
    name: string;
    totalQuantity: number | null;
    unit: string | null;
    recipeCount: number;
    recipes: string[];
  }>;
  shoppingPlan: {
    fresh: string[];
    pantry: string[];
    spices: string[];
    others: string[];
  };
}

// 定义推荐菜品的接口
export interface DishRecommendation {
  peopleCount: number;
  meatDishCount: number;
  vegetableDishCount: number;
  dishes: SimpleRecipe[];
  message: string;
} 