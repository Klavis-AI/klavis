import { BaseService } from './base.js';
import { ShippingZoneParams, ShippingMethodParams } from '../types.js';

export class ShippingService extends BaseService {
    // Shipping zones
    async listShippingZones() {
        return this.handleRequest(
            this.client.get('/shipping/zones')
        );
    }

    async getShippingZone(params: ShippingZoneParams) {
        if (!params.zoneId) {
            throw new Error('Zone ID is required');
        }
        return this.handleRequest(
            this.client.get(`/shipping/zones/${params.zoneId}`)
        );
    }

    async createShippingZone(zoneData: any) {
        return this.handleRequest(
            this.client.post('/shipping/zones', zoneData)
        );
    }

    async updateShippingZone(zoneId: number, zoneData: any) {
        return this.handleRequest(
            this.client.put(`/shipping/zones/${zoneId}`, zoneData)
        );
    }

    async deleteShippingZone(zoneId: number, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/shipping/zones/${zoneId}`, {
                params: { force }
            })
        );
    }

    // Shipping zone locations
    async getShippingZoneLocations(zoneId: number) {
        return this.handleRequest(
            this.client.get(`/shipping/zones/${zoneId}/locations`)
        );
    }

    async updateShippingZoneLocations(zoneId: number, locations: any) {
        return this.handleRequest(
            this.client.put(`/shipping/zones/${zoneId}/locations`, locations)
        );
    }

    // Shipping zone methods
    async listShippingZoneMethods(params: ShippingMethodParams) {
        if (!params.zoneId) {
            throw new Error('Zone ID is required');
        }
        return this.handleRequest(
            this.client.get(`/shipping/zones/${params.zoneId}/methods`)
        );
    }

    async createShippingZoneMethod(params: ShippingMethodParams) {
        if (!params.zoneId || !params.methodData) {
            throw new Error('Zone ID and method data are required');
        }
        return this.handleRequest(
            this.client.post(`/shipping/zones/${params.zoneId}/methods`, params.methodData)
        );
    }

    async updateShippingZoneMethod(params: ShippingMethodParams) {
        if (!params.zoneId || !params.instanceId || !params.methodData) {
            throw new Error('Zone ID, instance ID and method data are required');
        }
        return this.handleRequest(
            this.client.put(
                `/shipping/zones/${params.zoneId}/methods/${params.instanceId}`,
                params.methodData
            )
        );
    }

    async deleteShippingZoneMethod(zoneId: number, instanceId: number, force: boolean = true) {
        return this.handleRequest(
            this.client.delete(`/shipping/zones/${zoneId}/methods/${instanceId}`, {
                params: { force }
            })
        );
    }

    // Shipping methods
    async listShippingMethods() {
        return this.handleRequest(
            this.client.get('/shipping_methods')
        );
    }

    async getShippingMethod(methodId: string) {
        return this.handleRequest(
            this.client.get(`/shipping_methods/${methodId}`)
        );
    }
}