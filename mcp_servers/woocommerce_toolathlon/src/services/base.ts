import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { AsyncLocalStorage } from 'async_hooks';

export interface WooCommerceAuth {
    siteUrl: string;
    consumerKey: string;
    consumerSecret: string;
    username?: string;
    password?: string;
}

export const asyncLocalStorage = new AsyncLocalStorage<WooCommerceAuth>();

// Transport hardening against Bunny Shield WAF.
// - Fixed UA so Shield's fingerprint detectors don't classify us as a generic
//   axios bot and return HTML 403s.
// - 30s timeout: gives room to respond under concurrent load. A
//   previous 15s was too aggressive — requests that would eventually succeed
//   in 20-25s got killed, and the retries also kept timing out.
// - Retry ONLY on transient HTTP signals (429, 5xx, 403 with HTML body = WAF
//   block). Do NOT retry on pure timeout / network abort — those indicate
//   uniformly overloaded and piling on more requests makes it
//   worse. JSON 403 ({"code": "woocommerce_rest_cannot_view", ...}) is a
//   real auth error and is never retried.
const WOO_USER_AGENT = 'Klavis-Sandbox/1.0 (+https://klavis.ai)';
const REQUEST_TIMEOUT_MS = 30_000;
const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY_MS = 1_000;

type RetryableConfig = InternalAxiosRequestConfig & { __retryCount?: number };

function isHtmlBody(data: unknown): boolean {
    if (typeof data !== 'string') return false;
    const s = data.trimStart().toLowerCase();
    return s.startsWith('<!doctype') || s.startsWith('<html');
}

function isTransientError(error: AxiosError): boolean {
    // No response = network/timeout (ECONNABORTED, ECONNRESET, etc.).
    // Under concurrent overload, retrying these just amplifies
    // the problem — fail fast instead.
    if (!error.response) return false;
    const { status, data } = error.response;
    if (status === 429 || (status >= 500 && status <= 599)) return true;
    if (status === 403 && isHtmlBody(data)) return true;
    return false;
}

function delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

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

        const instance = axios.create({
            baseURL,
            timeout: REQUEST_TIMEOUT_MS,
            auth: {
                username: auth.consumerKey,
                password: auth.consumerSecret
            },
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': WOO_USER_AGENT,
            },
        });

        instance.interceptors.response.use(
            (response) => response,
            async (error: AxiosError) => {
                const config = error.config as RetryableConfig | undefined;
                if (!config || !isTransientError(error)) {
                    return Promise.reject(error);
                }
                config.__retryCount = (config.__retryCount ?? 0) + 1;
                if (config.__retryCount > MAX_RETRIES) {
                    return Promise.reject(error);
                }
                const backoff = INITIAL_RETRY_DELAY_MS * 2 ** (config.__retryCount - 1);
                const status = error.response?.status;
                const label = error.response
                    ? `HTTP ${status}${status === 403 ? ' WAF-HTML' : ''}`
                    : error.code ?? 'network';
                console.warn(
                    `[woo-retry] ${label} on ${config.method?.toUpperCase()} ${config.url} — ` +
                    `attempt ${config.__retryCount}/${MAX_RETRIES}, retry in ${backoff}ms`
                );
                await delay(backoff);
                return instance.request(config);
            }
        );

        return instance;
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
