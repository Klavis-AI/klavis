import { BaseService } from './base.js';
import { TaxRateParams, TaxRateData } from '../types.js';

export class TaxService extends BaseService {
    // Tax classes
    async listTaxClasses() {
        return this.handleRequest(
            this.client.get('/taxes/classes')
        );
    }

    async createTaxClass(taxClassData: any) {
        return this.handleRequest(
            this.client.post('/taxes/classes', taxClassData)
        );
    }

    async deleteTaxClass(slug: string, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/taxes/classes/${slug}`, {
                params: { force }
            })
        );
    }

    // Tax rates
    async listTaxRates(params: TaxRateParams) {
        return this.handleRequest(
            this.client.get('/taxes', { params: this.toSnakeCase(params) })
        );
    }

    async getTaxRate(params: TaxRateParams) {
        if (!params.rateId) {
            throw new Error('Tax rate ID is required');
        }
        return this.handleRequest(
            this.client.get(`/taxes/${params.rateId}`)
        );
    }

    async createTaxRate(taxRateData: TaxRateData) {
        return this.handleRequest(
            this.client.post('/taxes', taxRateData)
        );
    }

    async updateTaxRate(rateId: number, taxRateData: TaxRateData) {
        return this.handleRequest(
            this.client.put(`/taxes/${rateId}`, taxRateData)
        );
    }

    async deleteTaxRate(rateId: number, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/taxes/${rateId}`, {
                params: { force }
            })
        );
    }

    async batchUpdateTaxRates(params: any) {
        return this.handleRequest(
            this.client.post('/taxes/batch', params)
        );
    }
}