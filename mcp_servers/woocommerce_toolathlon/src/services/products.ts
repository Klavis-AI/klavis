import { BaseService } from './base.js';
import {
    ProductParams,
    CreateProductParams,
    UpdateProductParams,
    DeleteProductParams,
    VariationParams,
    BatchUpdateParams
} from '../types.js';

export class ProductService extends BaseService {
    async listProducts(params: ProductParams) {
        return this.handleRequest(
            this.client.get('/products', { params: this.toSnakeCase(params) })
        );
    }

    async getProduct(params: ProductParams) {
        if (!params.productId) {
            throw new Error('Product ID is required');
        }
        return this.handleRequest(
            this.client.get(`/products/${params.productId}`)
        );
    }

    async createProduct(params: CreateProductParams) {
        if (!params.productData) {
            throw new Error('Product data is required');
        }
        return this.handleRequest(
            this.client.post('/products', params.productData)
        );
    }

    async updateProduct(params: UpdateProductParams) {
        if (!params.productId) {
            throw new Error('Product ID is required');
        }
        if (!params.productData) {
            throw new Error('Product data is required');
        }
        return this.handleRequest(
            this.client.put(`/products/${params.productId}`, params.productData)
        );
    }

    async deleteProduct(params: DeleteProductParams) {
        if (!params.productId) {
            throw new Error('Product ID is required');
        }
        return this.handleRequest(
            this.client.delete(`/products/${params.productId}`, {
                params: { force: params.force || false }
            })
        );
    }

    async batchUpdateProducts(params: BatchUpdateParams) {
        return this.handleRequest(
            this.client.post('/products/batch', params)
        );
    }

    // Product variations
    async listVariations(params: VariationParams) {
        if (!params.productId) {
            throw new Error('Product ID is required');
        }
        return this.handleRequest(
            this.client.get(`/products/${params.productId}/variations`, {
                params: {
                    per_page: params.perPage,
                    page: params.page
                }
            })
        );
    }

    async getVariation(params: VariationParams) {
        if (!params.productId || !params.variationId) {
            throw new Error('Product ID and Variation ID are required');
        }
        return this.handleRequest(
            this.client.get(`/products/${params.productId}/variations/${params.variationId}`)
        );
    }

    // Product categories
    async listCategories(params: any) {
        return this.handleRequest(
            this.client.get('/products/categories', { params: this.toSnakeCase(params) })
        );
    }

    async getCategory(categoryId: number) {
        return this.handleRequest(
            this.client.get(`/products/categories/${categoryId}`)
        );
    }

    async createCategory(categoryData: any) {
        return this.handleRequest(
            this.client.post('/products/categories', categoryData)
        );
    }

    async updateCategory(categoryId: number, categoryData: any) {
        return this.handleRequest(
            this.client.put(`/products/categories/${categoryId}`, categoryData)
        );
    }

    // Product tags
    async listTags(params: any) {
        return this.handleRequest(
            this.client.get('/products/tags', { params: this.toSnakeCase(params) })
        );
    }

    async createTag(tagData: any) {
        return this.handleRequest(
            this.client.post('/products/tags', tagData)
        );
    }

    // Product attributes
    async listAttributes(params: any) {
        return this.handleRequest(
            this.client.get('/products/attributes', { params: this.toSnakeCase(params) })
        );
    }

    async getAttribute(attributeId: number) {
        return this.handleRequest(
            this.client.get(`/products/attributes/${attributeId}`)
        );
    }

    // Product reviews
    async listReviews(params: any) {
        return this.handleRequest(
            this.client.get('/products/reviews', { params: this.toSnakeCase(params) })
        );
    }

    async getReview(reviewId: number) {
        return this.handleRequest(
            this.client.get(`/products/reviews/${reviewId}`)
        );
    }

    async createReview(reviewData: any) {
        return this.handleRequest(
            this.client.post('/products/reviews', reviewData)
        );
    }

    async updateReview(reviewId: number, reviewData: any) {
        return this.handleRequest(
            this.client.put(`/products/reviews/${reviewId}`, reviewData)
        );
    }

    async deleteReview(reviewId: number, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/products/reviews/${reviewId}`, {
                params: { force }
            })
        );
    }
}