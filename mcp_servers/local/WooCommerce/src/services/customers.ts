import { BaseService } from './base.js';
import {
    CustomerParams,
    CreateCustomerParams,
    UpdateCustomerParams,
    DeleteCustomerParams,
    BatchUpdateParams
} from '../types.js';

export class CustomerService extends BaseService {
    async listCustomers(params: CustomerParams) {
        return this.handleRequest(
            this.client.get('/customers', { params: this.toSnakeCase(params) })
        );
    }

    async getCustomer(params: CustomerParams) {
        if (!params.customerId) {
            throw new Error('Customer ID is required');
        }
        return this.handleRequest(
            this.client.get(`/customers/${params.customerId}`)
        );
    }

    async createCustomer(params: CreateCustomerParams) {
        if (!params.customerData) {
            throw new Error('Customer data is required');
        }
        return this.handleRequest(
            this.client.post('/customers', params.customerData)
        );
    }

    async updateCustomer(params: UpdateCustomerParams) {
        if (!params.customerId) {
            throw new Error('Customer ID is required');
        }
        if (!params.customerData) {
            throw new Error('Customer data is required');
        }
        return this.handleRequest(
            this.client.put(`/customers/${params.customerId}`, params.customerData)
        );
    }

    async deleteCustomer(params: DeleteCustomerParams) {
        if (!params.customerId) {
            throw new Error('Customer ID is required');
        }
        return this.handleRequest(
            this.client.delete(`/customers/${params.customerId}`, {
                params: { force: params.force || false }
            })
        );
    }

    async batchUpdateCustomers(params: BatchUpdateParams) {
        return this.handleRequest(
            this.client.post('/customers/batch', params)
        );
    }

    async getCustomerOrders(customerId: number, params?: any) {
        return this.handleRequest(
            this.client.get('/orders', {
                params: this.toSnakeCase({
                    customer: customerId,
                    ...params
                })
            })
        );
    }

    async getCustomerDownloads(customerId: number) {
        return this.handleRequest(
            this.client.get(`/customers/${customerId}/downloads`)
        );
    }
}