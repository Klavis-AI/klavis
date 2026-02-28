import axios, { AxiosInstance } from 'axios';
import { AsyncLocalStorage } from 'async_hooks';

export interface WooCommerceAuth {
    siteUrl: string;
    consumerKey: string;
    consumerSecret: string;
    username?: string;
    password?: string;
}

export const asyncLocalStorage = new AsyncLocalStorage<WooCommerceAuth>();

/**
 * Extract WooCommerce auth from AUTH_DATA env var or x-auth-data header (base64-encoded JSON).
 */
export function extractAuthData(req?: { headers?: Record<string, any> } | null): WooCommerceAuth {
    let authData = process.env.AUTH_DATA;

    if (!authData) {
        const siteUrl = process.env.WORDPRESS_SITE_URL;
        const consumerKey = process.env.WOOCOMMERCE_CONSUMER_KEY;
        const consumerSecret = process.env.WOOCOMMERCE_CONSUMER_SECRET;
        if (siteUrl && consumerKey && consumerSecret) {
            return {
                siteUrl,
                consumerKey,
                consumerSecret,
                username: process.env.WORDPRESS_USERNAME,
                password: process.env.WORDPRESS_PASSWORD,
            };
        }
    }

    if (!authData && req?.headers?.['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error decoding x-auth-data header:', error);
        }
    }

    if (!authData) {
        console.error('Error: WooCommerce auth missing. Provide via AUTH_DATA env var, individual env vars, or x-auth-data header.');
        return { siteUrl: '', consumerKey: '', consumerSecret: '' };
    }

    try {
        const json = JSON.parse(authData);
        const mask = (v: string | undefined) => v ? v.slice(0, 4) + '***' + v.slice(-4) : undefined;
        console.log('Parsed woocommerce auth data:', {
            site_url: json.site_url,
            consumer_key: mask(json.consumer_key),
            consumer_secret: mask(json.consumer_secret),
            admin_username: json.admin_username,
            admin_password: mask(json.admin_password),
        });
        return {
            siteUrl: json.site_url ?? '',
            consumerKey: json.consumer_key ?? '',
            consumerSecret: json.consumer_secret ?? '',
            username: json.admin_username,
            password: json.admin_password,
        };
    } catch {
        console.error('Error parsing auth data JSON');
        return { siteUrl: '', consumerKey: '', consumerSecret: '' };
    }
}


function getAuth(): WooCommerceAuth {
    const store = asyncLocalStorage.getStore();
    if (store) return store;
    return extractAuthData(null);
}

export class BaseService {
    protected get client(): AxiosInstance {
        const auth = getAuth();
        const siteUrl = auth.siteUrl.replace(/\/$/, '');
        const baseURL = `${siteUrl}/wp-json/wc/v3`;

        return axios.create({
            baseURL,
            auth: {
                username: auth.consumerKey,
                password: auth.consumerSecret
            },
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }

    protected toSnakeCase(params: any): any {
        if (!params || typeof params !== 'object') {
            return params;
        }

        const result: any = {};
        for (const key in params) {
            if (params.hasOwnProperty(key)) {
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
