import { BaseService } from './base.js';
import {
    CouponParams,
    CreateCouponParams,
    UpdateCouponParams,
    DeleteCouponParams,
    BatchUpdateParams
} from '../types.js';

export class CouponService extends BaseService {
    async listCoupons(params: CouponParams) {
        return this.handleRequest(
            this.client.get('/coupons', { params: this.toSnakeCase(params) })
        );
    }

    async getCoupon(params: CouponParams) {
        if (!params.couponId) {
            throw new Error('Coupon ID is required');
        }
        return this.handleRequest(
            this.client.get(`/coupons/${params.couponId}`)
        );
    }

    async createCoupon(params: CreateCouponParams) {
        if (!params.couponData) {
            throw new Error('Coupon data is required');
        }
        return this.handleRequest(
            this.client.post('/coupons', params.couponData)
        );
    }

    async updateCoupon(params: UpdateCouponParams) {
        if (!params.couponId) {
            throw new Error('Coupon ID is required');
        }
        if (!params.couponData) {
            throw new Error('Coupon data is required');
        }
        return this.handleRequest(
            this.client.put(`/coupons/${params.couponId}`, params.couponData)
        );
    }

    async deleteCoupon(params: DeleteCouponParams) {
        if (!params.couponId) {
            throw new Error('Coupon ID is required');
        }
        return this.handleRequest(
            this.client.delete(`/coupons/${params.couponId}`, {
                params: { force: params.force || true }
            })
        );
    }

    async batchUpdateCoupons(params: BatchUpdateParams) {
        return this.handleRequest(
            this.client.post('/coupons/batch', params)
        );
    }
}