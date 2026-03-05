import { Recipe } from '../types/index.js'
import localRecipes from './all_recipes.json' with { type: 'json' };

// 远程菜谱JSON文件URL
const RECIPES_URL = 'https://weilei.site/all_recipes.json'

/**
 * 从远程获取菜谱，如果失败则使用本地备份
 */
export async function fetchRecipes(): Promise<Recipe[]> {
    try {
        const response = await fetch(RECIPES_URL)
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`)
        }
        const data = await response.json()
        return data as Recipe[]
    } catch (error) {
        console.error('获取远程菜谱数据失败，将使用本地备份数据')
        // localRecipes 已经是 JSON 转好的对象
        return localRecipes as Recipe[]
    }
}

/**
 * 获取所有分类
 */
export function getAllCategories(recipes: Recipe[]): string[] {
    const categories = new Set<string>()
    recipes.forEach((recipe) => {
        if (recipe.category) {
            categories.add(recipe.category)
        }
    })
    return Array.from(categories)
}
