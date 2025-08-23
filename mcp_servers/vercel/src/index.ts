#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { AsyncLocalStorage } from 'async_hooks';
// Load environment variables only in development
if (process.env.NODE_ENV !== 'production') {
  import('dotenv').then(dotenv => dotenv.config());
}
import { 
  VercelDeployment, 
  VercelProject, 
  VercelDomain, 
  VercelEnvironmentVariable,
  CreateProjectRequest,
  UpdateProjectRequest} from './types/vercel.js';
import { z } from 'zod';
import {
  validateInput,
  ListDeploymentsSchema,
  GetDeploymentSchema,
  CancelDeploymentSchema,
  GetDeploymentLogsSchema,
  ListProjectsSchema,
  GetProjectSchema,
  CreateProjectSchema,
  UpdateProjectSchema,
  DeleteProjectSchema,
  ListDomainsSchema,
  ListEnvVarsSchema,
  CreateEnvVarSchema,
  UpdateEnvVarSchema,
  DeleteEnvVarSchema
} from './schema.js';
import {
  formatDeployment,
  formatProject,
  formatDomain,
  formatEnvVar,
  sanitizeErrorMessage
} from './util.js';



// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  apiToken: string;
  teamId?: string;
}>();

// Helper function to get Vercel config from async local storage
function getVercelConfig(): { apiToken: string; teamId?: string; baseUrl: string } {
  const store = asyncLocalStorage.getStore();
  if (!store) {
    throw new Error('API token not found in AsyncLocalStorage');
  }
  return {
    apiToken: store.apiToken,
    teamId: store.teamId,
    baseUrl: 'https://api.vercel.com'
  };
}

// Helper function to make Vercel API requests with improved error handling
async function makeVercelRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const config = getVercelConfig();
  const url = `${config.baseUrl}${endpoint}`;
  const headers = {
    'Authorization': `Bearer ${config.apiToken}`,
    'Content-Type': 'application/json',
    ...options.headers
  };

  // Add team ID to query params if configured
  const urlObj = new URL(url);
  if (config.teamId) {
    urlObj.searchParams.set('teamId', config.teamId);
  }

  try {
    const response = await fetch(urlObj.toString(), {
      ...options,
      headers
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      
      try {
        const errorData = JSON.parse(errorText);
        if (errorData.error?.message) {
          errorMessage = errorData.error.message;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // Use HTTP status message if JSON parsing fails
      }
      
      throw new Error(errorMessage);
    }

    // Handle empty responses for DELETE operations
    if (options.method === 'DELETE' && response.status === 204) {
      return {} as T;
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      return data as T;
    } else {
      // Return empty object for non-JSON responses
      return {} as T;
    }
  } catch (error) {
    // Improve error handling for network issues
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error: Unable to connect to Vercel API');
    }
    throw error;
  }
}

// Helper function to safely validate and handle tool arguments
function safeValidateInput<T>(schema: z.ZodSchema<T>, args: any): T {
  try {
    return validateInput(schema, args || {});
  } catch (error) {
    throw new Error(`Invalid input: ${sanitizeErrorMessage(error)}`);
  }
}

class VercelMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'vercel-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        // Deployment tools
        {
          name: 'vercel_list_deployments',
          description: 'List deployments with optional filtering by project, state, and time range',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'Filter by project ID' },
              state: { 
                type: 'string', 
                enum: ['BUILDING', 'ERROR', 'INITIALIZING', 'QUEUED', 'READY', 'CANCELED'],
                description: 'Filter by deployment state' 
              },
              limit: { type: 'number', minimum: 1, maximum: 100, default: 20, description: 'Number of deployments to return' },
              until: { type: 'number', description: 'List deployments created before this timestamp' },
              since: { type: 'number', description: 'List deployments created after this timestamp' }
            }
          }
        },
        {
          name: 'vercel_get_deployment',
          description: 'Get detailed information about a specific deployment',
          inputSchema: {
            type: 'object',
            properties: {
              deploymentId: { type: 'string', description: 'The deployment ID or URL' }
            },
            required: ['deploymentId']
          }
        },
        {
          name: 'vercel_cancel_deployment',
          description: 'Cancel an in-progress deployment',
          inputSchema: {
            type: 'object',
            properties: {
              deploymentId: { type: 'string', description: 'The deployment ID to cancel' }
            },
            required: ['deploymentId']
          }
        },
        {
          name: 'vercel_get_deployment_logs',
          description: 'Retrieve build and function logs for a deployment',
          inputSchema: {
            type: 'object',
            properties: {
              deploymentId: { type: 'string', description: 'The deployment ID' },
              follow: { type: 'boolean', default: false, description: 'Follow logs in real-time' },
              since: { type: 'number', description: 'Get logs since this timestamp' },
              until: { type: 'number', description: 'Get logs until this timestamp' }
            },
            required: ['deploymentId']
          }
        },

        // Project management tools
        {
          name: 'vercel_list_projects',
          description: 'List all accessible projects',
          inputSchema: {
            type: 'object',
            properties: {
              limit: { type: 'number', minimum: 1, maximum: 100, default: 20, description: 'Number of projects to return' },
              from: { type: 'string', description: 'Pagination cursor' },
              search: { type: 'string', description: 'Search projects by name' }
            }
          }
        },
        {
          name: 'vercel_get_project',
          description: 'Get detailed information about a specific project',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'The project ID or name' }
            },
            required: ['projectId']
          }
        },
        {
          name: 'vercel_create_project',
          description: 'Create a new project from a Git repository',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Project name' },
              gitRepository: {
                type: 'object',
                properties: {
                  type: { type: 'string', enum: ['github', 'gitlab', 'bitbucket'] },
                  repo: { type: 'string', description: 'Repository in format owner/repo' }
                }
              },
              buildCommand: { type: 'string' },
              devCommand: { type: 'string' },
              framework: { type: 'string' },
              installCommand: { type: 'string' },
              outputDirectory: { type: 'string' },
              publicSource: { type: 'boolean' },
              rootDirectory: { type: 'string' },
              serverlessFunctionRegion: { type: 'string' },
              environmentVariables: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    key: { type: 'string' },
                    value: { type: 'string' },
                    target: {
                      type: 'array',
                      items: { type: 'string', enum: ['production', 'preview', 'development'] }
                    }
                  },
                  required: ['key', 'value', 'target']
                }
              }
            },
            required: ['name']
          }
        },
        {
          name: 'vercel_update_project',
          description: 'Update project configuration and settings',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'The project ID' },
              name: { type: 'string' },
              buildCommand: { type: 'string' },
              devCommand: { type: 'string' },
              framework: { type: 'string' },
              installCommand: { type: 'string' },
              outputDirectory: { type: 'string' },
              publicSource: { type: 'boolean' },
              rootDirectory: { type: 'string' },
              serverlessFunctionRegion: { type: 'string' }
            },
            required: ['projectId']
          }
        },
        {
          name: 'vercel_delete_project',
          description: 'Delete a project (WARNING: This action cannot be undone)',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'The project ID to delete' }
            },
            required: ['projectId']
          }
        },

        // Domain management tools
        {
          name: 'vercel_list_domains',
          description: 'List all configured custom domains',
          inputSchema: {
            type: 'object',
            properties: {
              limit: { type: 'number', minimum: 1, maximum: 100, default: 20 },
              since: { type: 'number', description: 'List domains created after this timestamp' },
              until: { type: 'number', description: 'List domains created before this timestamp' }
            }
          }
        },
        // Environment variables tools
        {
          name: 'vercel_list_env_vars',
          description: 'List environment variables for a project',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'Project ID' },
              decrypt: { type: 'boolean', default: false, description: 'Decrypt sensitive values' }
            },
            required: ['projectId']
          }
        },
        {
          name: 'vercel_create_env_var',
          description: 'Add a new environment variable to a project',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'Project ID' },
              key: { type: 'string', description: 'Environment variable name' },
              value: { type: 'string', description: 'Environment variable value' },
              target: {
                type: 'array',
                items: { type: 'string', enum: ['production', 'preview', 'development'] },
                description: 'Target environments'
              },
              gitBranch: { type: 'string', description: 'Specific git branch' },
              type: { 
                type: 'string', 
                enum: ['system', 'secret', 'encrypted', 'plain'], 
                default: 'encrypted',
                description: 'Variable type'
              }
            },
            required: ['projectId', 'key', 'value', 'target']
          }
        },
        {
          name: 'vercel_update_env_var',
          description: 'Update an existing environment variable',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'Project ID' },
              envVarId: { type: 'string', description: 'Environment variable ID' },
              key: { type: 'string', description: 'New variable name' },
              value: { type: 'string', description: 'New variable value' },
              target: {
                type: 'array',
                items: { type: 'string', enum: ['production', 'preview', 'development'] },
                description: 'Target environments'
              },
              gitBranch: { type: 'string', description: 'Specific git branch' },
              type: { 
                type: 'string', 
                enum: ['system', 'secret', 'encrypted', 'plain'], 
                description: 'Variable type'
              }
            },
            required: ['projectId', 'envVarId']
          }
        },
        {
          name: 'vercel_delete_env_var',
          description: 'Delete an environment variable from a project',
          inputSchema: {
            type: 'object',
            properties: {
              projectId: { type: 'string', description: 'Project ID' },
              envVarId: { type: 'string', description: 'Environment variable ID to delete' }
            },
            required: ['projectId', 'envVarId']
          }
        },
        {
          name: 'vercel_get_deployment_events',
          description: 'Get real-time deployment events and status updates',
          inputSchema: {
            type: 'object',
            properties: {
              deploymentId: { type: 'string', description: 'The deployment ID' },
              follow: { type: 'boolean', default: false, description: 'Follow events in real-time' }
            },
            required: ['deploymentId']
          }
        },
        {
          name: 'vercel_list_teams',
          description: 'List all teams accessible to the current user',
          inputSchema: {
            type: 'object',
            properties: {
              limit: { type: 'number', minimum: 1, maximum: 100, default: 20, description: 'Number of teams to return' }
            }
          }
        },
        {
          name: 'vercel_search_deployments',
          description: 'Search deployments with advanced filtering',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Search query for deployment names or URLs' },
              projectId: { type: 'string', description: 'Filter by project ID' },
              state: { 
                type: 'string', 
                enum: ['BUILDING', 'ERROR', 'INITIALIZING', 'QUEUED', 'READY', 'CANCELED'],
                description: 'Filter by deployment state' 
              },
              limit: { type: 'number', minimum: 1, maximum: 100, default: 20, description: 'Number of deployments to return' }
            }
          }
        }
      ]
    }));

    // Call tool handler with improved error handling
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        let result;
        switch (request.params.name) {
          // Deployment tools
          case 'vercel_list_deployments':
            result = await this.listDeployments(request.params.arguments);
            break;
          case 'vercel_get_deployment':
            result = await this.getDeployment(request.params.arguments);
            break;
          case 'vercel_cancel_deployment':
            result = await this.cancelDeployment(request.params.arguments);
            break;
          case 'vercel_get_deployment_logs':
            result = await this.getDeploymentLogs(request.params.arguments);
            break;

          // Project management tools
          case 'vercel_list_projects':
            result = await this.listProjects(request.params.arguments);
            break;
          case 'vercel_get_project':
            result = await this.getProject(request.params.arguments);
            break;
          case 'vercel_create_project':
            result = await this.createProject(request.params.arguments);
            break;
          case 'vercel_update_project':
            result = await this.updateProject(request.params.arguments);
            break;
          case 'vercel_delete_project':
            result = await this.deleteProject(request.params.arguments);
            break;

          // Domain management tools
          case 'vercel_list_domains':
            result = await this.listDomains(request.params.arguments);
            break;
          // Environment variables tools
          case 'vercel_list_env_vars':
            result = await this.listEnvVars(request.params.arguments);
            break;
          case 'vercel_create_env_var':
            result = await this.createEnvVar(request.params.arguments);
            break;
          case 'vercel_update_env_var':
            result = await this.updateEnvVar(request.params.arguments);
            break;
          case 'vercel_delete_env_var':
            result = await this.deleteEnvVar(request.params.arguments);
            break;
          case 'vercel_get_deployment_events':
            result = await this.getDeploymentEvents(request.params.arguments);
            break;
          case 'vercel_list_teams':
            result = await this.listTeams(request.params.arguments);
            break;
          case 'vercel_search_deployments':
            result = await this.searchDeployments(request.params.arguments);
            break;

          default:
            throw new Error(`Unknown tool: ${request.params.name}`);
        }

        // Ensure result has proper structure
        if (!result || !result.content) {
          throw new Error('Tool returned invalid response structure');
        }

        return result;
      } catch (error) {
        console.error(`Error in tool ${request.params.name}:`, error);
        return {
          content: [
            {
              type: 'text',
              text: `❌ Error: ${sanitizeErrorMessage(error)}`
            }
          ]
        };
      }
    });
  }

  // Deployment tools implementation
  private async listDeployments(args: any) {
    const validatedArgs = safeValidateInput(ListDeploymentsSchema, args || {}) as z.infer<typeof ListDeploymentsSchema>;
    
    const queryParams = new URLSearchParams();
    if (validatedArgs.projectId) queryParams.set('projectId', validatedArgs.projectId);
    if (validatedArgs.state) queryParams.set('state', validatedArgs.state);
    if (validatedArgs.limit) queryParams.set('limit', validatedArgs.limit.toString());
    if (validatedArgs.until) queryParams.set('until', validatedArgs.until.toString());
    if (validatedArgs.since) queryParams.set('since', validatedArgs.since.toString());

    const endpoint = `/v6/deployments?${queryParams.toString()}`;
    const response = await makeVercelRequest<{ deployments: VercelDeployment[] }>(endpoint);

    const formattedDeployments = response.deployments
      .map(deployment => formatDeployment(deployment))
      .join('\n');

    return {
      content: [
        {
          type: 'text',
          text: `Found ${response.deployments.length} deployments:\n\n${formattedDeployments}`
        }
      ]
    };
  }

  private async getDeployment(args: any) {
    const validatedArgs = safeValidateInput(GetDeploymentSchema, args) as z.infer<typeof GetDeploymentSchema>;
    let deploymentId = validatedArgs.deploymentId;
    let deployment: VercelDeployment | null = null;
    
    // First, try to find the deployment from the list (more complete data)
    if (deploymentId && deploymentId.includes('-')) {
      const deploymentsResp = await makeVercelRequest<{ deployments: VercelDeployment[] }>(`/v6/deployments?limit=50`);
      const found = deploymentsResp.deployments.find(d => 
        d.url === deploymentId || 
        d.alias?.includes(deploymentId) ||
        d.uid === deploymentId
      );
      if (found) {
        deployment = found;
        deploymentId = found.uid;
      }
    }
    
    // If not found or direct ID provided, fetch individual deployment
    if (!deployment) {
      if (!deploymentId) {
        return { content: [{ type: 'text', text: 'Error: Deployment ID not found for provided value.' }] };
      }
      try {
        const endpoint = `/v13/deployments/${deploymentId}`;
        deployment = await makeVercelRequest<VercelDeployment>(endpoint);
      } catch (error) {
        return { content: [{ type: 'text', text: `Error: Could not fetch deployment details. ${sanitizeErrorMessage(error)}` }] };
      }
    }
    
    const details = [
      `🚀 Deployment Details`,
      ``,
      `ID: ${deployment.uid || deploymentId}`,
      `Name: ${deployment.name || 'N/A'}`,
      `URL: ${deployment.url || 'N/A'}`,
      `State: ${deployment.state || 'N/A'}`,
      `Created: ${deployment.created ? new Date(deployment.created).toISOString() : 'N/A'}`,
      `Project ID: ${deployment.projectId || 'N/A'}`,
      `Target: ${deployment.target || 'N/A'}`,
      `Type: ${deployment.type || 'N/A'}`
    ];
    
    if (deployment.gitSource) {
      const gitRepo = deployment.gitSource.repo || 'N/A';
      const gitRef = deployment.gitSource.ref || 'main';
      const gitType = deployment.gitSource.type || 'N/A';
      details.push(`Git Source: ${gitType}:${gitRepo}@${gitRef}`);
    }
    
    if (deployment.alias && deployment.alias.length > 0) {
      details.push(`Aliases: ${deployment.alias.join(', ')}`);
    }
    
    return {
      content: [
        {
          type: 'text',
          text: details.join('\n')
        }
      ]
    };
  }

  private async cancelDeployment(args: any) {
    const validatedArgs = safeValidateInput(CancelDeploymentSchema, args) as z.infer<typeof CancelDeploymentSchema>;
    let deploymentId = validatedArgs.deploymentId;
    if (deploymentId && deploymentId.includes('-')) {
      const deploymentsResp = await makeVercelRequest<{ deployments: VercelDeployment[] }>(`/v6/deployments?limit=20`);
      const found = deploymentsResp.deployments.find(d => d.url === deploymentId || d.alias?.includes(deploymentId));
      if (found) deploymentId = found.uid;
    }
    if (!deploymentId) {
      return { content: [{ type: 'text', text: 'Error: Deployment ID not found for provided value.' }] };
    }
    const endpoint = `/v12/deployments/${deploymentId}`;
    await makeVercelRequest(endpoint, { method: 'DELETE' });
    return {
      content: [
        {
          type: 'text',
          text: `✅ Deployment ${deploymentId} has been canceled.`
        }
      ]
    };
  }

  private async getDeploymentLogs(args: any) {
      const validatedArgs = safeValidateInput(GetDeploymentLogsSchema, args) as z.infer<typeof GetDeploymentLogsSchema>;
      let deploymentId = validatedArgs.deploymentId;
      if (deploymentId && deploymentId.includes('-')) {
        const deploymentsResp = await makeVercelRequest<{ deployments: VercelDeployment[] }>(`/v6/deployments?limit=20`);
        const found = deploymentsResp.deployments.find(d => d.url === deploymentId || d.alias?.includes(deploymentId));
        if (found) deploymentId = found.uid;
      }
      if (!deploymentId) {
        return { content: [{ type: 'text', text: 'Error: Deployment ID not found for provided value.' }] };
      }
      
      const fetchEvents = async (id: string) => {
        const qp = new URLSearchParams();
        if (validatedArgs.follow) qp.set('follow', 'true');
        if (validatedArgs.since)  qp.set('since', validatedArgs.since.toString());
        if (validatedArgs.until)  qp.set('until', validatedArgs.until.toString());

        const resp = await makeVercelRequest<any>(`/v2/deployments/${id}/events?${qp.toString()}`);
        const list = resp.data || resp;
      if (!Array.isArray(list) || list.length === 0) {
        return '';
        }
        return list
          .map((log: any) => {
            let ts = 'N/A';
            try { ts = log.timestamp ? new Date(log.timestamp).toISOString() : ts; } catch {}
            const type = log.type?.toUpperCase() || 'LOG';
            const msg  = log.message || log.text || '';
            return `[${ts}] ${type}: ${msg}`;
          })
          .join('\n');
      };

      try {
        // first attempt
        let formattedLogs = await fetchEvents(deploymentId);

        // if empty, fall back to most-recent deployment
        if (!formattedLogs) {
          const rec = await makeVercelRequest<{ deployments: VercelDeployment[] }>(`/v6/deployments?limit=1`);
          if (rec.deployments.length > 0) {
            deploymentId   = rec.deployments[0].uid;
            formattedLogs  = await fetchEvents(deploymentId);
          }
        }

        const output = formattedLogs
          ? formattedLogs
          : 'No logs available for this deployment (even on the most recent one)';

        return {
          content: [
            {
              type: 'text',
              text: `📋 Deployment Logs for ${deploymentId}:\n\n${output}`
            }
          ]
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `❌ Error fetching deployment logs: ${sanitizeErrorMessage(error)}`
            }
          ]
        };
      }
    }
  // Project management tools implementation
  private async listProjects(args: any) {
    const validatedArgs = safeValidateInput(ListProjectsSchema, args || {}) as z.infer<typeof ListProjectsSchema>;
    
    const queryParams = new URLSearchParams();
    if (validatedArgs.limit) queryParams.set('limit', validatedArgs.limit.toString());
    if (validatedArgs.from) queryParams.set('from', validatedArgs.from);
    if (validatedArgs.search) queryParams.set('search', validatedArgs.search);

    const endpoint = `/v9/projects?${queryParams.toString()}`;
    const response = await makeVercelRequest<{ projects: VercelProject[] }>(endpoint);

    const formattedProjects = response.projects
      .map(project => formatProject(project))
      .join('\n');

    return {
      content: [
        {
          type: 'text',
          text: `Found ${response.projects.length} projects:\n\n${formattedProjects}`
        }
      ]
    };
  }

  private async getProject(args: any) {
    const validatedArgs = safeValidateInput(GetProjectSchema, args) as z.infer<typeof GetProjectSchema>;
    
    const endpoint = `/v9/projects/${validatedArgs.projectId}`;
    const project = await makeVercelRequest<VercelProject>(endpoint);

    const details = [
      `📁 Project Details`,
      ``,
      `ID: ${project.id}`,
      `Name: ${project.name}`,
      `Framework: ${project.framework || 'N/A'}`,
      `Created: ${new Date(project.createdAt).toISOString()}`,
      `Updated: ${project.updatedAt ? new Date(project.updatedAt).toISOString() : 'N/A'}`,
      `Build Command: ${project.buildCommand || 'N/A'}`,
      `Dev Command: ${project.devCommand || 'N/A'}`,
      `Install Command: ${project.installCommand || 'N/A'}`,
      `Output Directory: ${project.outputDirectory || 'N/A'}`,
      `Root Directory: ${project.rootDirectory || 'N/A'}`,
      `Public Source: ${project.publicSource ? 'Yes' : 'No'}`
    ];

    if (project.gitRepository) {
      details.push(`Git Repository: ${project.gitRepository.type}:${project.gitRepository.repo}`);
    }

    return {
      content: [
        {
          type: 'text',
          text: details.join('\n')
        }
      ]
    };
  }

  private async createProject(args: any) {
    const validatedArgs = safeValidateInput(CreateProjectSchema, args) as z.infer<typeof CreateProjectSchema>;

    const projectData: CreateProjectRequest = {
      name: validatedArgs.name,
      ...(validatedArgs.gitRepository && { gitRepository: validatedArgs.gitRepository }),
      ...(validatedArgs.buildCommand && { buildCommand: validatedArgs.buildCommand }),
      ...(validatedArgs.devCommand && { devCommand: validatedArgs.devCommand }),
      ...(validatedArgs.framework && { framework: validatedArgs.framework }),
      ...(validatedArgs.installCommand && { installCommand: validatedArgs.installCommand }),
      ...(validatedArgs.outputDirectory && { outputDirectory: validatedArgs.outputDirectory }),
      ...(validatedArgs.publicSource !== undefined && { publicSource: validatedArgs.publicSource }),
      ...(validatedArgs.rootDirectory && { rootDirectory: validatedArgs.rootDirectory }),
      ...(validatedArgs.serverlessFunctionRegion && { serverlessFunctionRegion: validatedArgs.serverlessFunctionRegion }),
      ...(validatedArgs.environmentVariables && { environmentVariables: validatedArgs.environmentVariables })
    };

    const endpoint = '/v10/projects';
    const project = await makeVercelRequest<VercelProject>(endpoint, {
      method: 'POST',
      body: JSON.stringify(projectData)
    });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Project created successfully!\n\n${formatProject(project)}`
        }
      ]
    };
  }

  private async updateProject(args: any) {
    const validatedArgs = safeValidateInput(UpdateProjectSchema, args) as z.infer<typeof UpdateProjectSchema>;

    const updateData: UpdateProjectRequest = {};
    if (validatedArgs.name) updateData.name = validatedArgs.name;
    if (validatedArgs.buildCommand) updateData.buildCommand = validatedArgs.buildCommand;
    if (validatedArgs.devCommand) updateData.devCommand = validatedArgs.devCommand;
    if (validatedArgs.framework) updateData.framework = validatedArgs.framework;
    if (validatedArgs.installCommand) updateData.installCommand = validatedArgs.installCommand;
    if (validatedArgs.outputDirectory) updateData.outputDirectory = validatedArgs.outputDirectory;
    if (validatedArgs.publicSource !== undefined) updateData.publicSource = validatedArgs.publicSource;
    if (validatedArgs.rootDirectory) updateData.rootDirectory = validatedArgs.rootDirectory;
    if (validatedArgs.serverlessFunctionRegion) updateData.serverlessFunctionRegion = validatedArgs.serverlessFunctionRegion;

    const endpoint = `/v9/projects/${validatedArgs.projectId}`;
    const project = await makeVercelRequest<VercelProject>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(updateData)
    });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Project updated successfully!\n\n${formatProject(project)}`
        }
      ]
    };
  }

  private async deleteProject(args: any) {
    const validatedArgs = safeValidateInput(DeleteProjectSchema, args) as z.infer<typeof DeleteProjectSchema>;
    let projectId = validatedArgs.projectId;
    if (projectId && !projectId.startsWith('prj_')) {
      const projectsResp = await makeVercelRequest<{ projects: VercelProject[] }>(`/v9/projects?limit=20`);
      const found = projectsResp.projects.find(p => p.name === projectId);
      if (found) projectId = found.id;
    }
    if (!projectId) {
      return { content: [{ type: 'text', text: 'Error: Project ID not found for provided value.' }] };
    }
    
    const endpoint = `/v9/projects/${projectId}`;
    const response = await makeVercelRequest(endpoint, { method: 'DELETE' });

    return {
      content: [
        {
          type: 'text',
          text: `✅ Project ${projectId} has been deleted permanently.`
        }
      ]
    };
  }

  // Domain management tools implementation
  private async listDomains(args: any) {
    const validatedArgs = safeValidateInput(ListDomainsSchema, args || {}) as z.infer<typeof ListDomainsSchema>;
    
    const queryParams = new URLSearchParams();
    if (validatedArgs.limit) queryParams.set('limit', validatedArgs.limit.toString());
    if (validatedArgs.since) queryParams.set('since', validatedArgs.since.toString());
    if (validatedArgs.until) queryParams.set('until', validatedArgs.until.toString());

    const endpoint = `/v4/domains?${queryParams.toString()}`;
    const response = await makeVercelRequest<{ domains: VercelDomain[] }>(endpoint);

    const formattedDomains = response.domains
      .map(domain => formatDomain(domain))
      .join('\n');

    return {
      content: [
        {
          type: 'text',
          text: `Found ${response.domains.length} domains:\n\n${formattedDomains}`
        }
      ]
    };
  }

  // Environment variables tools implementation
  private async listEnvVars(args: any) {
    const validatedArgs = safeValidateInput(ListEnvVarsSchema, args) as z.infer<typeof ListEnvVarsSchema>;
    let projectId = validatedArgs.projectId;
    if (projectId && !projectId.startsWith('prj_')) {
      const projectsResp = await makeVercelRequest<{ projects: VercelProject[] }>(`/v9/projects?limit=20`);
      const found = projectsResp.projects.find(p => p.name === projectId);
      if (found) projectId = found.id;
    }
    if (!projectId) {
      return { content: [{ type: 'text', text: 'Error: Project ID not found for provided value.' }] };
    }
    
    const queryParams = new URLSearchParams();
    if (validatedArgs.decrypt) queryParams.set('decrypt', 'true');

    const endpoint = `/v8/projects/${projectId}/env?${queryParams.toString()}`;
    const response = await makeVercelRequest<{ envs: VercelEnvironmentVariable[] }>(endpoint);

    const formattedEnvVars = response.envs
      .map(envVar => formatEnvVar(envVar))
      .join('\n');

    return {
      content: [
        {
          type: 'text',
          text: `Found ${response.envs.length} environment variables:\n\n${formattedEnvVars}`
        }
      ]
    };
  }

  private async createEnvVar(args: any) {
    const validatedArgs = safeValidateInput(CreateEnvVarSchema, args) as z.infer<typeof CreateEnvVarSchema>;
    let projectId = validatedArgs.projectId;
    if (projectId && !projectId.startsWith('prj_')) {
      const projectsResp = await makeVercelRequest<{ projects: VercelProject[] }>(`/v9/projects?limit=20`);
      const found = projectsResp.projects.find(p => p.name === projectId);
      if (found) projectId = found.id;
    }
    if (!projectId) {
      return { content: [{ type: 'text', text: 'Error: Project ID not found for provided value.' }] };
    }
    const envVarData = {
      key: validatedArgs.key,
      value: validatedArgs.value,
      target: validatedArgs.target,
      type: validatedArgs.type || 'encrypted',
      ...(validatedArgs.gitBranch && { gitBranch: validatedArgs.gitBranch })
    };
    const endpoint = `/v10/projects/${projectId}/env`;
    const envVar = await makeVercelRequest<VercelEnvironmentVariable>(endpoint, {
      method: 'POST',
      body: JSON.stringify(envVarData)
    });
    return {
      content: [
        {
          type: 'text',
          text: `✅ Environment variable created successfully!\n\n${formatEnvVar(envVar)}`
        }
      ]
    };
  }

  private async updateEnvVar(args: any) {
    const validatedArgs = safeValidateInput(UpdateEnvVarSchema, args) as z.infer<typeof UpdateEnvVarSchema>;
    let projectId = validatedArgs.projectId;
    if (projectId && !projectId.startsWith('prj_')) {
      const projectsResp = await makeVercelRequest<{ projects: VercelProject[] }>(`/v9/projects?limit=20`);
      const found = projectsResp.projects.find(p => p.name === projectId);
      if (found) projectId = found.id;
    }
    if (!projectId) {
      return { content: [{ type: 'text', text: 'Error: Project ID not found for provided value.' }] };
    }
    
    try {
      // If envVarId is not a proper ID, try to find it by key name
      let envVarId = validatedArgs.envVarId;
      if (!envVarId.startsWith('env_')) {
        const envVarsResp = await makeVercelRequest<{ envs: VercelEnvironmentVariable[] }>(`/v8/projects/${projectId}/env`);
        const found = envVarsResp.envs.find(env => env.key === envVarId);
        if (found) {
          // Try different possible ID fields
          envVarId = found.id || found.configurationId || found.key;
        }
      }
      if (!envVarId) {
        return { content: [{ type: 'text', text: 'Error: Environment variable ID not found for provided value.' }] };
      }
      
      const updateData: any = {};
      if (validatedArgs.key) updateData.key = validatedArgs.key;
      if (validatedArgs.value) updateData.value = validatedArgs.value;
      if (validatedArgs.target) updateData.target = validatedArgs.target;
      if (validatedArgs.type) updateData.type = validatedArgs.type;
      if (validatedArgs.gitBranch) updateData.gitBranch = validatedArgs.gitBranch;
      
      const endpoint = `/v9/projects/${projectId}/env/${envVarId}`;
      const envVar = await makeVercelRequest<VercelEnvironmentVariable>(endpoint, {
        method: 'PATCH',
        body: JSON.stringify(updateData)
      });
      
      return {
        content: [
          {
            type: 'text',
            text: `✅ Environment variable updated successfully!\n\n${formatEnvVar(envVar)}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `❌ Error updating environment variable: ${sanitizeErrorMessage(error)}`
          }
        ]
      };
    }
  }

  private async deleteEnvVar(args: any) {
    const validatedArgs = safeValidateInput(DeleteEnvVarSchema, args) as z.infer<typeof DeleteEnvVarSchema>;
    let projectId = validatedArgs.projectId;
    if (projectId && !projectId.startsWith('prj_')) {
      const projectsResp = await makeVercelRequest<{ projects: VercelProject[] }>(`/v9/projects?limit=20`);
      const found = projectsResp.projects.find(p => p.name === projectId);
      if (found) projectId = found.id;
    }
    if (!projectId) {
      return { content: [{ type: 'text', text: 'Error: Project ID not found for provided value.' }] };
    }
    
    // If envVarId is not a proper ID, try to find it by key name
    let envVarId = validatedArgs.envVarId;
    if (!envVarId.startsWith('env_')) {
      const envVarsResp = await makeVercelRequest<{ envs: VercelEnvironmentVariable[] }>(`/v8/projects/${projectId}/env`);
      const found = envVarsResp.envs.find(env => env.key === envVarId);
      if (found) {
        // Try different possible ID fields
        envVarId = found.id || found.configurationId || found.key;
      }
    }
    if (!envVarId) {
      return { content: [{ type: 'text', text: 'Error: Environment variable ID not found for provided value.' }] };
    }
    
    const endpoint = `/v9/projects/${projectId}/env/${envVarId}`;
    await makeVercelRequest(endpoint, { method: 'DELETE' });
    return {
      content: [
        {
          type: 'text',
          text: `✅ Environment variable ${envVarId} has been deleted.`
        }
      ]
    };
  }

  private async getDeploymentEvents(args: any) {
    const validatedArgs = safeValidateInput(z.object({
      deploymentId: z.string(),
      follow: z.boolean().optional()
    }), args);
    let deploymentId = args.deploymentId;
    if (deploymentId && deploymentId.includes('-')) {
      const deploymentsResp = await makeVercelRequest<{ deployments: VercelDeployment[] }>(`/v6/deployments?limit=20`);
      const found = deploymentsResp.deployments.find(d => d.url === deploymentId || d.alias?.includes(deploymentId));
      if (found) deploymentId = found.uid;
    }
    if (!deploymentId) {
      return { content: [{ type: 'text', text: 'Error: Deployment ID not found for provided value.' }] };
    }
    
    try {
      const queryParams = new URLSearchParams();
      if (args.follow) queryParams.set('follow', 'true');
      
      const endpoint = `/v2/deployments/${deploymentId}/events?${queryParams.toString()}`;
      const response = await makeVercelRequest<any>(endpoint);
      
      let formattedLogs = 'No events available for this deployment';
      
      if (response && (response.data || Array.isArray(response))) {
        const logsData = response.data || response;
        if (Array.isArray(logsData) && logsData.length > 0) {
          formattedLogs = logsData.map(log => {
            let ts = 'N/A';
            try { 
              ts = log.timestamp ? new Date(log.timestamp).toISOString() : 'N/A'; 
            } catch { 
              ts = 'N/A'; 
            }
            const type = log.type ? log.type.toUpperCase() : 'LOG';
            const message = log.message || log.text || '';
            return `[${ts}] ${type}: ${message}`;
          }).join('\n');
        }
      }
      
      return {
        content: [
          {
            type: 'text',
            text: `📋 Deployment Events for ${deploymentId}:\n\n${formattedLogs}`
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `❌ Error fetching deployment events: ${sanitizeErrorMessage(error)}`
          }
        ]
      };
    }
  }

  private async listTeams(args: any) {
    const validatedArgs = safeValidateInput(z.object({
      limit: z.number().optional()
    }), args);
    
    const queryParams = new URLSearchParams();
    if (args.limit) queryParams.set('limit', args.limit.toString());

    const endpoint = `/v10/teams?${queryParams.toString()}`;
    const response = await makeVercelRequest<{ teams: any[] }>(endpoint);

    const formattedTeams = response.teams
      .map(team => `ID: ${team.id}, Name: ${team.name}`)
      .join('\n');

    return {
      content: [
        {
          type: 'text',
          text: `Found ${response.teams.length} teams:\n\n${formattedTeams}`
        }
      ]
    };
  }

  private async searchDeployments(args: any) {
    const validatedArgs = safeValidateInput(z.object({
      query: z.string().optional(),
      projectId: z.string().optional(),
      state: z.enum(['BUILDING', 'ERROR', 'INITIALIZING', 'QUEUED', 'READY', 'CANCELED']).optional(),
      limit: z.number().optional()
    }), args);
    
    const queryParams = new URLSearchParams();
    if (args.query) queryParams.set('q', args.query);
    if (args.projectId) queryParams.set('projectId', args.projectId);
    if (args.state) queryParams.set('state', args.state);
    if (args.limit) queryParams.set('limit', args.limit.toString());

    if (validatedArgs.query) {
      queryParams.set('query', validatedArgs.query);
    }
    const endpoint = `/v6/deployments?${queryParams.toString()}`;
    const response = await makeVercelRequest<{ deployments: VercelDeployment[] }>(endpoint);
 
 
    const formattedDeployments = response.deployments
      .map(deployment => formatDeployment(deployment))
      .join('\n');

    return {
      content: [
        {
          type: 'text',
          text: `Found ${response.deployments.length} deployments matching your query:\n\n${formattedDeployments}`
        }
      ]
    };
  }

  getServer(): Server {
    return this.server;
  }
}

// Function to create and return the MCP server instance
function getVercelMcpServer(): VercelMCPServer {
  return new VercelMCPServer();
}

// Create Express app
const app = express();
app.use(express.json());

// Enable CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, x-api-token, x-team-id');
  
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

//=============================================================================
// HTTP TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

// StreamableHTTP endpoint for MCP protocol
app.post('/mcp', async (req: Request, res: Response) => {
  console.log('Received POST MCP request');
  
  const apiToken = req.headers['x-api-token'] as string || req.headers['authorization']?.replace('Bearer ', '');
  const teamId = req.headers['x-team-id'] as string;
  
  if (!apiToken) {
    res.status(401).json({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'API token is required. Provide it via x-api-token header or Authorization: Bearer header.'
      },
      id: null
    });
    return;
  }

  const server = getVercelMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.getServer().connect(transport);
    asyncLocalStorage.run({ apiToken, teamId }, async () => {
      await transport.handleRequest(req, res, req.body);
    });
    res.on('close', () => {
      console.log('Request closed');
      transport.close();
      server.getServer().close();
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
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport(`/messages`, res);

  // Set up cleanup when connection closes
  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    transports.delete(transport.sessionId);
  });

  transports.set(transport.sessionId, transport);

  const server = getVercelMcpServer();
  await server.getServer().connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    const apiToken = req.headers['x-api-token'] as string || req.headers['authorization']?.replace('Bearer ', '');
    const teamId = req.headers['x-team-id'] as string;

    if (!apiToken) {
      console.error('Error: Vercel API token is missing. Provide it via x-api-token header or Authorization: Bearer header.');
      res.status(401).json({
        error: "API token is required"
      });
      return;
    }

    asyncLocalStorage.run({ apiToken, teamId }, async () => {
      await transport!.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Root endpoint with API info
app.get('/', (req, res) => {
  res.json({
    name: 'vercel_Vercel MCP Server',
    version: '1.0.0',
    description: 'Model Context Protocol server for Vercel deployment management',
    endpoints: {
      '/mcp': 'StreamableHTTP endpoint for direct API calls',
      '/sse': 'Server-Sent Events endpoint for real-time communication',
      '/messages': 'SSE message handling endpoint',
      '/health': 'Health check endpoint'
    },
    authentication: {
      method: 'Bearer token or x-api-token header',
      description: 'Provide your Vercel API token via Authorization: Bearer header or x-api-token header'
    }
  });
});

const PORT = parseInt(process.env.PORT || '5000', 10);

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Vercel MCP Server running on port ${PORT}`);
  console.log(`Available endpoints:`);
  console.log(`  HTTP: http://0.0.0.0:${PORT}/mcp`);
  console.log(`  SSE: http://0.0.0.0:${PORT}/sse`);
  console.log(`  Health: http://0.0.0.0:${PORT}/health`);
});

export { VercelMCPServer, asyncLocalStorage };

