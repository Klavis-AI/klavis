import { anthropic } from '@ai-sdk/anthropic';
import { StreamTransport } from '@supabase/mcp-utils';
import {
  experimental_createMCPClient as createMCPClient,
  generateText,
  ToolSet,
  type ToolCallUnion,
} from 'ai';
import { setupServer } from 'msw/node';
import { beforeEach, describe, expect, test } from 'vitest';
import { createSupabaseMcpServer } from '../src/index.js';
import {
  ACCESS_TOKEN,
  API_URL,
  createOrganization,
  createProject,
  MCP_CLIENT_NAME,
  mockBranches,
  mockManagementApi,
  mockOrgs,
  mockProjects,
} from './mocks.js';

/**
 * Sets up an MCP client and server for testing.
 */
async function setup() {
  const clientTransport = new StreamTransport();
  const serverTransport = new StreamTransport();

  clientTransport.readable.pipeTo(serverTransport.writable);
  serverTransport.readable.pipeTo(clientTransport.writable);

  const server = createSupabaseMcpServer({
    platform: {
      apiUrl: API_URL,
      accessToken: ACCESS_TOKEN,
    },
  });

  await server.connect(serverTransport);

  const client = await createMCPClient({
    name: MCP_CLIENT_NAME,
    transport: clientTransport,
  });

  return { client, clientTransport, server, serverTransport };
}

beforeEach(async () => {
  mockOrgs.clear();
  mockProjects.clear();
  mockBranches.clear();

  const server = setupServer(...mockManagementApi);
  server.listen({ onUnhandledRequest: 'bypass' });
});

describe('llm tests', () => {
  test('identifies correct project before listing tables', async () => {
    const { client } = await setup();
    const model = anthropic('claude-3-7-sonnet-20250219');

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const todosProject = await createProject({
      name: 'todos-app',
      region: 'us-east-1',
      organization_id: org.id,
    });

    const inventoryProject = await createProject({
      name: 'inventory-app',
      region: 'us-east-1',
      organization_id: org.id,
    });

    await todosProject.db.sql`create table todos (id serial, name text)`;
    await inventoryProject.db
      .sql`create table inventory (id serial, name text)`;

    const toolCalls: ToolCallUnion<ToolSet>[] = [];

    const { text } = await generateText({
      model,
      tools: await client.tools(),
      messages: [
        {
          role: 'system',
          content:
            'You are a coding assistant. The current working directory is /home/user/projects/todos-app.',
        },
        {
          role: 'user',
          content: 'What tables do I have?',
        },
      ],
      maxSteps: 10,
      async onStepFinish({ toolCalls: tools }) {
        toolCalls.push(...tools);
      },
    });

    expect(toolCalls).toHaveLength(2);
    expect(toolCalls[0]).toEqual(
      expect.objectContaining({ toolName: 'supabase_list_projects' })
    );
    expect(toolCalls[1]).toEqual(
      expect.objectContaining({ toolName: 'supabase_list_tables' })
    );

    await expect(text).toMatchCriteria(
      'Describes a single table in the "todos-app" project called "todos"'
    );
  });
});
