import { createMcpServer, tool } from '@supabase/mcp-utils';
import { z } from 'zod';
import packageJson from '../package.json' with { type: 'json' };
const { version } = packageJson;
import { getLogQuery } from './logs.js';
import {
  assertSuccess,
  createManagementApiClient,
  type ManagementApiClient,
} from './management-api/index.js';
import { generatePassword } from './password.js';
import { listExtensionsSql, listTablesSql } from './pg-meta/index.js';
import type { PostgresExtension, PostgresTable } from './pg-meta/types.js';
import { getBranchCost, getNextProjectCost, type Cost } from './pricing.js';
import {
  AWS_REGION_CODES,
  getClosestAwsRegion,
  getCountryCode,
  getCountryCoordinates,
} from './regions.js';
import { hashObject } from './util.js';
import { AsyncLocalStorage } from 'async_hooks';

export const asyncLocalStorage = new AsyncLocalStorage<{
  accessToken: string;
}>();

function getManagementApiClient(): ManagementApiClient {
  const store = asyncLocalStorage.getStore();
  if (!store) {
    throw new Error('Access token not found in AsyncLocalStorage');
  }
  
  return createManagementApiClient(
    'https://api.supabase.com',
    store.accessToken,
    {
      'User-Agent': `supabase-mcp/${version}`,
    }
  );
}

export function getAccessToken(): string {
  const store = asyncLocalStorage.getStore();
  if (!store) {
    throw new Error('Access token not found in AsyncLocalStorage');
  }
  return store.accessToken;
}

export type SupabasePlatformOptions = {
};

export type SupabaseMcpServerOptions = {
  /**
   * Platform options for Supabase.
   */
  platform: SupabasePlatformOptions;

  /**
   * Executes database queries in read-only mode if true.
   */
  readOnly?: boolean;
};

/**
 * Creates an MCP server for interacting with Supabase.
 */
export function createSupabaseMcpServer(options: SupabaseMcpServerOptions) {
  async function executeSql<T>(projectId: string, query: string): Promise<T[]> {
    const response = await getManagementApiClient().POST(
      '/v1/projects/{ref}/database/query',
      {
        params: {
          path: {
            ref: projectId,
          },
        },
        body: {
          query,
          read_only: options.readOnly,
        },
      }
    );

    assertSuccess(response, 'Failed to execute SQL query');

    return response.data as unknown as T[];
  }

  async function getClosestRegion() {
    return getClosestAwsRegion(getCountryCoordinates(await getCountryCode()))
      .code;
  }

  const server = createMcpServer({
    name: 'supabase',
    version,
    onInitialize(clientInfo) {
    },

    // Note: tools are intentionally snake_case to align better with most MCP clients
    tools: {
      supabase_list_projects: tool({
        description: 'Lists all Supabase projects for the user.',
        parameters: z.object({}),
        execute: async () => {
          const response = await getManagementApiClient().GET('/v1/projects');

          assertSuccess(response, 'Failed to fetch projects');

          return response.data;
        },
      }),
      supabase_get_project: tool({
        description: 'Gets details for a Supabase project.',
        parameters: z.object({
          id: z.string().describe('The project ID'),
        }),
        execute: async ({ id }) => {
          const response = await getManagementApiClient().GET('/v1/projects/{ref}', {
            params: {
              path: {
                ref: id,
              },
            },
          });
          assertSuccess(response, 'Failed to fetch project');
          return response.data;
        },
      }),
      supabase_get_cost: tool({
        description:
          'Gets the cost of creating a new project or branch. Never assume organization as costs can be different for each.',
        parameters: z.object({
          type: z.enum(['project', 'branch']),
          organization_id: z
            .string()
            .describe('The organization ID. Always ask the user.'),
        }),
        execute: async ({ type, organization_id }) => {
          function generateResponse(cost: Cost) {
            return `The new ${type} will cost $${cost.amount} ${cost.recurrence}. You must repeat this to the user and confirm their understanding.`;
          }
          switch (type) {
            case 'project': {
              const cost = await getNextProjectCost(
                getManagementApiClient(),
                organization_id
              );
              return generateResponse(cost);
            }
            case 'branch': {
              const cost = getBranchCost();
              return generateResponse(cost);
            }
            default:
              throw new Error(`Unknown cost type: ${type}`);
          }
        },
      }),
      supabase_confirm_cost: tool({
        description:
          'Ask the user to confirm their understanding of the cost of creating a new project or branch. Call `get_cost` first. Returns a unique ID for this confirmation which should be passed to `create_project` or `create_branch`.',
        parameters: z.object({
          type: z.enum(['project', 'branch']),
          recurrence: z.enum(['hourly', 'monthly']),
          amount: z.number(),
        }),
        execute: async (cost) => {
          return await hashObject(cost);
        },
      }),
      supabase_create_project: tool({
        description:
          'Creates a new Supabase project. Always ask the user which organization to create the project in. The project can take a few minutes to initialize - use `get_project` to check the status.',
        parameters: z.object({
          name: z.string().describe('The name of the project'),
          region: z.optional(
            z
              .enum(AWS_REGION_CODES)
              .describe(
                'The region to create the project in. Defaults to the closest region.'
              )
          ),
          organization_id: z.string(),
          confirm_cost_id: z
            .string({
              required_error:
                'User must confirm understanding of costs before creating a project.',
            })
            .describe('The cost confirmation ID. Call `confirm_cost` first.'),
        }),
        execute: async ({ name, region, organization_id, confirm_cost_id }) => {
          const cost = await getNextProjectCost(
            getManagementApiClient(),
            organization_id
          );
          const costHash = await hashObject(cost);
          if (costHash !== confirm_cost_id) {
            throw new Error(
              'Cost confirmation ID does not match the expected cost of creating a project.'
            );
          }

          const response = await getManagementApiClient().POST('/v1/projects', {
            body: {
              name,
              region: region ?? (await getClosestRegion()),
              organization_id,
              db_pass: generatePassword({
                length: 16,
                numbers: true,
                uppercase: true,
                lowercase: true,
              }),
            },
          });

          assertSuccess(response, 'Failed to create project');

          return response.data;
        },
      }),
      supabase_pause_project: tool({
        description: 'Pauses a Supabase project.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          const response = await getManagementApiClient().POST(
            '/v1/projects/{ref}/pause',
            {
              params: {
                path: {
                  ref: project_id,
                },
              },
            }
          );

          assertSuccess(response, 'Failed to pause project');
        },
      }),
      supabase_restore_project: tool({
        description: 'Restores a Supabase project.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          const response = await getManagementApiClient().POST(
            '/v1/projects/{ref}/restore',
            {
              params: {
                path: {
                  ref: project_id,
                },
              },
              body: {},
            }
          );

          assertSuccess(response, 'Failed to restore project');
        },
      }),
      supabase_list_organizations: tool({
        description: 'Lists all organizations that the user is a member of.',
        parameters: z.object({}),
        execute: async () => {
          const response = await getManagementApiClient().GET('/v1/organizations');

          assertSuccess(response, 'Failed to fetch organizations');

          return response.data;
        },
      }),
      supabase_get_organization: tool({
        description:
          'Gets details for an organization. Includes subscription plan.',
        parameters: z.object({
          id: z.string().describe('The organization ID'),
        }),
        execute: async ({ id: organizationId }) => {
          const response = await getManagementApiClient().GET(
            '/v1/organizations/{slug}',
            {
              params: {
                path: {
                  slug: organizationId,
                },
              },
            }
          );

          assertSuccess(response, 'Failed to fetch organization');

          return response.data;
        },
      }),
      supabase_list_tables: tool({
        description: 'Lists all tables in a schema.',
        parameters: z.object({
          project_id: z.string(),
          schemas: z
            .optional(z.array(z.string()))
            .describe(
              'Optional list of schemas to include. Defaults to all schemas.'
            ),
        }),
        execute: async ({ project_id, schemas }) => {
          const sql = listTablesSql(schemas);
          const data = await executeSql<PostgresTable>(project_id, sql);
          return data;
        },
      }),
      supabase_list_extensions: tool({
        description: 'Lists all extensions in the database.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          const sql = listExtensionsSql();
          const data = await executeSql<PostgresExtension>(project_id, sql);
          return data;
        },
      }),
      supabase_list_migrations: tool({
        description: 'Lists all migrations in the database.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          const response = await getManagementApiClient().GET(
            '/v1/projects/{ref}/database/migrations',
            {
              params: {
                path: {
                  ref: project_id,
                },
              },
            }
          );

          assertSuccess(response, 'Failed to fetch migrations');

          return response.data;
        },
      }),
      supabase_apply_migration: tool({
        description:
          'Applies a migration to the database. Use this when executing DDL operations.',
        parameters: z.object({
          project_id: z.string(),
          name: z.string().describe('The name of the migration in snake_case'),
          query: z.string().describe('The SQL query to apply'),
        }),
        execute: async ({ project_id, name, query }) => {
          if (options.readOnly) {
            throw new Error('Cannot apply migration in read-only mode.');
          }

          const response = await getManagementApiClient().POST(
            '/v1/projects/{ref}/database/migrations',
            {
              params: {
                path: {
                  ref: project_id,
                },
              },
              body: {
                name,
                query,
              },
            }
          );

          assertSuccess(response, 'Failed to apply migration');

          return response.data;
        },
      }),
      supabase_execute_sql: tool({
        description:
          'Executes raw SQL in the Postgres database. Use `apply_migration` instead for DDL operations.',
        parameters: z.object({
          project_id: z.string(),
          query: z.string().describe('The SQL query to execute'),
        }),
        execute: async ({ query, project_id }) => {
          return await executeSql(project_id, query);
        },
      }),
      supabase_get_logs: tool({
        description:
          'Gets logs for a Supabase project by service type. Use this to help debug problems with your app. This will only return logs within the last minute. If the logs you are looking for are older than 1 minute, re-run your test to reproduce them.',
        parameters: z.object({
          project_id: z.string(),
          service: z
            .enum([
              'api',
              'branch-action',
              'postgres',
              'edge-function',
              'auth',
              'storage',
              'realtime',
            ])
            .describe('The service to fetch logs for'),
        }),
        execute: async ({ project_id, service }) => {
          // Omitting start and end time defaults to the last minute.
          // But since branch actions are async, we need to wait longer
          // for jobs to be scheduled and run to completion.
          const timestamp =
            service === 'branch-action'
              ? new Date(Date.now() - 5 * 60 * 1000)
              : undefined;
          const response = await getManagementApiClient().GET(
            '/v1/projects/{ref}/analytics/endpoints/logs.all',
            {
              params: {
                path: {
                  ref: project_id,
                },
                query: {
                  iso_timestamp_start: timestamp?.toISOString(),
                  sql: getLogQuery(service),
                },
              },
            }
          );

          assertSuccess(response, 'Failed to fetch logs');

          return response.data;
        },
      }),

      supabase_get_project_url: tool({
        description: 'Gets the API URL for a project.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          return `https://${project_id}.supabase.co`;
        },
      }),
      supabase_get_anon_key: tool({
        description: 'Gets the anonymous API key for a project.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          const response = await getManagementApiClient().GET(
            '/v1/projects/{ref}/api-keys',
            {
              params: {
                path: {
                  ref: project_id,
                },
                query: {
                  reveal: false,
                },
              },
            }
          );

          assertSuccess(response, 'Failed to fetch API keys');

          const anonKey = response.data?.find((key) => key.name === 'anon');

          if (!anonKey) {
            throw new Error('Anonymous key not found');
          }

          return anonKey.api_key;
        },
      }),
      supabase_generate_typescript_types: tool({
        description: 'Generates TypeScript types for a project.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          const response = await getManagementApiClient().GET(
            '/v1/projects/{ref}/types/typescript',
            {
              params: {
                path: {
                  ref: project_id,
                },
              },
            }
          );

          assertSuccess(response, 'Failed to fetch TypeScript types');

          return response.data;
        },
      }),

      // Experimental features
      supabase_create_branch: tool({
        description:
          'Creates a development branch on a Supabase project. This will apply all migrations from the main project to a fresh branch database. Note that production data will not carry over. The branch will get its own project_id via the resulting project_ref. Use this ID to execute queries and migrations on the branch.',
        parameters: z.object({
          project_id: z.string(),
          name: z
            .string()
            .default('develop')
            .describe('Name of the branch to create'),
          confirm_cost_id: z
            .string({
              required_error:
                'User must confirm understanding of costs before creating a branch.',
            })
            .describe('The cost confirmation ID. Call `confirm_cost` first.'),
        }),
        execute: async ({ project_id, name, confirm_cost_id }) => {
          const cost = getBranchCost();
          const costHash = await hashObject(cost);
          if (costHash !== confirm_cost_id) {
            throw new Error(
              'Cost confirmation ID does not match the expected cost of creating a branch.'
            );
          }

          const createBranchResponse = await getManagementApiClient().POST(
            '/v1/projects/{ref}/branches',
            {
              params: {
                path: {
                  ref: project_id,
                },
              },
              body: {
                branch_name: name,
              },
            }
          );

          assertSuccess(createBranchResponse, 'Failed to create branch');

          // Creating a default branch means we just enabled branching
          // TODO: move this logic to API eventually.
          if (createBranchResponse.data.is_default) {
            await getManagementApiClient().PATCH('/v1/branches/{branch_id}', {
              params: {
                path: {
                  branch_id: createBranchResponse.data.id,
                },
              },
              body: {
                branch_name: 'main',
              },
            });

            const response = await getManagementApiClient().POST(
              '/v1/projects/{ref}/branches',
              {
                params: {
                  path: {
                    ref: project_id,
                  },
                },
                body: {
                  branch_name: name,
                },
              }
            );

            assertSuccess(response, 'Failed to create branch');

            return response.data;
          }

          return createBranchResponse.data;
        },
      }),
      supabase_list_branches: tool({
        description:
          'Lists all development branches of a Supabase project. This will return branch details including status which you can use to check when operations like merge/rebase/reset complete.',
        parameters: z.object({
          project_id: z.string(),
        }),
        execute: async ({ project_id }) => {
          const response = await getManagementApiClient().GET(
            '/v1/projects/{ref}/branches',
            {
              params: {
                path: {
                  ref: project_id,
                },
              },
            }
          );

          // There are no branches if branching is disabled
          if (response.response.status === 422) return [];
          assertSuccess(response, 'Failed to list branches');

          return response.data;
        },
      }),
      supabase_delete_branch: tool({
        description: 'Deletes a development branch.',
        parameters: z.object({
          branch_id: z.string(),
        }),
        execute: async ({ branch_id }) => {
          const response = await getManagementApiClient().DELETE(
            '/v1/branches/{branch_id}',
            {
              params: {
                path: {
                  branch_id,
                },
              },
            }
          );

          assertSuccess(response, 'Failed to delete branch');

          return response.data;
        },
      }),
      supabase_merge_branch: tool({
        description:
          'Merges migrations and edge functions from a development branch to production.',
        parameters: z.object({
          branch_id: z.string(),
        }),
        execute: async ({ branch_id }) => {
          const response = await getManagementApiClient().POST(
            '/v1/branches/{branch_id}/merge',
            {
              params: {
                path: {
                  branch_id,
                },
              },
              body: {},
            }
          );

          assertSuccess(response, 'Failed to merge branch');

          return response.data;
        },
      }),
      supabase_reset_branch: tool({
        description:
          'Resets migrations of a development branch. Any untracked data or schema changes will be lost.',
        parameters: z.object({
          branch_id: z.string(),
          migration_version: z
            .string()
            .optional()
            .describe(
              'Reset your development branch to a specific migration version.'
            ),
        }),
        execute: async ({ branch_id, migration_version }) => {
          const response = await getManagementApiClient().POST(
            '/v1/branches/{branch_id}/reset',
            {
              params: {
                path: {
                  branch_id,
                },
              },
              body: {
                migration_version,
              },
            }
          );

          assertSuccess(response, 'Failed to reset branch');

          return response.data;
        },
      }),
      supabase_rebase_branch: tool({
        description:
          'Rebases a development branch on production. This will effectively run any newer migrations from production onto this branch to help handle migration drift.',
        parameters: z.object({
          branch_id: z.string(),
        }),
        execute: async ({ branch_id }) => {
          const response = await getManagementApiClient().POST(
            '/v1/branches/{branch_id}/push',
            {
              params: {
                path: {
                  branch_id,
                },
              },
              body: {},
            }
          );

          assertSuccess(response, 'Failed to rebase branch');

          return response.data;
        },
      }),
    },
  });

  return server;
}
