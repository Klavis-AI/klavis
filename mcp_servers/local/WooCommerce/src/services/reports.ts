import { BaseService } from './base.js';
import { ReportParams } from '../types.js';

export class ReportService extends BaseService {
    async getSalesReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/sales', { params: this.toSnakeCase(params) })
        );
    }

    async getTopSellersReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/top_sellers', { params: this.toSnakeCase(params) })
        );
    }

    async getCouponsReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/coupons/totals', { params: this.toSnakeCase(params) })
        );
    }

    async getCustomersReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/customers/totals', { params: this.toSnakeCase(params) })
        );
    }

    async getOrdersReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/orders/totals', { params: this.toSnakeCase(params) })
        );
    }

    async getProductsReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/products/totals', { params: this.toSnakeCase(params) })
        );
    }

    async getReviewsReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/reviews/totals', { params: this.toSnakeCase(params) })
        );
    }

    async getStockReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/stock', { params: this.toSnakeCase(params) })
        );
    }

    async getLowStockReport(params: ReportParams) {
        return this.handleRequest(
            this.client.get('/reports/stock/low', { params: this.toSnakeCase(params) })
        );
    }
}