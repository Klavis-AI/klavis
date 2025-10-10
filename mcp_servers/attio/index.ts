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
import dotenv from 'dotenv';

dotenv.config();

// Attio API configuration
const ATTIO_API_URL = 'https://api.attio.com/v2';

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    attioClient: AttioClient;
}>();

// Attio API Client
class AttioClient {
    private accessToken: string;
    private baseUrl: string;

    constructor(accessToken: string, baseUrl: string = ATTIO_API_URL) {
        this.accessToken = accessToken;
        this.baseUrl = baseUrl;
    }

    private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Attio API error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        return response.json();
    }

    async searchPeople(filters: any = {}, limit: number = 25): Promise<any> {
        if (Object.keys(filters).length === 0) {
            return this.makeRequest('/objects/people/records/query', {
                method: 'POST',
                body: JSON.stringify({
                    limit
                }),
            });
        }
        return this.makeRequest('/objects/people/records/query', {
            method: 'POST',
            body: JSON.stringify({
                filter: filters,
                limit
            }),
        });
    }

    async searchCompanies(filters: any = {}, limit: number = 25): Promise<any> {
        if (Object.keys(filters).length === 0) {
            return this.makeRequest('/objects/companies/records/query', {
                method: 'POST',
                body: JSON.stringify({
                    limit
                }),
            });
        }
        return this.makeRequest('/objects/companies/records/query', {
            method: 'POST',
            body: JSON.stringify({
                filter: filters,
                limit
            }),
        });
    }

    async searchDeals(filters: any = {}, limit: number = 25): Promise<any> {
        if (Object.keys(filters).length === 0) {
            return this.makeRequest('/objects/deals/records/query', {
                method: 'POST',
                body: JSON.stringify({
                    limit
                }),
            });
        }
        return this.makeRequest('/objects/deals/records/query', {
            method: 'POST',
            body: JSON.stringify({
                filter: filters,
                limit
            }),
        });
    }

    async searchNotes(query: string, limit: number = 50): Promise<any> {
        // First, get all notes (up to the limit)
        const allNotes = await this.makeRequest(`/notes?limit=${limit}`, {
            method: 'GET',
        });

        // If no query provided, return all notes
        if (!query || query.trim() === '') {
            return allNotes;
        }

        // Filter notes based on query matching title or content
        const queryLower = query.toLowerCase();
        const filteredNotes = allNotes.data.filter((note: any) => {
            const titleMatch = note.title?.toLowerCase().includes(queryLower);
            const contentPlaintextMatch = note.content_plaintext?.toLowerCase().includes(queryLower);
            const contentMarkdownMatch = note.content_markdown?.toLowerCase().includes(queryLower);

            return titleMatch || contentPlaintextMatch || contentMarkdownMatch;
        });

        return {
            ...allNotes,
            data: filteredNotes
        };
    }

    async createNote(data: {
        parent_object: string;
        parent_record_id: string;
        title: string;
        content: string;
        format?: 'plaintext' | 'markdown';
    }): Promise<any> {
        return this.makeRequest('/notes', {
            method: 'POST',
            body: JSON.stringify({
                data: {
                    parent_object: data.parent_object,
                    parent_record_id: data.parent_record_id,
                    title: data.title,
                    format: data.format || 'plaintext',
                    content: data.content
                }
            }),
        });
    }

    async createPerson(data: {
        name?: string;
        email_addresses?: string[];
        phone_numbers?: string[];
        job_title?: string;
        description?: string;
    }): Promise<any> {
        const recordData: any = {};

        if (data.name) { recordData.name = data.name; }
        if (data.email_addresses) { recordData.email_addresses = data.email_addresses; }
        if (data.phone_numbers) {
            for (const phoneNumber of data.phone_numbers) {
                recordData.phone_numbers.push({ original_phone_number: phoneNumber });
            }
        }
        if (data.job_title) { recordData.job_title = data.job_title; }
        if (data.description) { recordData.description = data.description; }

        return this.makeRequest('/objects/people/records', {
            method: 'POST',
            body: JSON.stringify({
                data: {
                    values: recordData
                }
            }),
        });
    }

    async createCompany(data: {
        name?: string;
        domains?: string[];
        description?: string;
    }): Promise<any> {
        const recordData: any = {};

        if (data.name) recordData.name = data.name;
        if (data.domains) recordData.domains = data.domains;
        if (data.description) recordData.description = data.description;

        return this.makeRequest('/objects/companies/records', {
            method: 'POST',
            body: JSON.stringify({
                data: {
                    values: recordData
                }
            }),
        });
    }

    async updatePerson(recordId: string, data: {
        name?: string;
        email_addresses?: string[];
        phone_numbers?: string[];
        job_title?: string;
        description?: string;
        company_id?: string;
    }): Promise<any> {
        const recordData: any = {};

        if (data.name) { recordData.name = data.name; }
        if (data.email_addresses) { recordData.email_addresses = data.email_addresses; }
        if (data.phone_numbers) {
            for (const phoneNumber of data.phone_numbers) {
                recordData.phone_numbers.push({ original_phone_number: phoneNumber });
            }
        }
        if (data.job_title) { recordData.job_title = data.job_title; }
        if (data.description) { recordData.description = data.description; }

        return this.makeRequest(`/objects/people/records/${recordId}`, {
            method: 'PATCH',
            body: JSON.stringify({
                data: {
                    values: recordData
                }
            }),
        });
    }

    async updateCompany(recordId: string, data: {
        name?: string;
        domains?: string[];
        description?: string;
    }): Promise<any> {
        const recordData: any = {};

        if (data.name) recordData.name = data.name;
        if (data.domains) recordData.domains = data.domains;
        if (data.description) recordData.description = data.description;

        return this.makeRequest(`/objects/companies/records/${recordId}`, {
            method: 'PATCH',
            body: JSON.stringify({
                data: {
                    values: recordData
                }
            }),
        });
    }

    async createTask(data: {
        content_plaintext: string;
        deadline_at?: string;
        assignee_emails: string[];
    }): Promise<any> {
        const taskData: any = {
            content: data.content_plaintext,
            format: 'plaintext',
            is_completed: false,
        };

        if (data.deadline_at) {
            taskData.deadline_at = data.deadline_at;
        }

        taskData.assignees = data.assignee_emails.map(email => ({
            workspace_member_email_address: email
        }));

        // Add linked_records for each assignee email to connect to people records
        taskData.linked_records = data.assignee_emails.map(email => ({
            target_object: "people",
            email_addresses: [
                {
                    email_address: email
                }
            ]
        }));

        console.log(JSON.stringify({
            data: taskData
        }));
        return this.makeRequest('/tasks', {
            method: 'POST',
            body: JSON.stringify({
                data: taskData
            }),
        });
    }
}

// Getter function for the client
function getAttioClient() {
    const store = asyncLocalStorage.getStore();
    if (!store) {
        throw new Error('Attio client not found in AsyncLocalStorage');
    }
    return store.attioClient;
}

// Tool definitions
const SEARCH_PEOPLE_TOOL: Tool = {
    name: 'attio_search_people',
    description: 'Search for people in your Attio workspace with advanced filtering options. If no parameter other than limit is provided, it will search all people.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query for people (searches across name, email, company, job title, description, etc.)',
            },
            email: {
                type: 'string',
                description: 'Filter by email address',
            },
            record_id: {
                type: 'string',
                description: 'Filter by specific person record ID',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 25, max: 50)',
                default: 25,
            },
        },
    },
    annotations: {
        category: 'ATTIO_PERSON',
        readOnlyHint: true
    },
};

const SEARCH_COMPANIES_TOOL: Tool = {
    name: 'attio_search_companies',
    description: 'Search for companies in your Attio workspace with filtering and sorting. If no parameter other than limit is provided, it will search all companies.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query for companies (searches across name, domain, description, employees names, employees descriptions, etc.)',
            },
            domain: {
                type: 'string',
                description: 'Filter by company domain',
            },
            record_id: {
                type: 'string',
                description: 'Filter by specific company record ID',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 25, max: 50)',
                default: 25,
            },
        },
    },
    annotations: {
        category: 'ATTIO_COMPANY',
        readOnlyHint: true
    },
};

const SEARCH_DEALS_TOOL: Tool = {
    name: 'attio_search_deals',
    description: 'Search for deals in your Attio workspace with stage and value filtering. If no parameter other than limit is provided, it will search all deals.',
    inputSchema: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
                description: 'Filter by deal name',
            },
            stage: {
                type: 'string',
                description: 'Filter by deal stage (one of "Lead", "In Progress", "Won 🎉", "Lost")',
            },
            minValue: {
                type: 'number',
                description: 'Minimum deal value',
            },
            maxValue: {
                type: 'number',
                description: 'Maximum deal value',
            },
            record_id: {
                type: 'string',
                description: 'Filter by specific deal record ID',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 25, max: 50)',
                default: 25,
            },
        },
    },
    annotations: {
        category: 'ATTIO_DEAL',
        readOnlyHint: true
    },
};

const SEARCH_NOTES_TOOL: Tool = {
    name: 'attio_search_notes',
    description: 'Search for notes across all objects in your Attio workspace by fetching all notes and filtering by content.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query for notes content (searches title, plaintext content, and markdown content). Leave empty to get all notes.',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of notes to fetch and search through (default: 50, max: 50)',
                default: 50,
            },
        },
    },
    annotations: {
        category: 'ATTIO_NOTE',
        readOnlyHint: true
    },
};

const CREATE_NOTE_TOOL: Tool = {
    name: 'attio_create_note',
    description: 'Create a new note for a given record in Attio.',
    inputSchema: {
        type: 'object',
        properties: {
            parent_object: {
                type: 'string',
                description: 'The object type to attach the note to (e.g., "people", "companies", "deals")',
                enum: ['people', 'companies', 'deals']
            },
            parent_record_id: {
                type: 'string',
                description: 'The ID of the record to attach the note to'
            },
            title: {
                type: 'string',
                description: 'Title of the note'
            },
            content: {
                type: 'string',
                description: 'Content of the note'
            },
            format: {
                type: 'string',
                description: 'Format of the note content',
                enum: ['plaintext', 'markdown'],
                default: 'plaintext'
            }
        },
        required: ['parent_object', 'parent_record_id', 'title', 'content'],
    },
    annotations: {
        category: 'ATTIO_NOTE'
    },
};

const CREATE_PERSON_TOOL: Tool = {
    name: 'attio_create_person',
    description: 'Create a new person record in your Attio workspace.',
    inputSchema: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
                description: 'Full name of the person',
            },
            email_addresses: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of email addresses for the person',
            },
            phone_numbers: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of phone numbers for the person',
            },
            job_title: {
                type: 'string',
                description: 'Job title of the person',
            },
            description: {
                type: 'string',
                description: 'Description or notes about the person',
            },
        },
    },
    annotations: {
        category: 'ATTIO_PERSON'
    },
};

const CREATE_COMPANY_TOOL: Tool = {
    name: 'attio_create_company',
    description: 'Create a new company record in your Attio workspace.',
    inputSchema: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
                description: 'Name of the company',
            },
            domains: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of domain names associated with the company',
            },
            description: {
                type: 'string',
                description: 'Description of the company',
            },
        },
    },
    annotations: {
        category: 'ATTIO_COMPANY'
    },
};

const UPDATE_PERSON_TOOL: Tool = {
    name: 'attio_update_person',
    description: 'Update an existing person record in your Attio workspace.',
    inputSchema: {
        type: 'object',
        properties: {
            record_id: {
                type: 'string',
                description: 'ID of the person record to update',
            },
            name: {
                type: 'string',
                description: 'Full name of the person',
            },
            email_addresses: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of email addresses for the person',
            },
            phone_numbers: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of phone numbers for the person',
            },
            job_title: {
                type: 'string',
                description: 'Job title of the person',
            },
            description: {
                type: 'string',
                description: 'Description or notes about the person',
            },
        },
        required: ['record_id'],
    },
    annotations: {
        category: 'ATTIO_PERSON'
    },
};

const UPDATE_COMPANY_TOOL: Tool = {
    name: 'attio_update_company',
    description: 'Update an existing company record in your Attio workspace.',
    inputSchema: {
        type: 'object',
        properties: {
            record_id: {
                type: 'string',
                description: 'ID of the company record to update',
            },
            name: {
                type: 'string',
                description: 'Name of the company',
            },
            domains: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of domain names associated with the company',
            },
            description: {
                type: 'string',
                description: 'Description of the company',
            },
        },
        required: ['record_id'],
    },
    annotations: {
        category: 'ATTIO_COMPANY'
    },
};

const CREATE_TASK_TOOL: Tool = {
    name: 'attio_create_task',
    description: 'Create a new task in your Attio workspace. Tasks must be assigned to workspace members and can have optional deadlines.',
    inputSchema: {
        type: 'object',
        properties: {
            content_plaintext: {
                type: 'string',
                description: 'The plaintext content of the task (e.g., "Follow up on current software solutions")',
            },
            deadline_at: {
                type: 'string',
                description: 'Optional deadline for the task as an ISO 8601 timestamp (e.g., "2023-01-01T15:00:00.000000000Z")',
            },
            assignee_emails: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of workspace member email addresses to assign the task to (e.g., ["alice@attio.com", "bob@attio.com"])',
            },
        },
        required: ['content_plaintext', 'assignee_emails'],
    },
    annotations: {
        category: 'ATTIO_TASK'
    },
};

// Utility functions
function safeLog(level: 'error' | 'debug' | 'info' | 'notice' | 'warning' | 'critical' | 'alert' | 'emergency', data: any): void {
    try {
        const logData = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
        console.log(`[${level.toUpperCase()}] ${logData}`);
    } catch (error) {
        console.log(`[${level.toUpperCase()}] [LOG_ERROR] Could not serialize log data`);
    }
}

function extractAccessToken(req: Request): string {
    let authData = process.env.AUTH_DATA;
    
    if (!authData && req.headers['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error parsing x-auth-data JSON:', error);
        }
    }

    if (!authData) {
        console.error('Error: Attio access token is missing. Provide it via ACCESS_TOKEN env var or x-auth-data header with access_token field.');
        return '';
    }

    const authDataJson = JSON.parse(authData);
    return authDataJson.access_token ?? '';
}

// Main server function
const getAttioMcpServer = () => {
    const server = new Server(
        {
            name: 'attio-mcp-server',
            version: '1.0.0',
        },
        {
            capabilities: {
                tools: {},
            },
        }
    );

    server.setRequestHandler(ListToolsRequestSchema, async () => {
        return {
            tools: [
                SEARCH_PEOPLE_TOOL,
                SEARCH_COMPANIES_TOOL,
                SEARCH_DEALS_TOOL,
                SEARCH_NOTES_TOOL,
                CREATE_NOTE_TOOL,
                CREATE_PERSON_TOOL,
                CREATE_COMPANY_TOOL,
                UPDATE_PERSON_TOOL,
                UPDATE_COMPANY_TOOL,
                CREATE_TASK_TOOL,
            ],
        };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case 'attio_search_people': {
                    const client = getAttioClient();
                    const filters: any = {};

                    if (args?.record_id) {
                        filters.record_id = { $eq: args.record_id };
                    } else {
                        if (args?.query) {
                            filters.$or = [
                                { name: { $contains: args.query } },
                                { email_addresses: { $contains: args.query } },
                                { description: { $contains: args.query } },
                                { job_title: { $contains: args.query } },
                                {
                                    path: [
                                        ["people", "company"],
                                        ["companies", "name"]
                                    ],
                                    constraints: {
                                        $contains: args.query
                                    }
                                },
                                {
                                    path: [
                                        ["people", "company"],
                                        ["companies", "description"]
                                    ],
                                    constraints: {
                                        $contains: args.query
                                    }
                                },
                                { primary_location: { locality: { $contains: args.query } } },
                            ];
                        }
                        if (args?.email) {
                            filters.email_addresses = args.email;
                        }
                    }

                    const result = await client.searchPeople(filters, (args?.limit as number) || 25);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_search_companies': {
                    const client = getAttioClient();
                    const filters: any = {};

                    if (args?.record_id) {
                        filters.record_id = { $eq: args.record_id };
                    } else {
                        if (args?.query) {
                            filters.$or = [
                                { name: { $contains: args.query } },
                                { domains: { domain: { $contains: args.query } } },
                                { description: { $contains: args.query } },
                                { primary_location: { locality: { $contains: args.query } } },
                                {
                                    path: [
                                        ["companies", "team"],
                                        ["people", "name"]
                                    ],
                                    constraints: {
                                        $contains: args.query
                                    }
                                },
                                {
                                    path: [
                                        ["companies", "team"],
                                        ["people", "description"]
                                    ],
                                    constraints: {
                                        $contains: args.query
                                    }
                                },
                            ];
                        }
                        if (args?.domain) {
                            filters.domains = { domain: args.domain };
                        }
                    }

                    const result = await client.searchCompanies(filters, (args?.limit as number) || 25);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_search_deals': {
                    const client = getAttioClient();
                    const filters: any = {};

                    if (args?.record_id) {
                        filters.record_id = { $eq: args.record_id };
                    } else {
                        if (args?.name) {
                            filters.name = { $contains: args.name };
                        }
                        if (args?.stage) {
                            filters.stage = args.stage;
                        }
                        if (args?.minValue !== undefined || args?.maxValue !== undefined) {
                            filters.value = {};
                            if (args?.minValue !== undefined) {
                                filters.value.$gte = args.minValue;
                            }
                            if (args?.maxValue !== undefined) {
                                filters.value.$lte = args.maxValue;
                            }
                        }
                    }

                    const result = await client.searchDeals(filters, (args?.limit as number) || 25);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_search_notes': {
                    const client = getAttioClient();
                    const result = await client.searchNotes((args as any)?.query || '', (args?.limit as number) || 50);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_create_note': {
                    const client = getAttioClient();

                    const result = await client.createNote({
                        parent_object: (args as any)?.parent_object,
                        parent_record_id: (args as any)?.parent_record_id,
                        title: (args as any)?.title,
                        content: (args as any)?.content,
                        format: (args as any)?.format || 'plaintext'
                    });

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_create_person': {
                    const client = getAttioClient();

                    const result = await client.createPerson({
                        name: (args as any)?.name,
                        email_addresses: (args as any)?.email_addresses,
                        phone_numbers: (args as any)?.phone_numbers,
                        job_title: (args as any)?.job_title,
                        description: (args as any)?.description,
                    });

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_create_company': {
                    const client = getAttioClient();

                    const result = await client.createCompany({
                        name: (args as any)?.name,
                        domains: (args as any)?.domains,
                        description: (args as any)?.description,
                    });

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_update_person': {
                    const client = getAttioClient();

                    const result = await client.updatePerson((args as any)?.record_id, {
                        name: (args as any)?.name,
                        email_addresses: (args as any)?.email_addresses,
                        phone_numbers: (args as any)?.phone_numbers,
                        job_title: (args as any)?.job_title,
                        description: (args as any)?.description,
                    });

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_update_company': {
                    const client = getAttioClient();

                    const result = await client.updateCompany((args as any)?.record_id, {
                        name: (args as any)?.name,
                        domains: (args as any)?.domains,
                        description: (args as any)?.description,
                    });

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_create_task': {
                    const client = getAttioClient();

                    const result = await client.createTask({
                        content_plaintext: (args as any)?.content_plaintext,
                        deadline_at: (args as any)?.deadline_at,
                        assignee_emails: (args as any)?.assignee_emails,
                    });

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error: any) {
            safeLog('error', `Tool ${name} failed: ${error.message}`);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Error: ${error.message}`,
                    },
                ],
                isError: true,
            };
        }
    });

    return server;
};

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    const accessToken = extractAccessToken(req);
    const attioClient = new AttioClient(accessToken);

    const server = getAttioMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ attioClient }, async () => {
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

    const server = getAttioMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (transport) {
        const accessToken = extractAccessToken(req);
        const attioClient = new AttioClient(accessToken);

        asyncLocalStorage.run({ attioClient }, async () => {
            await transport.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
});

app.listen(5000, () => {
    console.log('server running on port 5000');
});