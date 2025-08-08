import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';
import { AsyncLocalStorage } from 'async_hooks';
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import fetch from 'node-fetch';

dotenv.config();

type RequestContext = {
  accessToken?: string;
};

const asyncLocalStorage = new AsyncLocalStorage<RequestContext>();

async function getAccessToken(): Promise<string> {
  const store = asyncLocalStorage.getStore();
  const accessToken = (store?.accessToken || '').trim();
  if (!accessToken) {
    throw new Error('Missing OAuth access token. Pass a valid token in the x-auth-token header.');
  }
  return accessToken;
}



const CreateMeetingSpaceSchema = z.object({});

const MeetingSpaceIdSchema = z.object({
  space_id: z.string().min(1).describe('Meeting space ID (spaces/{space-id})'),
});



const ListConferenceRecordsSchema = z.object({
  page_size: z.number().int().positive().max(100).optional().default(10).describe('Maximum number of records to return'),
  page_token: z.string().optional().describe('Token for pagination'),
  filter: z.string().optional().describe('Filter expression'),
});

const ConferenceRecordIdSchema = z.object({
  conference_record_id: z.string().min(1).describe('Conference record ID (conferenceRecords/{record-id})'),
});

const ListParticipantsSchema = z.object({
  conference_record_id: z.string().min(1).describe('Conference record ID (conferenceRecords/{record-id})'),
  page_size: z.number().int().positive().max(100).optional().default(10).describe('Maximum number of participants to return'),
  page_token: z.string().optional().describe('Token for pagination'),
  filter: z.string().optional().describe('Filter expression'),
});



interface MeetingSpace {
  name: string;
  meetingUri: string;
  meetingCode?: string;
  config?: {
    accessType?: string;
    entryPointAccess?: string;
  };
}

interface ConferenceRecord {
  name: string;
  startTime?: string;
  endTime?: string;
  expireTime?: string;
  space?: string;
}

interface Participant {
  name: string;
  earliestStartTime?: string;
  latestEndTime?: string;
}

interface ApiResponse<T> {
  [key: string]: T | string | undefined;
}



const tools: Tool[] = [
  {
    name: 'create_space',
    description: 'Create a new Google Meet space',
    inputSchema: zodToJsonSchema(CreateMeetingSpaceSchema) as Tool['inputSchema'],
  },
  {
    name: 'get_space',
    description: 'Get details of a Google Meet space',
    inputSchema: zodToJsonSchema(MeetingSpaceIdSchema) as Tool['inputSchema'],
  },
  {
    name: 'list_conference_records',
    description: 'List conference records for completed meetings',
    inputSchema: zodToJsonSchema(ListConferenceRecordsSchema) as Tool['inputSchema'],
  },
  {
    name: 'get_conference_record',
    description: 'Get details of a specific conference record',
    inputSchema: zodToJsonSchema(ConferenceRecordIdSchema) as Tool['inputSchema'],
  },
  {
    name: 'list_participants',
    description: 'List participants from a conference record',
    inputSchema: zodToJsonSchema(ListParticipantsSchema) as Tool['inputSchema'],
  },
];

async function createMeetingSpace(args: z.infer<typeof CreateMeetingSpaceSchema>) {
  const accessToken = await getAccessToken();
  
  const response = await fetch('https://meet.googleapis.com/v2/spaces', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create meeting space: ${response.status} ${error}`);
  }

  const space = await response.json() as MeetingSpace;
  return {
    space_id: space.name,
    meet_link: space.meetingUri,
    space,
  };
}



async function getMeetingSpace(args: z.infer<typeof MeetingSpaceIdSchema>) {
  const accessToken = await getAccessToken();
  
  const response = await fetch(`https://meet.googleapis.com/v2/${args.space_id}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get meeting space: ${response.status} ${error}`);
  }

  const space = await response.json() as MeetingSpace;
  return {
    space_id: space.name,
    meet_link: space.meetingUri,
    space,
  };
}



async function listConferenceRecords(args: z.infer<typeof ListConferenceRecordsSchema>) {
  const accessToken = await getAccessToken();
  
  const params = new URLSearchParams();
  params.append('pageSize', args.page_size?.toString() || '10');
  if (args.page_token) params.append('pageToken', args.page_token);
  if (args.filter) params.append('filter', args.filter);

  const response = await fetch(`https://meet.googleapis.com/v2/conferenceRecords?${params.toString()}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to list conference records: ${response.status} ${error}`);
  }

  const data = await response.json() as ApiResponse<ConferenceRecord[]>;
  return {
    conference_records: data.conferenceRecords || [],
    next_page_token: data.nextPageToken as string | undefined,
  };
}

async function getConferenceRecord(args: z.infer<typeof ConferenceRecordIdSchema>) {
  const accessToken = await getAccessToken();
  
  const response = await fetch(`https://meet.googleapis.com/v2/${args.conference_record_id}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get conference record: ${response.status} ${error}`);
  }

  const record = await response.json() as ConferenceRecord;
  return {
    conference_record_id: record.name,
    record,
  };
}

async function listParticipants(args: z.infer<typeof ListParticipantsSchema>) {
  const accessToken = await getAccessToken();
  
  const params = new URLSearchParams();
  params.append('pageSize', args.page_size?.toString() || '10');
  if (args.page_token) params.append('pageToken', args.page_token);
  if (args.filter) params.append('filter', args.filter);

  const response = await fetch(`https://meet.googleapis.com/v2/${args.conference_record_id}/participants?${params.toString()}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to list participants: ${response.status} ${error}`);
  }

  const data = await response.json() as ApiResponse<Participant[]>;
  return {
    participants: data.participants || [],
    next_page_token: data.nextPageToken as string | undefined,
    participant_count: (data.participants || []).length,
  };
}



const getGoogleMeetMcpServer = () => {
  const server = new Server(
    { name: 'google-meet-mcp-server', version: '1.0.0' },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const name = request.params.name;
    const args = (request.params.arguments || {}) as Record<string, unknown>;

    try {
      switch (name) {
        case 'create_space': {
          const v = CreateMeetingSpaceSchema.parse(args);
          const res = await createMeetingSpace(v);
          return { content: [{ type: 'text', text: JSON.stringify(res) }] } as const;
        }
        case 'get_space': {
          const v = MeetingSpaceIdSchema.parse(args);
          const res = await getMeetingSpace(v);
          return { content: [{ type: 'text', text: JSON.stringify(res) }] } as const;
        }
        
        case 'list_conference_records': {
          const v = ListConferenceRecordsSchema.parse(args);
          const res = await listConferenceRecords(v);
          return { content: [{ type: 'text', text: JSON.stringify(res) }] } as const;
        }
        case 'get_conference_record': {
          const v = ConferenceRecordIdSchema.parse(args);
          const res = await getConferenceRecord(v);
          return { content: [{ type: 'text', text: JSON.stringify(res) }] } as const;
        }
        case 'list_participants': {
          const v = ListParticipantsSchema.parse(args);
          const res = await listParticipants(v);
          return { content: [{ type: 'text', text: JSON.stringify(res) }] } as const;
        }
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: 'text', text: `Error: ${errorMessage}` }],
        isError: true,
      } as const;
    }
  });

  return server;
};

const app = express();
app.use(express.json());

app.post('/mcp', async (req: Request, res: Response) => {
  const token = req.headers['x-auth-token'] as string | undefined;
  const server = getGoogleMeetMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    await server.connect(transport);
    asyncLocalStorage.run({ accessToken: token }, async () => {
      await transport.handleRequest(req, res, req.body);
    });
    res.on('close', () => {
      transport.close();
      server.close();
    });
  } catch (error) {
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: { code: -32603, message: 'Internal server error' },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (_req: Request, res: Response) => {
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: '2.0',
    error: { code: -32000, message: 'Method not allowed.' },
    id: null,
  }));
});

app.delete('/mcp', async (_req: Request, res: Response) => {
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: '2.0',
    error: { code: -32000, message: 'Method not allowed.' },
    id: null,
  }));
});


const transports = new Map<string, SSEServerTransport>();

app.get('/sse', async (_req: Request, res: Response) => {
  const transport = new SSEServerTransport('/messages', res);
  res.on('close', async () => {
    transports.delete(transport.sessionId);
  });
  transports.set(transport.sessionId, transport);
  const server = getGoogleMeetMcpServer();
  await server.connect(transport);
});

app.post('/messages', async (req: Request, res: Response) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports.get(sessionId);
  if (!transport) {
    res.status(404).send({ error: 'Transport not found' });
    return;
  }
  const token = req.headers['x-auth-token'] as string | undefined;
  asyncLocalStorage.run({ accessToken: token }, async () => {
    await transport.handlePostMessage(req, res);
  });
});

const PORT = Number(process.env.SERVER_PORT || '5000') || 5000;
app.listen(PORT, () => {
  console.log(`Google Meet MCP server running on port ${PORT}`);
});


