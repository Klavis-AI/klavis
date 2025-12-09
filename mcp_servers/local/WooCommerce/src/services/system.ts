import { BaseService } from './base.js';

export class SystemService extends BaseService {
    // System status
    async getSystemStatus() {
        return this.handleRequest(
            this.client.get('/system_status')
        );
    }

    async listSystemStatusTools() {
        return this.handleRequest(
            this.client.get('/system_status/tools')
        );
    }

    async runSystemStatusTool(toolId: string) {
        return this.handleRequest(
            this.client.put(`/system_status/tools/${toolId}`)
        );
    }

    // Settings
    async listSettings() {
        return this.handleRequest(
            this.client.get('/settings')
        );
    }

    async getSettingsGroup(groupId: string) {
        return this.handleRequest(
            this.client.get(`/settings/${groupId}`)
        );
    }

    async getSettingOption(groupId: string, optionId: string) {
        return this.handleRequest(
            this.client.get(`/settings/${groupId}/${optionId}`)
        );
    }

    async updateSettingOption(groupId: string, optionId: string, settingData: any) {
        return this.handleRequest(
            this.client.put(`/settings/${groupId}/${optionId}`, settingData)
        );
    }

    // Payment gateways
    async listPaymentGateways() {
        return this.handleRequest(
            this.client.get('/payment_gateways')
        );
    }

    async getPaymentGateway(gatewayId: string) {
        return this.handleRequest(
            this.client.get(`/payment_gateways/${gatewayId}`)
        );
    }

    async updatePaymentGateway(gatewayId: string, gatewayData: any) {
        return this.handleRequest(
            this.client.put(`/payment_gateways/${gatewayId}`, gatewayData)
        );
    }

    // Data
    async getDataEndpoints() {
        return this.handleRequest(
            this.client.get('/data')
        );
    }

    async getContinents() {
        return this.handleRequest(
            this.client.get('/data/continents')
        );
    }

    async getCountries() {
        return this.handleRequest(
            this.client.get('/data/countries')
        );
    }

    async getCurrencies() {
        return this.handleRequest(
            this.client.get('/data/currencies')
        );
    }

    async getCurrentCurrency() {
        return this.handleRequest(
            this.client.get('/data/currencies/current')
        );
    }

    // Webhooks
    async listWebhooks(params?: any) {
        return this.handleRequest(
            this.client.get('/webhooks', { params: this.toSnakeCase(params) })
        );
    }

    async getWebhook(webhookId: number) {
        return this.handleRequest(
            this.client.get(`/webhooks/${webhookId}`)
        );
    }

    async createWebhook(webhookData: any) {
        return this.handleRequest(
            this.client.post('/webhooks', webhookData)
        );
    }

    async updateWebhook(webhookId: number, webhookData: any) {
        return this.handleRequest(
            this.client.put(`/webhooks/${webhookId}`, webhookData)
        );
    }

    async deleteWebhook(webhookId: number, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/webhooks/${webhookId}`, {
                params: { force }
            })
        );
    }

    async batchUpdateWebhooks(params: any) {
        return this.handleRequest(
            this.client.post('/webhooks/batch', params)
        );
    }
}