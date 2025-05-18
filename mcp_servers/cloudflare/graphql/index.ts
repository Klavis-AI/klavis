import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
    Tool,
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { AsyncLocalStorage } from 'async_hooks';
import * as LZString from 'lz-string';
import { z } from 'zod';
import dotenv from 'dotenv';

dotenv.config();

// GraphQL API endpoint
const CLOUDFLARE_GRAPHQL_ENDPOINT = 'https://api.cloudflare.com/client/v4/graphql';

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    apiToken: string;
    email?: string;
}>();

// Define the context accessor function
function getRequestContext() {
    const store = asyncLocalStorage.getStore();
    if (!store) {
        throw new Error('Request context not found in AsyncLocalStorage');
    }
    return store;
}

// Type definitions for GraphQL schema responses
interface GraphQLTypeRef {
    kind: string;
    name: string | null;
    ofType?: GraphQLTypeRef | null;
}

interface GraphQLField {
    name: string;
    description: string | null;
    args: Array<{
        name: string;
        description: string | null;
        type: GraphQLTypeRef;
    }>;
    type: GraphQLTypeRef;
}

interface GraphQLType {
    name: string;
    kind: string;
    description: string | null;
    fields?: GraphQLField[] | null;
    inputFields?: Array<{
        name: string;
        description: string | null;
        type: GraphQLTypeRef;
    }> | null;
    interfaces?: Array<{ name: string }> | null;
    enumValues?: Array<{
        name: string;
        description: string | null;
    }> | null;
    possibleTypes?: Array<{ name: string }> | null;
}

interface SchemaOverviewResponse {
    data: {
        __schema: {
            queryType: { name: string } | null;
            mutationType: { name: string } | null;
            subscriptionType: { name: string } | null;
            types: Array<{
                name: string;
                kind: string;
                description: string | null;
            }>;
        };
    };
}

interface TypeDetailsResponse {
    data: {
        __type: GraphQLType;
    };
}

// Define the structure of a single error
const graphQLErrorSchema = z.object({
    message: z.string(),
    path: z.array(z.union([z.string(), z.number()])),
    extensions: z.object({
        code: z.string(),
        timestamp: z.string(),
        ray_id: z.string(),
    }),
});

// Define the overall GraphQL response schema
const graphQLResponseSchema = z.object({
    data: z.union([z.record(z.unknown()), z.null()]),
    errors: z.union([z.array(graphQLErrorSchema), z.null()]),
});

// Tool definitions
const SCHEMA_SEARCH_TOOL: Tool = {
    name: 'graphql_schema_search',
    description: 'Search the Cloudflare GraphQL API schema for types, fields, and enum values matching a keyword.',
    inputSchema: {
        type: 'object',
        properties: {
            keyword: {
                type: 'string',
                description: 'Keyword to search for in the schema',
            },
            accountId: {
                type: 'string',
                description: 'Optional Cloudflare account ID (defaults to active account)',
            },
            maxDetails: {
                type: 'number',
                description: 'Maximum number of type details to fetch (default: 10)',
            },
            onlyObjectTypes: {
                type: 'boolean',
                description: 'Only search in object types, not scalars/enums (default: true)',
            },
        },
        required: ['keyword'],
    },
};

const SCHEMA_OVERVIEW_TOOL: Tool = {
    name: 'graphql_schema_overview',
    description: 'Fetch the high-level overview of the Cloudflare GraphQL API schema.',
    inputSchema: {
        type: 'object',
        properties: {},
    },
};

const TYPE_DETAILS_TOOL: Tool = {
    name: 'graphql_type_details',
    description: 'Fetch detailed information about a specific GraphQL type.',
    inputSchema: {
        type: 'object',
        properties: {
            typeName: {
                type: 'string',
                description: 'The name of the type to fetch details for',
            },
        },
        required: ['typeName'],
    },
};

const COMPLETE_SCHEMA_TOOL: Tool = {
    name: 'graphql_complete_schema',
    description: 'Fetch the complete Cloudflare GraphQL API schema (combines overview and important type details).',
    inputSchema: {
        type: 'object',
        properties: {
            includeQueries: {
                type: 'boolean',
                description: 'Include details of query root type (default: true)',
            },
            includeMutations: {
                type: 'boolean',
                description: 'Include details of mutation root type (default: true)',
            },
            maxTypeDetails: {
                type: 'number',
                description: 'Maximum number of type details to fetch (default: 20)',
            },
        },
    },
};

const QUERY_TOOL: Tool = {
    name: 'graphql_query',
    description: 'Execute a GraphQL query against the Cloudflare API.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'GraphQL query to execute',
            },
            variables: {
                type: 'object',
                description: 'Variables for the GraphQL query',
            },
            accountId: {
                type: 'string',
                description: 'Optional Cloudflare account ID (defaults to active account)',
            },
        },
        required: ['query'],
    },
};

const API_EXPLORER_TOOL: Tool = {
    name: 'graphql_api_explorer',
    description: 'Generate a Cloudflare GraphQL API Explorer link with pre-populated query and variables.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'GraphQL query to pre-populate in the explorer',
            },
            variables: {
                type: 'object',
                description: 'Variables for the GraphQL query',
            },
        },
        required: ['query'],
    },
};

// Helper functions for GraphQL operations
async function executeGraphQLRequest<T>(query: string, apiToken: string): Promise<T> {
    const response = await fetch(CLOUDFLARE_GRAPHQL_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiToken}`,
        },
        body: JSON.stringify({ query }),
    });

    if (!response.ok) {
        throw new Error(`Failed to execute GraphQL request: ${response.statusText}`);
    }

    const data = graphQLResponseSchema.parse(await response.json());

    if (data.errors && data.errors.length > 0) {
        throw new Error(`GraphQL error: ${data.errors[0].message}`);
    }

    return data as T;
}

async function executeGraphQLQuery(query: string, variables: any, apiToken: string) {
    const response = await fetch(CLOUDFLARE_GRAPHQL_ENDPOINT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiToken}`,
        },
        body: JSON.stringify({
            query,
            variables,
        }),
    });

    if (!response.ok) {
        throw new Error(`Failed to execute GraphQL query: ${response.statusText}`);
    }

    const data = graphQLResponseSchema.parse(await response.json());

    if (data.errors && data.errors.length > 0) {
        throw new Error(`GraphQL error: ${data.errors[0].message}`);
    }

    return data;
}

async function fetchSchemaOverview(apiToken: string): Promise<SchemaOverviewResponse> {
    const overviewQuery = `
        query SchemaOverview {
            __schema {
                queryType { name }
                mutationType { name }
                subscriptionType { name }
                types {
                    name
                    kind
                    description
                }
            }
        }
    `;

    const response = await executeGraphQLRequest<SchemaOverviewResponse>(overviewQuery, apiToken);
    return response;
}

async function fetchTypeDetails(typeName: string, apiToken: string): Promise<TypeDetailsResponse> {
    const typeDetailsQuery = `
        query TypeDetails {
            __type(name: "${typeName}") {
                name
                kind
                description
                fields(includeDeprecated: false) {
                    name
                    description
                    args {
                        name
                        description
                        type {
                            kind
                            name
                            ofType {
                                kind
                                name
                            }
                        }
                    }
                    type {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                            }
                        }
                    }
                }
                inputFields {
                    name
                    description
                    type {
                        kind
                        name
                        ofType {
                            kind
                            name
                        }
                    }
                }
                interfaces {
                    name
                }
                enumValues(includeDeprecated: false) {
                    name
                    description
                }
                possibleTypes {
                    name
                }
            }
        }
    `;

    const response = await executeGraphQLRequest<TypeDetailsResponse>(typeDetailsQuery, apiToken);
    return response;
}

async function searchGraphQLSchema(
    schema: SchemaOverviewResponse,
    keyword: string,
    accountId: string,
    apiToken: string,
    maxDetailsToFetch: number = 10,
    onlyObjectTypes: boolean = true
) {
    const searchKeyword = keyword.toLowerCase();
    let matchedTypes = schema.data.__schema.types
        .filter(type => {
            if (onlyObjectTypes && type.kind !== 'OBJECT') return false;
            
            // Skip internal types
            if (type.name && type.name.startsWith('__')) return false;
            
            return (
                (type.name && type.name.toLowerCase().includes(searchKeyword)) ||
                (type.description && type.description.toLowerCase().includes(searchKeyword))
            );
        })
        .map(type => ({
            name: type.name,
            kind: type.kind,
            description: type.description,
            source: 'type',
            matchedOn: type.name && type.name.toLowerCase().includes(searchKeyword) ? 'name' : 'description',
        }));

    // Limit the number of types to fetch details for to avoid too many requests
    const typesToFetch = matchedTypes.slice(0, maxDetailsToFetch);
    
    // Fetch details for each matched type to find matching fields
    const typeDetailsPromises = typesToFetch.map(async (typeInfo) => {
        if (!typeInfo.name) return null;
        
        const typeDetails = await fetchTypeDetails(typeInfo.name, apiToken);
        return typeDetails.data.__type;
    });
    
    const typeDetailsResults = await Promise.all(typeDetailsPromises);
    const validTypeDetails = typeDetailsResults.filter(Boolean);
    
    // Search in fields
    for (const typeDetail of validTypeDetails) {
        if (!typeDetail || !typeDetail.name) continue;
        
        // Search in fields
        if (typeDetail.fields) {
            for (const field of typeDetail.fields) {
                if (
                    (field.name && field.name.toLowerCase().includes(searchKeyword)) ||
                    (field.description && field.description.toLowerCase().includes(searchKeyword))
                ) {
                    matchedTypes.push({
                        name: `${typeDetail.name}.${field.name}`,
                        kind: 'FIELD',
                        description: field.description,
                        source: 'field',
                        matchedOn: field.name.toLowerCase().includes(searchKeyword) ? 'name' : 'description',
                    });
                }
                
                // Search in field arguments
                for (const arg of field.args) {
                    if (
                        (arg.name && arg.name.toLowerCase().includes(searchKeyword)) ||
                        (arg.description && arg.description.toLowerCase().includes(searchKeyword))
                    ) {
                        matchedTypes.push({
                            name: `${typeDetail.name}.${field.name}(${arg.name})`,
                            kind: 'ARGUMENT',
                            description: arg.description,
                            source: 'argument',
                            matchedOn: arg.name.toLowerCase().includes(searchKeyword) ? 'name' : 'description',
                        });
                    }
                }
            }
        }
        
        // Search in enum values
        if (typeDetail.enumValues) {
            for (const enumValue of typeDetail.enumValues) {
                if (
                    (enumValue.name && enumValue.name.toLowerCase().includes(searchKeyword)) ||
                    (enumValue.description && enumValue.description.toLowerCase().includes(searchKeyword))
                ) {
                    matchedTypes.push({
                        name: `${typeDetail.name}.${enumValue.name}`,
                        kind: 'ENUM_VALUE',
                        description: enumValue.description,
                        source: 'enumValue',
                        matchedOn: enumValue.name.toLowerCase().includes(searchKeyword) ? 'name' : 'description',
                    });
                }
            }
        }
    }
    
    return matchedTypes;
}

function generateApiExplorerLink(query: string, variables?: Record<string, any>): string {
    // Compress the query to be used in the URL
    const compressedQuery = LZString.compressToEncodedURIComponent(query);
    
    // Prepare variables string if present
    let variablesString = '';
    if (variables && Object.keys(variables).length > 0) {
        variablesString = LZString.compressToEncodedURIComponent(JSON.stringify(variables));
    }
    
    // Construct the API Explorer URL
    let url = `https://graphql.cloudflare.com/explorer?query=${compressedQuery}`;
    if (variablesString) {
        url += `&variables=${variablesString}`;
    }
    
    return url;
}

// Type guards for arguments validation
function isSchemaSearchOptions(args: unknown): args is { 
    keyword: string; 
    accountId?: string; 
    maxDetails?: number;
    onlyObjectTypes?: boolean;
} {
    return (
        typeof args === 'object' &&
        args !== null &&
        'keyword' in args &&
        typeof (args as { keyword: unknown }).keyword === 'string'
    );
}

function isTypeDetailsOptions(args: unknown): args is { typeName: string } {
    return (
        typeof args === 'object' &&
        args !== null &&
        'typeName' in args &&
        typeof (args as { typeName: unknown }).typeName === 'string'
    );
}

function isCompleteSchemaOptions(args: unknown): args is {
    includeQueries?: boolean;
    includeMutations?: boolean;
    maxTypeDetails?: number;
} {
    return (
        typeof args === 'object' &&
        args !== null
    );
}

function isQueryOptions(args: unknown): args is {
    query: string;
    variables?: Record<string, any>;
    accountId?: string;
} {
    return (
        typeof args === 'object' &&
        args !== null &&
        'query' in args &&
        typeof (args as { query: unknown }).query === 'string'
    );
}

function isApiExplorerOptions(args: unknown): args is {
    query: string;
    variables?: Record<string, any>;
} {
    return (
        typeof args === 'object' &&
        args !== null &&
        'query' in args &&
        typeof (args as { query: unknown }).query === 'string'
    );
}

// Utility function to trim trailing whitespace from text responses
function trimResponseText(text: string): string {
    return text.trim();
}

// Server implementation function
const getGraphQLMcpServer = () => {
    const server = new Server(
        {
            name: 'graphql-mcp',
            version: process.env.MCP_SERVER_VERSION || '0.0.2',
        },
        {
            capabilities: {
                tools: {},
                logging: {},
            },
        }
    );

    // Tool handlers
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [
            SCHEMA_SEARCH_TOOL,
            SCHEMA_OVERVIEW_TOOL,
            TYPE_DETAILS_TOOL,
            COMPLETE_SCHEMA_TOOL,
            QUERY_TOOL,
            API_EXPLORER_TOOL,
        ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const startTime = Date.now();
        try {
            const { name, arguments: args } = request.params;
            const context = getRequestContext();
            const apiToken = context.apiToken;

            // Log incoming request with timestamp
            console.log(`[${new Date().toISOString()}] Received request for tool: ${name}`);

            if (!args) {
                throw new Error('No arguments provided');
            }

            switch (name) {
                case 'graphql_schema_search': {
                    if (!isSchemaSearchOptions(args)) {
                        throw new Error('Invalid arguments for graphql_schema_search');
                    }

                    const { keyword, accountId, maxDetails = 10, onlyObjectTypes = true } = args;
                    
                    try {
                        console.log(`Starting schema search for keyword: ${keyword}`);
                        
                        // First get schema overview
                        const schema = await fetchSchemaOverview(apiToken);
                        
                        // Then search in the schema
                        const results = await searchGraphQLSchema(
                            schema, 
                            keyword, 
                            accountId || 'current', 
                            apiToken,
                            maxDetails,
                            onlyObjectTypes
                        );
                        
                        console.log(`Schema search completed in ${Date.now() - startTime}ms`);
                        
                        const formattedResults = results.map(result => 
                            `${result.kind}: ${result.name}
Description: ${result.description || 'No description'}
Matched on: ${result.matchedOn}`
                        ).join('\n\n');
                        
                        return {
                            content: [
                                { 
                                    type: 'text', 
                                    text: trimResponseText(
                                        `Found ${results.length} matches for "${keyword}":\n\n${formattedResults}`
                                    ) 
                                },
                            ],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage = error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }
                
                case 'graphql_schema_overview': {
                    try {
                        const schema = await fetchSchemaOverview(apiToken);
                        
                        const typesInfo = schema.data.__schema.types
                            .filter(type => !type.name?.startsWith('__')) // Filter out internal types
                            .map(type => `${type.kind}: ${type.name}${type.description ? `\nDescription: ${type.description}` : ''}`)
                            .join('\n\n');
                        
                        const overview = `Schema Overview:
Query Type: ${schema.data.__schema.queryType?.name || 'None'}
Mutation Type: ${schema.data.__schema.mutationType?.name || 'None'}
Subscription Type: ${schema.data.__schema.subscriptionType?.name || 'None'}

Types:
${typesInfo}`;
                        
                        return {
                            content: [{ type: 'text', text: trimResponseText(overview) }],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage = error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }
                
                case 'graphql_type_details': {
                    if (!isTypeDetailsOptions(args)) {
                        throw new Error('Invalid arguments for graphql_type_details');
                    }
                    
                    try {
                        const { typeName } = args;
                        const typeDetails = await fetchTypeDetails(typeName, apiToken);
                        
                        if (!typeDetails.data.__type) {
                            return {
                                content: [{ type: 'text', text: trimResponseText(`Type "${typeName}" not found in the schema.`) }],
                                isError: true,
                            };
                        }
                        
                        const type = typeDetails.data.__type;
                        
                        let detailsText = `Type: ${type.name} (${type.kind})
Description: ${type.description || 'No description'}\n`;
                        
                        if (type.fields && type.fields.length > 0) {
                            detailsText += '\nFields:\n';
                            detailsText += type.fields.map(field => {
                                let fieldText = `  ${field.name}: ${formatGraphQLType(field.type)}`;
                                if (field.description) fieldText += `\n    Description: ${field.description}`;
                                
                                if (field.args && field.args.length > 0) {
                                    fieldText += '\n    Arguments:';
                                    fieldText += field.args.map(arg => 
                                        `\n      ${arg.name}: ${formatGraphQLType(arg.type)}${arg.description ? ` - ${arg.description}` : ''}`
                                    ).join('');
                                }
                                
                                return fieldText;
                            }).join('\n\n');
                        }
                        
                        if (type.inputFields && type.inputFields.length > 0) {
                            detailsText += '\nInput Fields:\n';
                            detailsText += type.inputFields.map(field => 
                                `  ${field.name}: ${formatGraphQLType(field.type)}${field.description ? `\n    Description: ${field.description}` : ''}`
                            ).join('\n\n');
                        }
                        
                        if (type.enumValues && type.enumValues.length > 0) {
                            detailsText += '\nEnum Values:\n';
                            detailsText += type.enumValues.map(enumValue => 
                                `  ${enumValue.name}${enumValue.description ? `\n    Description: ${enumValue.description}` : ''}`
                            ).join('\n\n');
                        }
                        
                        if (type.interfaces && type.interfaces.length > 0) {
                            detailsText += '\nInterfaces:\n';
                            detailsText += type.interfaces.map(iface => `  ${iface.name}`).join('\n');
                        }
                        
                        if (type.possibleTypes && type.possibleTypes.length > 0) {
                            detailsText += '\nPossible Types:\n';
                            detailsText += type.possibleTypes.map(ptype => `  ${ptype.name}`).join('\n');
                        }
                        
                        return {
                            content: [{ type: 'text', text: trimResponseText(detailsText) }],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage = error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }
                
                case 'graphql_complete_schema': {
                    try {
                        const options = isCompleteSchemaOptions(args) ? args : {};
                        const { 
                            includeQueries = true, 
                            includeMutations = true,
                            maxTypeDetails = 20 
                        } = options;
                        
                        // Get schema overview
                        const schema = await fetchSchemaOverview(apiToken);
                        
                        let result = `Cloudflare GraphQL API Complete Schema:\n\n`;
                        
                        // Add root types information
                        result += `Root Types:\n`;
                        result += `Query: ${schema.data.__schema.queryType?.name || 'None'}\n`;
                        result += `Mutation: ${schema.data.__schema.mutationType?.name || 'None'}\n`;
                        result += `Subscription: ${schema.data.__schema.subscriptionType?.name || 'None'}\n\n`;
                        
                        // Add query type details if requested
                        if (includeQueries && schema.data.__schema.queryType?.name) {
                            const queryTypeName = schema.data.__schema.queryType.name;
                            const queryTypeDetails = await fetchTypeDetails(queryTypeName, apiToken);
                            
                            result += `Query Type Details (${queryTypeName}):\n`;
                            if (queryTypeDetails.data.__type?.fields) {
                                result += queryTypeDetails.data.__type.fields.map(field => 
                                    `  ${field.name}: ${formatGraphQLType(field.type)}${field.description ? `\n    Description: ${field.description}` : ''}`
                                ).join('\n\n');
                            }
                            result += `\n\n`;
                        }
                        
                        // Add mutation type details if requested
                        if (includeMutations && schema.data.__schema.mutationType?.name) {
                            const mutationTypeName = schema.data.__schema.mutationType.name;
                            const mutationTypeDetails = await fetchTypeDetails(mutationTypeName, apiToken);
                            
                            result += `Mutation Type Details (${mutationTypeName}):\n`;
                            if (mutationTypeDetails.data.__type?.fields) {
                                result += mutationTypeDetails.data.__type.fields.map(field => 
                                    `  ${field.name}: ${formatGraphQLType(field.type)}${field.description ? `\n    Description: ${field.description}` : ''}`
                                ).join('\n\n');
                            }
                            result += `\n\n`;
                        }
                        
                        // Add common type information
                        result += `Object Types (${Math.min(maxTypeDetails, schema.data.__schema.types.length)} most important):\n`;
                        
                        const objectTypes = schema.data.__schema.types
                            .filter(type => 
                                type.kind === 'OBJECT' && 
                                !type.name?.startsWith('__') &&
                                type.name !== schema.data.__schema.queryType?.name &&
                                type.name !== schema.data.__schema.mutationType?.name
                            )
                            .slice(0, maxTypeDetails);
                        
                        for (const type of objectTypes) {
                            result += `\n${type.name} - ${type.description || 'No description'}\n`;
                        }
                        
                        return {
                            content: [{ type: 'text', text: trimResponseText(result) }],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage = error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }
                
                case 'graphql_query': {
                    if (!isQueryOptions(args)) {
                        throw new Error('Invalid arguments for graphql_query');
                    }
                    
                    try {
                        const { query, variables = {}, accountId } = args;
                        
                        console.log(`Executing GraphQL query: ${query.substring(0, 100)}${query.length > 100 ? '...' : ''}`);
                        
                        // Execute the query
                        const response = await executeGraphQLQuery(query, variables, apiToken);
                        
                        console.log(`Query completed in ${Date.now() - startTime}ms`);
                        
                        return {
                            content: [{ 
                                type: 'text', 
                                text: trimResponseText(JSON.stringify(response.data, null, 2)) 
                            }],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage = error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }
                
                case 'graphql_api_explorer': {
                    if (!isApiExplorerOptions(args)) {
                        throw new Error('Invalid arguments for graphql_api_explorer');
                    }
                    
                    try {
                        const { query, variables } = args;
                        const link = generateApiExplorerLink(query, variables);
                        
                        return {
                            content: [{ 
                                type: 'text', 
                                text: trimResponseText(`Cloudflare GraphQL API Explorer link:\n${link}`) 
                            }],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage = error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }
                
                default:
                    return {
                        content: [
                            { type: 'text', text: trimResponseText(`Unknown tool: ${name}`) },
                        ],
                        isError: true,
                    };
            }
        } catch (error) {
            // Log detailed error information
            console.error({
                message: `Request failed: ${error instanceof Error ? error.message : String(error)}`,
                tool: request.params.name,
                arguments: request.params.arguments,
                timestamp: new Date().toISOString(),
                duration: Date.now() - startTime,
            });
            
            return {
                content: [
                    {
                        type: 'text',
                        text: trimResponseText(
                            `Error: ${error instanceof Error ? error.message : String(error)}`
                        ),
                    },
                ],
                isError: true,
            };
        } finally {
            // Log request completion with performance metrics
            console.log(`Request completed in ${Date.now() - startTime}ms`);
        }
    });

    return server;
};

// Helper function to format GraphQL type for display
function formatGraphQLType(type: GraphQLTypeRef): string {
    if (!type) return 'Unknown';
    
    if (type.kind === 'NON_NULL') {
        return `${formatGraphQLType(type.ofType!)}!`;
    }
    
    if (type.kind === 'LIST') {
        return `[${formatGraphQLType(type.ofType!)}]`;
    }
    
    return type.name || 'Unknown';
}

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    // Get API token from header
    const apiToken = req.headers.authorization?.replace('Bearer ', '') || 
                     req.headers['x-auth-token'] as string;
    const email = req.headers['x-auth-email'] as string;

    if (!apiToken) {
        console.error('Error: API token is missing. Provide it via Authorization header or x-auth-token header.');
        res.status(401).json({
            jsonrpc: '2.0',
            error: {
                code: -32000,
                message: 'API token is required'
            },
            id: null
        });
        return;
    }

    const server = getGraphQLMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ apiToken, email }, async () => {
            await transport.handleRequest(req, res, req.body);
        });
        res.on('close', () => {
            console.log('Request closed');
            transport.close();
            server.close();
        });
    } catch (error) {
        console.error('Error handling MCP request:', error);
        if (!res.headersSent) {
            res.status(500).json({
                jsonrpc: '2.0',
                error: {
                    code: -32603,
                    message: 'Internal server error',
                },
                id: null,
            });
        }
    }
});

app.get('/mcp', async (req: Request, res: Response) => {
    console.log('Received GET MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
    console.log('Received DELETE MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
    const transport = new SSEServerTransport(`/messages`, res);

    // Set up cleanup when connection closes
    res.on('close', async () => {
        console.log(`SSE connection closed for transport: ${transport.sessionId}`);
        try {
            transports.delete(transport.sessionId);
        } finally {
        }
    });

    transports.set(transport.sessionId, transport);

    const server = getGraphQLMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (transport) {
        // Get API token from header
        const apiToken = req.headers.authorization?.replace('Bearer ', '') || 
                       req.headers['x-auth-token'] as string;
        const email = req.headers['x-auth-email'] as string;

        if (!apiToken) {
            console.error('Error: API token is missing. Provide it via Authorization header or x-auth-token header.');
            res.status(401).json({
                error: "API token is required"
            });
            return;
        }

        // Run handler within AsyncLocalStorage context
        asyncLocalStorage.run({ apiToken, email }, async () => {
            await transport.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
});

const PORT = process.env.PORT || 8787;
app.listen(PORT, () => {
    console.log(`GraphQL MCP server running on port ${PORT}`);
}); 