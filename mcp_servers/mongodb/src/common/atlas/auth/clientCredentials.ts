import * as oauth from "oauth4webapi";
import type { LoggerBase } from "../../logger.js";
import { LogId } from "../../logger.js";
import { createFetch } from "@mongodb-js/devtools-proxy-support";
import type { AccessToken, AuthProvider } from "./authProvider.js";

export interface ClientCredentialsAuthOptions {
    clientId: string;
    clientSecret: string;
    baseUrl: string;
    userAgent: string;
}

export class ClientCredentialsAuthProvider implements AuthProvider {
    private oauth2Issuer?: oauth.AuthorizationServer;
    private accessToken?: AccessToken;
    private readonly options: ClientCredentialsAuthOptions;
    private readonly logger: LoggerBase;
    private customFetch: typeof fetch;

    constructor(options: ClientCredentialsAuthOptions, logger: LoggerBase) {
        this.options = options;
        this.logger = logger;

        this.oauth2Issuer = {
            issuer: options.baseUrl,
            token_endpoint: new URL("/api/oauth/token", options.baseUrl).toString(),
            revocation_endpoint: new URL("/api/oauth/revoke", options.baseUrl).toString(),
            token_endpoint_auth_methods_supported: ["client_secret_basic"],
            grant_types_supported: ["client_credentials"],
        };

        this.customFetch = createFetch({
            useEnvironmentVariableProxies: true,
        }) as unknown as typeof fetch;
    }

    public async getAuthHeaders(): Promise<Record<string, string> | undefined> {
        const accessToken = await this.getAccessToken();
        return accessToken
            ? {
                  Authorization: `Bearer ${accessToken}`,
              }
            : undefined;
    }

    private isAccessTokenValid(): boolean {
        return !!(
            this.accessToken &&
            this.accessToken.expires_at !== undefined &&
            this.accessToken.expires_at > Date.now()
        );
    }

    private getOauthClientAuth(): { client: oauth.Client | undefined; clientAuth: oauth.ClientAuth | undefined } {
        const clientSecret = this.options.clientSecret;
        const clientId = this.options.clientId;

        // We are using our own ClientAuth because ClientSecretBasic URL encodes wrongly
        // the username and password (for example, encodes `_` to %5F, which is wrong).
        return {
            client: { client_id: clientId },
            clientAuth: (_as, client, _body, headers): void => {
                const credentials = Buffer.from(`${clientId}:${clientSecret}`).toString("base64");
                headers.set("Authorization", `Basic ${credentials}`);
            },
        };
    }

    private async getNewAccessToken(): Promise<AccessToken | undefined> {
        if (!this.oauth2Issuer) {
            return undefined;
        }

        const { client, clientAuth } = this.getOauthClientAuth();
        if (client && clientAuth) {
            try {
                const response = await oauth.clientCredentialsGrantRequest(
                    this.oauth2Issuer,
                    client,
                    clientAuth,
                    new URLSearchParams(),
                    {
                        [oauth.customFetch]: this.customFetch,
                        headers: {
                            "User-Agent": this.options.userAgent,
                        },
                    }
                );

                const result = await oauth.processClientCredentialsResponse(this.oauth2Issuer, client, response);
                this.accessToken = {
                    access_token: result.access_token,
                    expires_at: Date.now() + (result.expires_in ?? 0) * 1000,
                };
            } catch (error: unknown) {
                const err = error instanceof Error ? error : new Error(String(error));
                this.logger.error({
                    id: LogId.atlasConnectFailure,
                    context: "clientCredentialsAuth",
                    message: `Failed to request access token: ${err.message}`,
                });
            }
            return this.accessToken;
        }

        return undefined;
    }

    private async getAccessToken(): Promise<string | undefined> {
        if (!this.isAccessTokenValid()) {
            this.accessToken = await this.getNewAccessToken();
        }

        return this.accessToken?.access_token;
    }

    public async validate(): Promise<boolean> {
        const token = await this.getAccessToken();
        return !!token;
    }

    public async revoke(): Promise<void> {
        const { client, clientAuth } = this.getOauthClientAuth();
        try {
            if (this.oauth2Issuer && this.accessToken && client && clientAuth) {
                await oauth.revocationRequest(this.oauth2Issuer, client, clientAuth, this.accessToken.access_token);
            }
        } catch (error: unknown) {
            const err = error instanceof Error ? error : new Error(String(error));
            this.logger.error({
                id: LogId.atlasApiRevokeFailure,
                context: "clientCredentialsAuth",
                message: `Failed to revoke access token: ${err.message}`,
            });
        }
        this.accessToken = undefined;
    }
}
