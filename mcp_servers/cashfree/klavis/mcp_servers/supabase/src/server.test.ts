import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import {
  CallToolResultSchema,
  type CallToolRequest,
} from '@modelcontextprotocol/sdk/types.js';
import { StreamTransport } from '@supabase/mcp-utils';
import { setupServer } from 'msw/node';
import { beforeEach, describe, expect, test } from 'vitest';
import {
  ACCESS_TOKEN,
  API_URL,
  CLOSEST_REGION,
  createOrganization,
  createProject,
  MCP_CLIENT_NAME,
  MCP_CLIENT_VERSION,
  mockBranches,
  mockManagementApi,
  mockOrgs,
  mockProjects,
} from '../test/mocks.js';
import { BRANCH_COST_HOURLY, PROJECT_COST_MONTHLY } from './pricing.js';
import { createSupabaseMcpServer } from './server.js';

beforeEach(async () => {
  mockOrgs.clear();
  mockProjects.clear();
  mockBranches.clear();

  const server = setupServer(...mockManagementApi);
  server.listen({ onUnhandledRequest: 'error' });
});

type SetupOptions = {
  accessToken?: string;
  readOnly?: boolean;
};

/**
 * Sets up an MCP client and server for testing.
 */
async function setup(options: SetupOptions = {}) {
  const { accessToken = ACCESS_TOKEN, readOnly } = options;
  const clientTransport = new StreamTransport();
  const serverTransport = new StreamTransport();

  clientTransport.readable.pipeTo(serverTransport.writable);
  serverTransport.readable.pipeTo(clientTransport.writable);

  const client = new Client(
    {
      name: MCP_CLIENT_NAME,
      version: MCP_CLIENT_VERSION,
    },
    {
      capabilities: {},
    }
  );

  const server = createSupabaseMcpServer({
    platform: {
      apiUrl: API_URL,
      accessToken,
    },
    readOnly,
  });

  await server.connect(serverTransport);
  await client.connect(clientTransport);

  /**
   * Calls a tool with the given parameters.
   *
   * Wrapper around the `client.callTool` method to handle the response and errors.
   */
  async function callTool(params: CallToolRequest['params']) {
    const output = await client.callTool(params);
    const { content } = CallToolResultSchema.parse(output);
    const [textContent] = content;

    if (!textContent) {
      return undefined;
    }

    if (textContent.type !== 'text') {
      throw new Error('tool result content is not text');
    }

    if (textContent.text === '') {
      throw new Error('tool result content is empty');
    }

    const result = JSON.parse(textContent.text);

    if (output.isError) {
      throw new Error(result.error.message);
    }

    return result;
  }

  return { client, clientTransport, callTool, server, serverTransport };
}

describe('tools', () => {
  test('list organizations', async () => {
    const { callTool } = await setup();

    const org1 = await createOrganization({
      name: 'Org 1',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });
    const org2 = await createOrganization({
      name: 'Org 2',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const result = await callTool({
      name: 'supabase_list_organizations',
      arguments: {},
    });

    expect(result).toEqual([
      { id: org1.id, name: org1.name },
      { id: org2.id, name: org2.name },
    ]);
  });

  test('get organization', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const result = await callTool({
      name: 'supabase_get_organization',
      arguments: {
        id: org.id,
      },
    });

    expect(result).toEqual(org);
  });

  test('get next project cost for free org', async () => {
    const { callTool } = await setup();

    const freeOrg = await createOrganization({
      name: 'Free Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const result = await callTool({
      name: 'supabase_get_cost',
      arguments: {
        type: 'project',
        organization_id: freeOrg.id,
      },
    });

    expect(result).toEqual(
      'The new project will cost $0 monthly. You must repeat this to the user and confirm their understanding.'
    );
  });

  test('get next project cost for paid org with 0 projects', async () => {
    const { callTool } = await setup();

    const paidOrg = await createOrganization({
      name: 'Paid Org',
      plan: 'pro',
      allowed_release_channels: ['ga'],
    });

    const result = await callTool({
      name: 'supabase_get_cost',
      arguments: {
        type: 'project',
        organization_id: paidOrg.id,
      },
    });

    expect(result).toEqual(
      'The new project will cost $0 monthly. You must repeat this to the user and confirm their understanding.'
    );
  });

  test('get next project cost for paid org with > 0 active projects', async () => {
    const { callTool } = await setup();

    const paidOrg = await createOrganization({
      name: 'Paid Org',
      plan: 'pro',
      allowed_release_channels: ['ga'],
    });

    const priorProject = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: paidOrg.id,
    });
    priorProject.status = 'ACTIVE_HEALTHY';

    const result = await callTool({
      name: 'supabase_get_cost',
      arguments: {
        type: 'project',
        organization_id: paidOrg.id,
      },
    });

    expect(result).toEqual(
      `The new project will cost $${PROJECT_COST_MONTHLY} monthly. You must repeat this to the user and confirm their understanding.`
    );
  });

  test('get next project cost for paid org with > 0 inactive projects', async () => {
    const { callTool } = await setup();

    const paidOrg = await createOrganization({
      name: 'Paid Org',
      plan: 'pro',
      allowed_release_channels: ['ga'],
    });

    const priorProject = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: paidOrg.id,
    });
    priorProject.status = 'INACTIVE';

    const result = await callTool({
      name: 'supabase_get_cost',
      arguments: {
        type: 'project',
        organization_id: paidOrg.id,
      },
    });

    expect(result).toEqual(
      `The new project will cost $0 monthly. You must repeat this to the user and confirm their understanding.`
    );
  });

  test('get branch cost', async () => {
    const { callTool } = await setup();

    const paidOrg = await createOrganization({
      name: 'Paid Org',
      plan: 'pro',
      allowed_release_channels: ['ga'],
    });

    const result = await callTool({
      name: 'supabase_get_cost',
      arguments: {
        type: 'branch',
        organization_id: paidOrg.id,
      },
    });

    expect(result).toEqual(
      `The new branch will cost $${BRANCH_COST_HOURLY} hourly. You must repeat this to the user and confirm their understanding.`
    );
  });

  test('list projects', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project1 = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });

    const project2 = await createProject({
      name: 'Project 2',
      region: 'us-east-1',
      organization_id: org.id,
    });

    const result = await callTool({
      name: 'supabase_list_projects',
      arguments: {},
    });

    expect(result).toEqual([project1.details, project2.details]);
  });

  test('get project', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });

    const result = await callTool({
      name: 'supabase_get_project',
      arguments: {
        id: project.id,
      },
    });

    expect(result).toEqual(project.details);
  });

  test('create project', async () => {
    const { callTool } = await setup();

    const freeOrg = await createOrganization({
      name: 'Free Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const confirm_cost_id = await callTool({
      name: 'confirm_cost',
      arguments: {
        type: 'project',
        recurrence: 'monthly',
        amount: 0,
      },
    });

    const newProject = {
      name: 'New Project',
      region: 'us-east-1',
      organization_id: freeOrg.id,
      db_pass: 'dummy-password',
      confirm_cost_id,
    };

    const result = await callTool({
      name: 'supabase_create_project',
      arguments: newProject,
    });

    const { db_pass, confirm_cost_id: _, ...projectInfo } = newProject;

    expect(result).toEqual({
      ...projectInfo,
      id: expect.stringMatching(/^.+$/),
      created_at: expect.stringMatching(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/
      ),
      status: 'UNKNOWN',
    });
  });

  test('create project chooses closest region when undefined', async () => {
    const { callTool } = await setup();

    const freeOrg = await createOrganization({
      name: 'Free Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const confirm_cost_id = await callTool({
      name: 'supabase_confirm_cost',
      arguments: {
        type: 'project',
        recurrence: 'monthly',
        amount: 0,
      },
    });

    const newProject = {
      name: 'New Project',
      organization_id: freeOrg.id,
      db_pass: 'dummy-password',
      confirm_cost_id,
    };

    const result = await callTool({
      name: 'supabase_create_project',
      arguments: newProject,
    });

    const { db_pass, confirm_cost_id: _, ...projectInfo } = newProject;

    expect(result).toEqual({
      ...projectInfo,
      id: expect.stringMatching(/^.+$/),
      created_at: expect.stringMatching(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/
      ),
      status: 'UNKNOWN',
      region: CLOSEST_REGION,
    });
  });

  test('create project without cost confirmation fails', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'Paid Org',
      plan: 'pro',
      allowed_release_channels: ['ga'],
    });

    const newProject = {
      name: 'New Project',
      region: 'us-east-1',
      organization_id: org.id,
      db_pass: 'dummy-password',
    };

    const createProjectPromise = callTool({
      name: 'supabase_create_project',
      arguments: newProject,
    });

    await expect(createProjectPromise).rejects.toThrow(
      'User must confirm understanding of costs before creating a project.'
    );
  });

  test('pause project', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    await callTool({
      name: 'supabase_pause_project',
      arguments: {
        project_id: project.id,
      },
    });

    expect(project.status).toEqual('INACTIVE');
  });

  test('restore project', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'INACTIVE';

    await callTool({
      name: 'supabase_restore_project',
      arguments: {
        project_id: project.id,
      },
    });

    expect(project.status).toEqual('ACTIVE_HEALTHY');
  });

  test('get project url', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const result = await callTool({
      name: 'supabase_get_project_url',
      arguments: {
        project_id: project.id,
      },
    });
    expect(result).toEqual(`https://${project.id}.supabase.co`);
  });

  test('get anon key', async () => {
    const { callTool } = await setup();
    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });
    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const result = await callTool({
      name: 'supabase_get_anon_key',
      arguments: {
        project_id: project.id,
      },
    });
    expect(result).toEqual('dummy-anon-key');
  });

  test('execute sql', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const query = 'select 1+1 as sum';

    const result = await callTool({
      name: 'supabase_execute_sql',
      arguments: {
        project_id: project.id,
        query,
      },
    });

    expect(result).toEqual([{ sum: 2 }]);
  });

  test('can run read queries in read-only mode', async () => {
    const { callTool } = await setup({ readOnly: true });

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const query = 'select 1+1 as sum';

    const result = await callTool({
      name: 'supabase_execute_sql',
      arguments: {
        project_id: project.id,
        query,
      },
    });

    expect(result).toEqual([{ sum: 2 }]);
  });

  test('cannot run write queries in read-only mode', async () => {
    const { callTool } = await setup({ readOnly: true });

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const query =
      'create table test (id integer generated always as identity primary key)';

    const resultPromise = callTool({
      name: 'supabase_execute_sql',
      arguments: {
        project_id: project.id,
        query,
      },
    });

    await expect(resultPromise).rejects.toThrow(
      'permission denied for schema public'
    );
  });

  test('apply migration, list migrations, check tables', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const name = 'test_migration';
    const query =
      'create table test (id integer generated always as identity primary key)';

    const result = await callTool({
      name: 'supabase_apply_migration',
      arguments: {
        project_id: project.id,
        name,
        query,
      },
    });

    expect(result).toEqual([]);

    const listMigrationsResult = await callTool({
      name: 'supabase_list_migrations',
      arguments: {
        project_id: project.id,
      },
    });

    expect(listMigrationsResult).toEqual([
      {
        name,
        version: expect.stringMatching(/^\d{14}$/),
      },
    ]);

    const listTablesResult = await callTool({
      name: 'supabase_list_tables',
      arguments: {
        project_id: project.id,
        schemas: ['public'],
      },
    });

    expect(listTablesResult).toEqual([
      {
        bytes: 8192,
        columns: [
          {
            check: null,
            comment: null,
            data_type: 'integer',
            default_value: null,
            enums: [],
            format: 'int4',
            id: expect.stringMatching(/^\d+\.\d+$/),
            identity_generation: 'ALWAYS',
            is_generated: false,
            is_identity: true,
            is_nullable: false,
            is_unique: false,
            is_updatable: true,
            name: 'id',
            ordinal_position: 1,
            schema: 'public',
            table: 'test',
            table_id: expect.any(Number),
          },
        ],
        comment: null,
        dead_rows_estimate: 0,
        id: expect.any(Number),
        live_rows_estimate: 0,
        name: 'test',
        primary_keys: [
          {
            name: 'id',
            schema: 'public',
            table_id: expect.any(Number),
            table_name: 'test',
          },
        ],
        relationships: [],
        replica_identity: 'DEFAULT',
        rls_enabled: false,
        rls_forced: false,
        schema: 'public',
        size: '8192 bytes',
      },
    ]);
  });

  test('cannot apply migration in read-only mode', async () => {
    const { callTool } = await setup({ readOnly: true });

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const name = 'test-migration';
    const query =
      'create table test (id integer generated always as identity primary key)';

    const resultPromise = callTool({
      name: 'supabase_apply_migration',
      arguments: {
        project_id: project.id,
        name,
        query,
      },
    });

    await expect(resultPromise).rejects.toThrow(
      'Cannot apply migration in read-only mode.'
    );
  });

  test('list tables only under a specific schema', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    await project.db.exec('create schema test;');
    await project.db.exec(
      'create table public.test_1 (id serial primary key);'
    );
    await project.db.exec('create table test.test_2 (id serial primary key);');

    const result = await callTool({
      name: 'supabase_list_tables',
      arguments: {
        project_id: project.id,
        schemas: ['test'],
      },
    });

    expect(result).toEqual(
      expect.arrayContaining([expect.objectContaining({ name: 'test_2' })])
    );
    expect(result).not.toEqual(
      expect.arrayContaining([expect.objectContaining({ name: 'test_1' })])
    );
  });

  test('listing all tables excludes system schemas', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const result = await callTool({
      name: 'supabase_list_tables',
      arguments: {
        project_id: project.id,
      },
    });

    expect(result).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({ schema: 'pg_catalog' }),
      ])
    );

    expect(result).not.toEqual(
      expect.arrayContaining([
        expect.objectContaining({ schema: 'information_schema' }),
      ])
    );

    expect(result).not.toEqual(
      expect.arrayContaining([expect.objectContaining({ schema: 'pg_toast' })])
    );
  });

  test('list extensions', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const result = await callTool({
      name: 'supabase_list_extensions',
      arguments: {
        project_id: project.id,
      },
    });

    expect(result).toMatchInlineSnapshot(`
      [
        {
          "comment": "PL/pgSQL procedural language",
          "default_version": "1.0",
          "installed_version": "1.0",
          "name": "plpgsql",
          "schema": "pg_catalog",
        },
      ]
    `);
  });

  test('invalid access token', async () => {
    const { callTool } = await setup({ accessToken: 'bad-token' });

    const listOrganizationsPromise = callTool({
      name: 'supabase_list_organizations',
      arguments: {},
    });

    await expect(listOrganizationsPromise).rejects.toThrow(
      'Unauthorized. Please provide a valid access token to the MCP server via the --access-token flag.'
    );
  });

  test('invalid sql for apply_migration', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const name = 'test-migration';
    const query = 'invalid sql';

    const applyMigrationPromise = callTool({
      name: 'supabase_apply_migration',
      arguments: {
        project_id: project.id,
        name,
        query,
      },
    });

    await expect(applyMigrationPromise).rejects.toThrow(
      'syntax error at or near "invalid"'
    );
  });

  test('invalid sql for execute_sql', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const query = 'invalid sql';

    const executeSqlPromise = callTool({
      name: 'supabase_execute_sql',
      arguments: {
        project_id: project.id,
        query,
      },
    });

    await expect(executeSqlPromise).rejects.toThrow(
      'syntax error at or near "invalid"'
    );
  });

  test('get logs for each service type', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const services = [
      'api',
      'branch-action',
      'postgres',
      'edge-function',
      'auth',
      'storage',
      'realtime',
    ] as const;

    for (const service of services) {
      const result = await callTool({
        name: 'supabase_get_logs',
        arguments: {
          project_id: project.id,
          service,
        },
      });

      expect(result).toEqual([]);
    }
  });

  test('get logs for invalid service type', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const invalidService = 'invalid-service';
    const getLogsPromise = callTool({
      name: 'supabase_get_logs',
      arguments: {
        project_id: project.id,
        service: invalidService,
      },
    });
    await expect(getLogsPromise).rejects.toThrow('Invalid enum value');
  });

  test('create branch', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const confirm_cost_id = await callTool({
      name: 'supabase_confirm_cost',
      arguments: {
        type: 'branch',
        recurrence: 'hourly',
        amount: BRANCH_COST_HOURLY,
      },
    });

    const branchName = 'test-branch';
    const result = await callTool({
      name: 'supabase_create_branch',
      arguments: {
        project_id: project.id,
        name: branchName,
        confirm_cost_id,
      },
    });

    expect(result).toEqual({
      id: expect.stringMatching(/^.+$/),
      name: branchName,
      project_ref: expect.stringMatching(/^.+$/),
      parent_project_ref: project.id,
      is_default: false,
      persistent: false,
      status: 'CREATING_PROJECT',
      created_at: expect.stringMatching(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/
      ),
      updated_at: expect.stringMatching(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/
      ),
    });
  });

  test('create branch without cost confirmation fails', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'Paid Org',
      plan: 'pro',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const branchName = 'test-branch';
    const createBranchPromise = callTool({
      name: 'supabase_create_branch',
      arguments: {
        project_id: project.id,
        name: branchName,
      },
    });

    await expect(createBranchPromise).rejects.toThrow(
      'User must confirm understanding of costs before creating a branch.'
    );
  });

  test('delete branch', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const confirm_cost_id = await callTool({
      name: 'supabase_confirm_cost',
      arguments: {
        type: 'branch',
        recurrence: 'hourly',
        amount: BRANCH_COST_HOURLY,
      },
    });

    const branch = await callTool({
      name: 'supabase_create_branch',
      arguments: {
        project_id: project.id,
        name: 'test-branch',
        confirm_cost_id,
      },
    });

    const listBranchesResult = await callTool({
      name: 'supabase_list_branches',
      arguments: {
        project_id: project.id,
      },
    });

    expect(listBranchesResult).toContainEqual(
      expect.objectContaining({ id: branch.id })
    );
    expect(listBranchesResult).toHaveLength(2);

    await callTool({
      name: 'supabase_delete_branch',
      arguments: {
        branch_id: branch.id,
      },
    });

    const listBranchesResultAfterDelete = await callTool({
      name: 'supabase_list_branches',
      arguments: {
        project_id: project.id,
      },
    });

    expect(listBranchesResultAfterDelete).not.toContainEqual(
      expect.objectContaining({ id: branch.id })
    );
    expect(listBranchesResultAfterDelete).toHaveLength(1);

    const mainBranch = listBranchesResultAfterDelete[0];

    const deleteBranchPromise = callTool({
      name: 'supabase_delete_branch',
      arguments: {
        branch_id: mainBranch.id,
      },
    });

    await expect(deleteBranchPromise).rejects.toThrow(
      'Cannot delete the default branch.'
    );
  });

  test('list branches', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const result = await callTool({
      name: 'supabase_list_branches',
      arguments: {
        project_id: project.id,
      },
    });

    expect(result).toStrictEqual([]);
  });

  test('merge branch', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const confirm_cost_id = await callTool({
      name: 'supabase_confirm_cost',
      arguments: {
        type: 'branch',
        recurrence: 'hourly',
        amount: BRANCH_COST_HOURLY,
      },
    });

    const branch = await callTool({
      name: 'supabase_create_branch',
      arguments: {
        project_id: project.id,
        name: 'test-branch',
        confirm_cost_id,
      },
    });

    const migrationName = 'sample_migration';
    const migrationQuery =
      'create table sample (id integer generated always as identity primary key)';
    await callTool({
      name: 'supabase_apply_migration',
      arguments: {
        project_id: branch.project_ref,
        name: migrationName,
        query: migrationQuery,
      },
    });

    const mergeResult = await callTool({
      name: 'supabase_merge_branch',
      arguments: {
        branch_id: branch.id,
      },
    });

    expect(mergeResult).toEqual({
      migration_version: expect.stringMatching(/^\d{14}$/),
    });

    // Check that the migration was applied to the parent project
    const listResult = await callTool({
      name: 'supabase_list_migrations',
      arguments: {
        project_id: project.id,
      },
    });

    expect(listResult).toContainEqual({
      name: migrationName,
      version: expect.stringMatching(/^\d{14}$/),
    });
  });

  test('reset branch', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const confirm_cost_id = await callTool({
      name: 'supabase_confirm_cost',
      arguments: {
        type: 'branch',
        recurrence: 'hourly',
        amount: BRANCH_COST_HOURLY,
      },
    });

    const branch = await callTool({
      name: 'supabase_create_branch',
      arguments: {
        project_id: project.id,
        name: 'test-branch',
        confirm_cost_id,
      },
    });

    // Create a table via execute_sql so that it is untracked
    const query =
      'create table test_untracked (id integer generated always as identity primary key)';
    await callTool({
      name: 'supabase_execute_sql',
      arguments: {
        project_id: branch.project_ref,
        query,
      },
    });

    const firstTablesResult = await callTool({
      name: 'supabase_list_tables',
      arguments: {
        project_id: branch.project_ref,
      },
    });

    expect(firstTablesResult).toContainEqual(
      expect.objectContaining({ name: 'test_untracked' })
    );

    await callTool({
      name: 'supabase_reset_branch',
      arguments: {
        branch_id: branch.id,
      },
    });

    const secondTablesResult = await callTool({
      name: 'supabase_list_tables',
      arguments: {
        project_id: branch.project_ref,
      },
    });

    // Expect the untracked table to be removed after reset
    expect(secondTablesResult).not.toContainEqual(
      expect.objectContaining({ name: 'test_untracked' })
    );
  });

  test('revert migrations', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const confirm_cost_id = await callTool({
      name: 'supabase_confirm_cost',
      arguments: {
        type: 'branch',
        recurrence: 'hourly',
        amount: BRANCH_COST_HOURLY,
      },
    });

    const branch = await callTool({
      name: 'supabase_create_branch',
      arguments: {
        project_id: project.id,
        name: 'test-branch',
        confirm_cost_id,
      },
    });

    const migrationName = 'sample_migration';
    const migrationQuery =
      'create table sample (id integer generated always as identity primary key)';
    await callTool({
      name: 'supabase_apply_migration',
      arguments: {
        project_id: branch.project_ref,
        name: migrationName,
        query: migrationQuery,
      },
    });

    // Check that migration has been applied to the branch
    const firstListResult = await callTool({
      name: 'supabase_list_migrations',
      arguments: {
        project_id: branch.project_ref,
      },
    });

    expect(firstListResult).toContainEqual({
      name: migrationName,
      version: expect.stringMatching(/^\d{14}$/),
    });

    const firstTablesResult = await callTool({
      name: 'supabase_list_tables',
      arguments: {
        project_id: branch.project_ref,
      },
    });

    expect(firstTablesResult).toContainEqual(
      expect.objectContaining({ name: 'sample' })
    );

    await callTool({
      name: 'supabase_reset_branch',
      arguments: {
        branch_id: branch.id,
        migration_version: '0',
      },
    });

    // Check that all migrations have been reverted
    const secondListResult = await callTool({
      name: 'supabase_list_migrations',
      arguments: {
        project_id: branch.project_ref,
      },
    });

    expect(secondListResult).toStrictEqual([]);

    const secondTablesResult = await callTool({
      name: 'supabase_list_tables',
      arguments: {
        project_id: branch.project_ref,
      },
    });

    expect(secondTablesResult).not.toContainEqual(
      expect.objectContaining({ name: 'sample' })
    );
  });

  test('rebase branch', async () => {
    const { callTool } = await setup();

    const org = await createOrganization({
      name: 'My Org',
      plan: 'free',
      allowed_release_channels: ['ga'],
    });

    const project = await createProject({
      name: 'Project 1',
      region: 'us-east-1',
      organization_id: org.id,
    });
    project.status = 'ACTIVE_HEALTHY';

    const confirm_cost_id = await callTool({
      name: 'supabase_confirm_cost',
      arguments: {
        type: 'branch',
        recurrence: 'hourly',
        amount: BRANCH_COST_HOURLY,
      },
    });

    const branch = await callTool({
      name: 'supabase_create_branch',
      arguments: {
        project_id: project.id,
        name: 'test-branch',
        confirm_cost_id,
      },
    });

    const migrationName = 'sample_migration';
    const migrationQuery =
      'create table sample (id integer generated always as identity primary key)';
    await callTool({
      name: 'supabase_apply_migration',
      arguments: {
        project_id: project.id,
        name: migrationName,
        query: migrationQuery,
      },
    });

    const rebaseResult = await callTool({
      name: 'supabase_rebase_branch',
      arguments: {
        branch_id: branch.id,
      },
    });

    expect(rebaseResult).toEqual({
      migration_version: expect.stringMatching(/^\d{14}$/),
    });

    // Check that the production migration was applied to the branch
    const listResult = await callTool({
      name: 'supabase_list_migrations',
      arguments: {
        project_id: branch.project_ref,
      },
    });

    expect(listResult).toContainEqual({
      name: migrationName,
      version: expect.stringMatching(/^\d{14}$/),
    });
  });

  // We use snake_case because it aligns better with most MCP clients
  test('all tools follow snake_case naming convention', async () => {
    const { client } = await setup();

    const { tools } = await client.listTools();

    for (const tool of tools) {
      expect(tool.name, 'expected tool name to be snake_case').toMatch(
        /^[a-z0-9_]+$/
      );

      const parameterNames = Object.keys(tool.inputSchema.properties ?? {});
      for (const name of parameterNames) {
        expect(name, 'expected parameter to be snake_case').toMatch(
          /^[a-z0-9_]+$/
        );
      }
    }
  });
});
