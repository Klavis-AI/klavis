import createClient from "openapi-fetch";
import type { ClientOptions, FetchOptions, Client, Middleware } from "openapi-fetch";
import { ApiClientError } from "./apiClientError.js";
import type { paths, operations } from "./openapi.js";
import type { CommonProperties, TelemetryEvent } from "../../telemetry/types.js";
import { packageInfo } from "../packageInfo.js";
import type { LoggerBase } from "../logger.js";
import { createFetch } from "@mongodb-js/devtools-proxy-support";
import { Request as NodeFetchRequest } from "node-fetch";
import type { Credentials, AuthProvider } from "./auth/authProvider.js";
import { AuthProviderFactory } from "./auth/authProvider.js";

const ATLAS_API_VERSION = "2025-03-12";

export interface ApiClientOptions {
    baseUrl: string;
    userAgent?: string;
    credentials?: Credentials;
    requestContext?: RequestContext;
}

type RequestContext = {
    headers?: Record<string, string | string[] | undefined>;
};

export type ApiClientFactoryFn = (options: ApiClientOptions, logger: LoggerBase) => ApiClient;

export const createAtlasApiClient: ApiClientFactoryFn = (options, logger) => {
    return new ApiClient(options, logger);
};

export class ApiClient {
    private readonly options: {
        baseUrl: string;
        userAgent: string;
    };

    private customFetch: typeof fetch;

    private client: Client<paths>;

    public isAuthConfigured(): boolean {
        return !!this.authProvider;
    }

    constructor(
        options: ApiClientOptions,
        public readonly logger: LoggerBase,
        public readonly authProvider?: AuthProvider
    ) {
        // createFetch assumes that the first parameter of fetch is always a string
        // with the URL. However, fetch can also receive a Request object. While
        // the typechecking complains, createFetch does passthrough the parameters
        // so it works fine. That said, node-fetch has incompatibilities with the web version
        // of fetch and can lead to genuine issues so we would like to move away of node-fetch dependency.
        this.customFetch = createFetch({
            useEnvironmentVariableProxies: true,
        }) as unknown as typeof fetch;
        this.options = {
            ...options,
            userAgent:
                options.userAgent ??
                `AtlasMCP/${packageInfo.version} (${process.platform}; ${process.arch}; ${process.env.HOSTNAME || "unknown"})`,
        };

        this.authProvider =
            authProvider ??
            AuthProviderFactory.create(
                {
                    apiBaseUrl: this.options.baseUrl,
                    userAgent: this.options.userAgent,
                    credentials: options.credentials ?? {},
                },
                logger
            );

        this.client = createClient<paths>({
            baseUrl: this.options.baseUrl,
            headers: {
                "User-Agent": this.options.userAgent,
                Accept: `application/vnd.atlas.${ATLAS_API_VERSION}+json`,
            },
            fetch: this.customFetch,
            // NodeFetchRequest has more overloadings than the native Request
            // so it complains here. However, the interfaces are actually compatible
            // so it's not a real problem, just a type checking problem.
            Request: NodeFetchRequest as unknown as ClientOptions["Request"],
        });

        if (this.authProvider) {
            this.client.use(this.createAuthMiddleware());
        }
    }

    private createAuthMiddleware(): Middleware {
        return {
            onRequest: async ({ request, schemaPath }): Promise<Request | undefined> => {
                if (schemaPath.startsWith("/api/private/unauth") || schemaPath.startsWith("/api/oauth")) {
                    return undefined;
                }

                try {
                    const authHeaders = (await this.authProvider?.getAuthHeaders()) ?? {};
                    for (const [key, value] of Object.entries(authHeaders)) {
                        request.headers.set(key, value);
                    }
                    return request;
                } catch {
                    // ignore not available tokens, API will return 401
                    return undefined;
                }
            },
        };
    }

    public async validateAuthConfig(): Promise<void> {
        await this.authProvider?.validate();
    }

    public async close(): Promise<void> {
        await this.authProvider?.revoke();
    }

    public async getIpInfo(): Promise<{
        currentIpv4Address: string;
    }> {
        const authHeaders = (await this.authProvider?.getAuthHeaders()) ?? {};

        const endpoint = "api/private/ipinfo";
        const url = new URL(endpoint, this.options.baseUrl);
        const response = await fetch(url, {
            method: "GET",
            headers: {
                ...authHeaders,
                Accept: "application/json",
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
        if (!this.authProvider) {
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
        const authHeaders = await this.authProvider?.getAuthHeaders();
        if (!authHeaders) {
            throw new Error("No access token available");
        }
        const authUrl = new URL("api/private/v1.0/telemetry/events", this.options.baseUrl);
        const response = await fetch(authUrl, {
            method: "POST",
            headers: {
                ...authHeaders,
                Accept: "application/json",
                "Content-Type": "application/json",
                "User-Agent": this.options.userAgent,
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
    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listClusterDetails(options?: FetchOptions<operations["listClusterDetails"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/clusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listGroups(options?: FetchOptions<operations["listGroups"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async createGroup(options: FetchOptions<operations["createGroup"]>) {
        const { data, error, response } = await this.client.POST("/api/atlas/v2/groups", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async deleteGroup(options: FetchOptions<operations["deleteGroup"]>) {
        const { error, response } = await this.client.DELETE("/api/atlas/v2/groups/{groupId}", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async getGroup(options: FetchOptions<operations["getGroup"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listAccessListEntries(options: FetchOptions<operations["listGroupAccessListEntries"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/accessList", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async createAccessListEntry(options: FetchOptions<operations["createGroupAccessListEntry"]>) {
        const { data, error, response } = await this.client.POST("/api/atlas/v2/groups/{groupId}/accessList", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async deleteAccessListEntry(options: FetchOptions<operations["deleteGroupAccessListEntry"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/accessList/{entryValue}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listAlerts(options: FetchOptions<operations["listGroupAlerts"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/alerts", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listClusters(options: FetchOptions<operations["listGroupClusters"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/clusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async createCluster(options: FetchOptions<operations["createGroupCluster"]>) {
        const { data, error, response } = await this.client.POST("/api/atlas/v2/groups/{groupId}/clusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async deleteCluster(options: FetchOptions<operations["deleteGroupCluster"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/clusters/{clusterName}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async getCluster(options: FetchOptions<operations["getGroupCluster"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/clusters/{clusterName}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listDropIndexSuggestions(
        options: FetchOptions<operations["listGroupClusterPerformanceAdvisorDropIndexSuggestions"]>
    ) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/clusters/{clusterName}/performanceAdvisor/dropIndexSuggestions",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listSchemaAdvice(options: FetchOptions<operations["listGroupClusterPerformanceAdvisorSchemaAdvice"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/clusters/{clusterName}/performanceAdvisor/schemaAdvice",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listClusterSuggestedIndexes(
        options: FetchOptions<operations["listGroupClusterPerformanceAdvisorSuggestedIndexes"]>
    ) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/clusters/{clusterName}/performanceAdvisor/suggestedIndexes",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listDatabaseUsers(options: FetchOptions<operations["listGroupDatabaseUsers"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/databaseUsers",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async createDatabaseUser(options: FetchOptions<operations["createGroupDatabaseUser"]>) {
        const { data, error, response } = await this.client.POST(
            "/api/atlas/v2/groups/{groupId}/databaseUsers",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async deleteDatabaseUser(options: FetchOptions<operations["deleteGroupDatabaseUser"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/databaseUsers/{databaseName}/{username}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listFlexClusters(options: FetchOptions<operations["listGroupFlexClusters"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/groups/{groupId}/flexClusters", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async createFlexCluster(options: FetchOptions<operations["createGroupFlexCluster"]>) {
        const { data, error, response } = await this.client.POST(
            "/api/atlas/v2/groups/{groupId}/flexClusters",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async deleteFlexCluster(options: FetchOptions<operations["deleteGroupFlexCluster"]>) {
        const { error, response } = await this.client.DELETE(
            "/api/atlas/v2/groups/{groupId}/flexClusters/{name}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async getFlexCluster(options: FetchOptions<operations["getGroupFlexCluster"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/flexClusters/{name}",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listSlowQueryLogs(options: FetchOptions<operations["listGroupProcessPerformanceAdvisorSlowQueryLogs"]>) {
        const { data, error, response } = await this.client.GET(
            "/api/atlas/v2/groups/{groupId}/processes/{processId}/performanceAdvisor/slowQueryLogs",
            options
        );
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async listOrgs(options?: FetchOptions<operations["listOrgs"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/orgs", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
    async getOrgGroups(options: FetchOptions<operations["getOrgGroups"]>) {
        const { data, error, response } = await this.client.GET("/api/atlas/v2/orgs/{orgId}/groups", options);
        if (error) {
            throw ApiClientError.fromError(response, error);
        }
        return data;
    }

    // DO NOT EDIT. This is auto-generated code.
}
