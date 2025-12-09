import axios, { AxiosInstance } from 'axios';

export class BaseService {
    protected client: AxiosInstance;
    protected siteUrl: string;
    protected consumerKey: string;
    protected consumerSecret: string;

    constructor() {
        this.siteUrl = process.env.WORDPRESS_SITE_URL!;
        this.consumerKey = process.env.WOOCOMMERCE_CONSUMER_KEY!;
        this.consumerSecret = process.env.WOOCOMMERCE_CONSUMER_SECRET!;

        // 移除末尾的斜杠
        this.siteUrl = this.siteUrl.replace(/\/$/, '');

        const baseURL = `${this.siteUrl}/wp-json/wc/v3`;
        
        console.error(`[WooCommerce] Initializing with base URL: ${baseURL}`);

        this.client = axios.create({
            baseURL,
            auth: {
                username: this.consumerKey,
                password: this.consumerSecret
            },
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // 添加请求拦截器用于调试
        this.client.interceptors.request.use(
            (config) => {
                console.error(`[WooCommerce] Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
                console.error(`[WooCommerce] Params:`, config.params);
                return config;
            },
            (error) => {
                console.error('[WooCommerce] Request error:', error);
                return Promise.reject(error);
            }
        );

        // 添加响应拦截器用于调试
        this.client.interceptors.response.use(
            (response) => {
                console.error(`[WooCommerce] Response: ${response.status} ${response.statusText}`);
                return response;
            },
            (error) => {
                if (error.response) {
                    console.error(`[WooCommerce] Response error: ${error.response.status} ${error.response.statusText}`);
                    console.error(`[WooCommerce] Response URL: ${error.config?.url}`);
                    console.error(`[WooCommerce] Response data:`, error.response.data);
                }
                return Promise.reject(error);
            }
        );
    }

    /**
     * Convert camelCase object keys to snake_case for WooCommerce API
     */
    protected toSnakeCase(params: any): any {
        if (!params || typeof params !== 'object') {
            return params;
        }

        const result: any = {};
        for (const key in params) {
            if (params.hasOwnProperty(key)) {
                // Convert camelCase to snake_case
                const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
                result[snakeKey] = params[key];
            }
        }
        return result;
    }

    protected async handleRequest<T>(request: Promise<any>): Promise<T> {
        try {
            const response = await request;
            return response.data;
        } catch (error: any) {
            if (error.response) {
                const message = error.response.data?.message || error.response.data?.code || error.message;
                const status = error.response.status;

                if (status === 404) {
                    throw new Error(`WooCommerce API endpoint not found. Please check if WooCommerce is installed and REST API is enabled. URL: ${error.config?.url}`);
                } else if (status === 401) {
                    throw new Error(`WooCommerce API authentication failed. Please check your consumer key and secret.`);
                } else if (status === 403) {
                    throw new Error(`WooCommerce API access forbidden. Please check your API key permissions.`);
                }

                throw new Error(`WooCommerce API error: ${message} (Status: ${status})`);
            }
            throw error;
        }
    }
}