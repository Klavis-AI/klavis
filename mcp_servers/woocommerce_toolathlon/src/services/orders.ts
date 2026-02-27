import { BaseService } from './base.js';
import {
    OrderParams,
    CreateOrderParams,
    UpdateOrderParams,
    DeleteOrderParams,
    BatchUpdateParams
} from '../types.js';

export class OrderService extends BaseService {
    async listOrders(params: OrderParams) {
        return this.handleRequest(
            this.client.get('/orders', { params: this.toSnakeCase(params) })
        );
    }

    async getOrder(params: OrderParams) {
        if (!params.orderId) {
            throw new Error('Order ID is required');
        }
        return this.handleRequest(
            this.client.get(`/orders/${params.orderId}`)
        );
    }

    async createOrder(params: CreateOrderParams) {
        if (!params.orderData) {
            throw new Error('Order data is required');
        }
        return this.handleRequest(
            this.client.post('/orders', params.orderData)
        );
    }

    async updateOrder(params: UpdateOrderParams) {
        if (!params.orderId) {
            throw new Error('Order ID is required');
        }
        if (!params.orderData) {
            throw new Error('Order data is required');
        }
        return this.handleRequest(
            this.client.put(`/orders/${params.orderId}`, params.orderData)
        );
    }

    async deleteOrder(params: DeleteOrderParams) {
        if (!params.orderId) {
            throw new Error('Order ID is required');
        }
        return this.handleRequest(
            this.client.delete(`/orders/${params.orderId}`, {
                params: { force: params.force || false }
            })
        );
    }

    async batchUpdateOrders(params: BatchUpdateParams) {
        return this.handleRequest(
            this.client.post('/orders/batch', params)
        );
    }

    // Order notes
    async listOrderNotes(orderId: number, params?: any) {
        return this.handleRequest(
            this.client.get(`/orders/${orderId}/notes`, { params: this.toSnakeCase(params) })
        );
    }

    async getOrderNote(orderId: number, noteId: number) {
        return this.handleRequest(
            this.client.get(`/orders/${orderId}/notes/${noteId}`)
        );
    }

    async createOrderNote(orderId: number, noteData: any) {
        return this.handleRequest(
            this.client.post(`/orders/${orderId}/notes`, noteData)
        );
    }

    async deleteOrderNote(orderId: number, noteId: number, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/orders/${orderId}/notes/${noteId}`, {
                params: { force }
            })
        );
    }

    // Refunds
    async listRefunds(orderId: number, params?: any) {
        return this.handleRequest(
            this.client.get(`/orders/${orderId}/refunds`, { params: this.toSnakeCase(params) })
        );
    }

    async getRefund(orderId: number, refundId: number) {
        return this.handleRequest(
            this.client.get(`/orders/${orderId}/refunds/${refundId}`)
        );
    }

    async createRefund(orderId: number, refundData: any) {
        return this.handleRequest(
            this.client.post(`/orders/${orderId}/refunds`, refundData)
        );
    }

    async deleteRefund(orderId: number, refundId: number, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/orders/${orderId}/refunds/${refundId}`, {
                params: { force }
            })
        );
    }
}