import open from 'open';
import * as dotenv from 'dotenv';

dotenv.config();

const KLAVIS_API_BASE_URL = "https://api.klavis.ai";

// Type definitions for API enums
export type ServerName = 
    | "Markdown2doc" | "Slack" | "Supabase" | "Postgres" | "YouTube" | "Doc2markdown"
    | "Klavis ReportGen" | "Resend" | "Discord" | "Firecrawl Web Search" | "GitHub"
    | "Firecrawl Deep Research" | "Jira" | "WordPress" | "Notion" | "Gmail"
    | "Google Drive" | "Google Calendar" | "Google Sheets" | "Google Docs"
    | "Attio" | "Salesforce" | "Linear" | "Asana" | "Close";

const OAUTH_SERVICE_NAME_TO_URL_PATH: Record<ServerName, string> = {
    'Slack': 'slack',
    'Supabase': 'supabase',
    'GitHub': 'github',
    'Google Drive': 'gdrive',
    'Google Calendar': 'gcalendar',
    'Google Sheets': 'gsheets',
    'Google Docs': 'gdocs',
    'Jira': 'jira',
    'WordPress': 'wordpress',
    'Notion': 'notion',
    'Gmail': 'gmail',
    'Asana': 'asana',
    'Linear': 'linear',
    'Salesforce': 'salesforce',
    'Close': 'close',
    'Attio': 'attio',
    // non oauth services
    'Markdown2doc': '',
    'Postgres': '',
    'YouTube': '',
    'Doc2markdown': '',
    'Klavis ReportGen': '',
    'Resend': '',
    'Discord': '',
    'Firecrawl Web Search': '',
    'Firecrawl Deep Research': '',
};

export type ConnectionType = "SSE" | "StreamableHttp";

export class KlavisAPI {
    private baseUrl: string;
    private apiKey: string;

    constructor(apiKey: string, baseUrl: string = KLAVIS_API_BASE_URL) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    async createMcpInstance(
        serverName: ServerName, 
        userId: string, 
        platformName: string, 
        connectionType: ConnectionType = "StreamableHttp"
    ): Promise<{ serverUrl: string; instanceId: string }> {
        if (!userId || userId.trim().length < 1) {
            throw new Error("userId must have minimum length of 1");
        }
        if (!platformName || platformName.trim().length < 1) {
            throw new Error("platformName must have minimum length of 1");
        }

        try {
            const response = await fetch(`${this.baseUrl}/mcp-server/instance/create`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    serverName,
                    userId,
                    platformName,
                    connectionType
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to create MCP instance: ${response.status} ${errorText}`);
            }

            const result = await response.json();
            console.info(`Created MCP instance: ${JSON.stringify(result)}`);

            if (!result.instanceId) {
                throw new Error("Response missing instanceId");
            }
            if (!result.serverUrl) {
                throw new Error("Response missing serverUrl");
            }

            return {
                serverUrl: result.serverUrl,
                instanceId: result.instanceId
            };
        } catch (error) {
            console.error('Error creating MCP instance:', error);
            throw error;
        }
    }

    async redirectToOauth(instanceId: string, serverName: ServerName): Promise<void> {
        const servicePath = OAUTH_SERVICE_NAME_TO_URL_PATH[serverName];
        if (!servicePath) {
            return; // Do not raise an error, skip it
        }

        const oauthUrl = `${this.baseUrl}/oauth/${servicePath}/authorize?instance_id=${instanceId}`;
        console.info(`Opening OAuth URL: ${oauthUrl}`);
        await open(oauthUrl);
    }

    async listTools(serverUrl: string, connectionType: ConnectionType = "StreamableHttp"): Promise<any> {
        try {
            const encodedServerUrl = encodeURIComponent(serverUrl);
            const url = new URL(`${this.baseUrl}/mcp-server/list-tools/${encodedServerUrl}`);
            url.searchParams.append('connection_type', connectionType);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    Authorization: `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to list tools: ${response.status} ${errorText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error listing tools:', error);
            throw error;
        }
    }

    async callTool(
        serverUrl: string, 
        toolName: string, 
        toolArgs: Record<string, any> | null = null, 
        connectionType: ConnectionType = "StreamableHttp"
    ): Promise<any> {
        try {
            const response = await fetch(`${this.baseUrl}/mcp-server/call-tool`, {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    serverUrl,
                    toolName,
                    toolArgs: toolArgs || {},
                    connectionType
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Failed to call tool '${toolName}': ${response.status} ${errorText}`);
            }

            const result = await response.json();
            console.info(`Called tool '${toolName}'`);
            return result;
        } catch (error) {
            console.error(`Error calling tool '${toolName}':`, error);
            throw error;
        }
    }
} 