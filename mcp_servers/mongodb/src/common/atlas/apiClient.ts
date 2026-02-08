import createClient, { Client, Middleware } from "openapi-fetch";
import type { FetchOptions } from "openapi-fetch";
import { AccessToken, ClientCredentials } from "simple-oauth2";
import { ApiClientError } from "./apiClientError.js";
import { paths, operations } from "./openapi.js";
import { CommonProperties, TelemetryEvent } from "../../telemetry/types.js";
import { packageInfo } from "../packageInfo.js";
import logger, { LogId } from "../logger.js";

const ATLAS_API_VERSION = "2025-03-12";

export interface ApiClientCredentials {
    clientId: string;
    clientSecret: string;
}

export interface ApiClientOptions {
    credentials?: ApiClientCredentials;
    baseUrl: string;
    userAgent?: string;
}

export class ApiClient {
    private options: {
        baseUrl: string;
        userAgent: string;
        credentials?: {
            clientId: string;
            clientSecret: string;
        };
    };
    private client: Client<paths>;
    private oauth2Client?: ClientCredentials;
    private accessToken?: AccessToken;

    private getAccessToken = async () => {
        if (this.oauth2Client && (!this.accessToken || this.accessToken.expired())) {
            this.accessToken = await this.oauth2Client.getToken({});
        }
        return this.accessToken?.token.access_token as string | undefined;
    };

    private authMiddleware: Middleware = {
        onRequest: async ({ request, schemaPath }) => {
            if (schemaPath.startsWith("/api/private/unauth") || schemaPath.startsWith("/api/oauth")) {
                return undefined;
            }

            try {
                const accessToken = await this.getAccessToken();
                if (accessToken) {
                    request.headers.set("Authorization", `Bearer ${accessToken}`);
                }
                return request;
            } catch {
                // ignore not availble tokens, API will return 401
            }
        },
    };

    constructor(options: ApiClientOptions) {
        this.options = {
            ...options,
            userAgent:
                options.userAgent ||
                `AtlasMCP/${packageInfo.version} (${process.platform}; ${process.arch}; ${process.env.HOSTNAME || "unknown"})`,
        };

        this.client = createClient<paths>({
            baseUrl: this.options.baseUrl,
            headers: {
                "User-Agent": this.options.userAgent,
                Accept: `application/vnd.atlas.${ATLAS_API_VERSION}+json`,
            },
        });
        if (this.options.credentials?.clientId && this.options.credentials?.clientSecret) {
            this.oauth2Client = new ClientCredentials({
                client: {
                    id: this.options.credentials.clientId,
                    secret: this.options.credentials.clientSecret,
                },
                auth: {
                    tokenHost: this.options.baseUrl,
                    tokenPath: "/api/oauth/token",
                    revokePath: "/api/oauth/revoke",
                },
                http: {
                    headers: {
                        "User-Agent": this.options.userAgent,
                    },
                },
            });
            this.client.use(this.authMiddleware);
        }
    }

    public hasCredentials(): boolean {
        return !!this.oauth2Client;
    }

    public async validateAccessToken(): Promise<void> {
        await this.getAccessToken();
    }

    public async close(): Promise<void> {
        if (this.accessToken) {
            try {
                await this.accessToken.revoke("access_token");
            } catch (error: unknown) {
                const err = error instanceof Error ? error : new Error(String(error));
                logger.error(LogId.atlasApiRevokeFailure, "apiClient", `Failed to revoke access token: ${err.message}`);
            }
            this.accessToken = undefined;
        }
    }

    public async getIpInfo(): Promise<{
        currentIpv4Address: string;
    }> {
        const accessToken = await this.getAccessToken();

        const endpoint = "api/private/ipinfo";
        const url = new URL(endpoint, this.options.baseUrl);
        const response = await fetch(url, {
            method: "GET",
            headers: {
                Accept: "application/json",
                Authorization: `Bearer ${accessToken}`,
                "User-Agent": this.options.userAgent,
            },
        });

        if (!response.ok) {
            throw await ApiClientError.fromResponse(response);
        }

        return (await response.json()) as Promise<{
            currentIpv4Address: string;
        }>;
    }

    public async sendEvents(events: TelemetryEvent<CommonProperties>[]): Promise<void> {
        if (!this.options.credentials) {
            await this.sendUnauthEvents(events);
            return;
        }

        try {
            await this.sendAuthEvents(events);
        } catch (error) {
            if (error instanceof ApiClientError) {
                if (error.response.status !== 401) {
                    throw error;
                }
            }

            // send unauth events if any of the following are true:
            // 1: the token is not valid (not ApiClientError)
            // 2: if the api responded with 401 (ApiClientError with status 401)
            await this.sendUnauthEvents(events);
        }
    }

    private async sendAuthEvents(events: TelemetryEvent<CommonProperties>[]): Promise<void> {
        const accessToken = await this.getAccessToken();
        if (!accessToken) {
            throw new Error("No access token available");
        }
        const authUrl = new URL("api/private/v1.0/telemetry/events", this.options.baseUrl);
        const response = await fetch(authUrl, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                "User-Agent": this.options.userAgent,
                Authorization: `Bearer ${accessToken}`,
            },
            body: JSON.stringify(events),
        });

        if (!response.ok) {
            throw await ApiClientError.fromResponse(response);
        }
    }

    private async sendUnauthEvents(events: TelemetryEvent<CommonProperties>[]): Promise<void> {
        const headers: Record<string, string> = {
            Accept: "application/json",
            "Content-Type": "application/json",
            "User-Agent": this.options.userAgent,
        };

        const unauthUrl = new URL("api/private/unauth/telemetry/events", this.options.baseUrl);
        const response = await fetch(unauthUrl, {
            method: "POST",
            headers,
            body: JSON.stringify(events),
        });

        if (!response.ok) {
            throw await ApiClientError.fromResponse(response);
        }
    }

    // DO NOT EDIT. This is auto-generated code.
    async listClustersForAllProjects(options?: FetchOptions<operations["listClustersForAllProjects"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/clusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async listProjects(options?: FetchOptions<operations["listProjects"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async createProject(options: FetchOptions<operations["createProject"]>) {
        const { data, error, response } = await this.client.POST("/api/atlas/v2/groups", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async deleteProject(options: FetchOptions<operations["deleteProject"]>) {
        const { error, response } = await this.client.DELETE("/api/atlas/v2/groups/{groupId}", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    async getProject(options: FetchOptions<operations["getProject"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async listProjectIpAccessLists(options: FetchOptions<operations["listProjectIpAccessLists"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/accessList", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async createProjectIpAccessList(options: FetchOptions<operations["createProjectIpAccessList"]>) {
        const { data, error, response } = await this.client.POST("/api/atlas/v2/groups/{groupId}/accessList", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async deleteProjectIpAccessList(options: FetchOptions<operations["deleteProjectIpAccessList"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/accessList/{entryValue}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    async listAlerts(options: FetchOptions<operations["listAlerts"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/alerts", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async listClusters(options: FetchOptions<operations["listClusters"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/clusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async createCluster(options: FetchOptions<operations["createCluster"]>) {
        const { data, error, response } = await this.client.POST("/api/atlas/v2/groups/{groupId}/clusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async deleteCluster(options: FetchOptions<operations["deleteCluster"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/clusters/{clusterName}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    async getCluster(options: FetchOptions<operations["getCluster"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/clusters/{clusterName}",
            options
        );

        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async listDatabaseUsers(options: FetchOptions<operations["listDatabaseUsers"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/databaseUsers",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async createDatabaseUser(options: FetchOptions<operations["createDatabaseUser"]>) {
        const { data, error, response } = await this.client.POST(
            "/api/atlas/v2/groups/{groupId}/databaseUsers",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async deleteDatabaseUser(options: FetchOptions<operations["deleteDatabaseUser"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/databaseUsers/{databaseName}/{username}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    async listFlexClusters(options: FetchOptions<operations["listFlexClusters"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/flexClusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async createFlexCluster(options: FetchOptions<operations["createFlexCluster"]>) {
        const { data, error, response } = await this.client.POST(
            "/api/atlas/v2/groups/{groupId}/flexClusters",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async deleteFlexCluster(options: FetchOptions<operations["deleteFlexCluster"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/flexClusters/{name}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    async getFlexCluster(options: FetchOptions<operations["getFlexCluster"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/flexClusters/{name}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async listOrganizations(options?: FetchOptions<operations["listOrganizations"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/orgs", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    async listOrganizationProjects(options: FetchOptions<operations["listOrganizationProjects"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/orgs/{orgId}/groups", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // DO NOT EDIT. This is auto-generated code.
}
