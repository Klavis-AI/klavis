import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { CallToolRequestSchema, JSONRPCResponse, ListToolsRequestSchema, Tool } from '@modelcontextprotocol/sdk/types.js'
import { JSONSchema7 as IJsonSchema } from 'json-schema'
import { OpenAPIToMCPConverter } from '../openapi/parser'
import { HttpClient, HttpClientError } from '../client/http-client'
import { OpenAPIV3 } from 'openapi-types'
import { Transport } from '@modelcontextprotocol/sdk/shared/transport.js'

type PathItemObject = OpenAPIV3.PathItemObject & {
  get?: OpenAPIV3.OperationObject
  put?: OpenAPIV3.OperationObject
  post?: OpenAPIV3.OperationObject
  delete?: OpenAPIV3.OperationObject
  patch?: OpenAPIV3.OperationObject
}

type NewToolDefinition = {
  methods: Array<{
    name: string
    description: string
    inputSchema: IJsonSchema & { type: 'object' }
    returnSchema?: IJsonSchema
  }>
}

// State that is safe to share across requests: the parsed OpenAPI spec,
// converted MCP tool definitions, the operation lookup table, and the axios
// client (which has NO auth headers baked in — token is injected per call).
export type SharedProxyState = {
  tools: Record<string, NewToolDefinition>
  openApiLookup: Record<string, OpenAPIV3.OperationObject & { method: string; path: string }>
  httpClient: HttpClient
}

export function buildSharedProxyState(openApiSpec: OpenAPIV3.Document): SharedProxyState {
  const baseUrl = openApiSpec.servers?.[0].url
  if (!baseUrl) {
    throw new Error('No base URL found in OpenAPI spec')
  }
  const httpClient = new HttpClient({ baseUrl, headers: {} }, openApiSpec)
  const converter = new OpenAPIToMCPConverter(openApiSpec)
  const { tools, openApiLookup } = converter.convertToMCPTools()
  return { tools, openApiLookup, httpClient }
}

// import this class, extend and return server
export class MCPProxy {
  private server: Server
  private httpClient: HttpClient
  private tools: Record<string, NewToolDefinition>
  private openApiLookup: Record<string, OpenAPIV3.OperationObject & { method: string; path: string }>
  private notionToken?: string

  constructor(
    name: string,
    specOrShared: OpenAPIV3.Document | SharedProxyState,
    notionToken?: string,
  ) {
    this.server = new Server({ name, version: '1.0.0' }, { capabilities: { tools: {} } })
    this.notionToken = notionToken

    if ('httpClient' in specOrShared) {
      // Hot path: reuse the shared parsed/converted/axios state.
      this.httpClient = specOrShared.httpClient
      this.tools = specOrShared.tools
      this.openApiLookup = specOrShared.openApiLookup
    } else {
      // Legacy path (stdio / tests): parse + convert + build axios per instance.
      const shared = buildSharedProxyState(specOrShared)
      this.tools = shared.tools
      this.openApiLookup = shared.openApiLookup
      this.httpClient = shared.httpClient
      // stdio mode: fall back to env-based auth if no per-request token
      if (!notionToken) {
        const envHeaders = this.parseHeadersFromEnv(undefined)
        const envToken = envHeaders['Authorization']?.replace(/^Bearer\s+/, '')
        if (envToken) this.notionToken = envToken
      }
    }

    this.setupHandlers()
  }

  private setupHandlers() {
    // Handle tool listing
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const tools: Tool[] = []

      // Add methods as separate tools to match the MCP format
      Object.entries(this.tools).forEach(([toolName, def]) => {
        def.methods.forEach(method => {
          const toolNameWithMethod = `${toolName}-${method.name}`;
          const truncatedToolName = this.truncateToolName(toolNameWithMethod);
          tools.push({
            name: truncatedToolName,
            description: method.description,
            inputSchema: method.inputSchema as Tool['inputSchema'],
          })
        })
      })

      return { tools }
    })

    // Handle tool calling
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: params } = request.params

      // Find the operation in OpenAPI spec
      const operation = this.findOperation(name)
      if (!operation) {
        throw new Error(`Method ${name} not found`)
      }

      try {
        // Execute the operation (inject per-request Notion token)
        const response = await this.httpClient.executeOperation(operation, params, this.notionToken)

        // Convert response to MCP format
        return {
          content: [
            {
              type: 'text', // currently this is the only type that seems to be used by mcp server
              text: JSON.stringify(response.data), // TODO: pass through the http status code text?
            },
          ],
        }
      } catch (error) {
        console.error('Error in tool call', error)
        if (error instanceof HttpClientError) {
          console.error('HttpClientError encountered, returning structured error', error)
          const data = error.data?.response?.data ?? error.data ?? {}
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({
                  status: 'error', // TODO: get this from http status code?
                  ...(typeof data === 'object' ? data : { data: data }),
                }),
              },
            ],
          }
        }
        throw error
      }
    })
  }

  private findOperation(operationId: string): (OpenAPIV3.OperationObject & { method: string; path: string }) | null {
    return this.openApiLookup[operationId] ?? null
  }

  private parseHeadersFromEnv(notionToken?: string): Record<string, string> {
    // First: use per-request token if provided (from x-auth-data header)
    if (notionToken) {
      return {
        'Authorization': `Bearer ${notionToken}`,
        'Notion-Version': '2022-06-28'
      }
    }

    // Second: try OPENAPI_MCP_HEADERS (existing behavior)
    const headersJson = process.env.OPENAPI_MCP_HEADERS
    if (headersJson) {
      try {
        const headers = JSON.parse(headersJson)
        if (typeof headers !== 'object' || headers === null) {
          console.warn('OPENAPI_MCP_HEADERS environment variable must be a JSON object, got:', typeof headers)
        } else if (Object.keys(headers).length > 0) {
          // Only use OPENAPI_MCP_HEADERS if it contains actual headers
          return headers
        }
        // If OPENAPI_MCP_HEADERS is empty object, fall through to try NOTION_TOKEN
      } catch (error) {
        console.warn('Failed to parse OPENAPI_MCP_HEADERS environment variable:', error)
        // Fall through to try NOTION_TOKEN
      }
    }

    // Alternative: try NOTION_TOKEN
    const envNotionToken = process.env.NOTION_TOKEN
    if (envNotionToken) {
      return {
        'Authorization': `Bearer ${envNotionToken}`,
        'Notion-Version': '2022-06-28'
      }
    }

    return {}
  }

  private getContentType(headers: Headers): 'text' | 'image' | 'binary' {
    const contentType = headers.get('content-type')
    if (!contentType) return 'binary'

    if (contentType.includes('text') || contentType.includes('json')) {
      return 'text'
    } else if (contentType.includes('image')) {
      return 'image'
    }
    return 'binary'
  }

  private truncateToolName(name: string): string {
    if (name.length <= 64) {
      return name;
    }
    return name.slice(0, 64);
  }

  async connect(transport: Transport) {
    // The SDK will handle stdio communication
    await this.server.connect(transport)
  }

  getServer() {
    return this.server
  }
}
