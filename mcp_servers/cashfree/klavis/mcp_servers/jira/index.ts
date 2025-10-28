#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequest,
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from 'zod';
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';
import fetch, { RequestInit } from 'node-fetch';

// Load environment variables
dotenv.config();

// Default fields for Jira reads
const DEFAULT_READ_JIRA_FIELDS = [
  "summary",
  "status",
  "assignee",
  "issuetype",
  "priority",
  "created",
  "updated",
  "description",
  "labels"
];

// Define interfaces for Jira API client
interface JiraClient {
  baseUrl: string;
  cloudId: string;
  authToken: string;
  fetch: <T>(path: string, options?: RequestInit) => Promise<T>;
}

// Type definitions for tool arguments
interface SearchIssuesArgs {
  jql: string;
  maxResults?: number;
  fields?: string[];
}

interface CreateIssueArgs {
  projectKey: string;
  issueType: string;
  summary: string;
  description: string;
  priority?: string;
  assignee?: string;
  labels?: string[];
  components?: string[];
  customFields?: Record<string, any>;
}

interface GetIssueArgs {
  issueKey: string;
  fields?: string[];
}

interface UpdateIssueArgs {
  issueKey: string;
  summary?: string;
  description?: string;
  status?: string;
  priority?: string;
  assignee?: string;
  labels?: string[];
  customFields?: Record<string, any>;
}

interface AddCommentArgs {
  issueKey: string;
  comment: string;
}

// Type definitions for tool arguments
interface JiraGetIssueArgs {
  issue_key: string;
  fields?: string;
  expand?: string;
  comment_limit?: number;
  properties?: string;
  update_history?: boolean;
}

interface JiraSearchArgs {
  jql: string;
  fields?: string;
  limit?: number;
  startAt?: number;
  projects_filter?: string;
}

interface JiraSearchFieldsArgs {
  keyword?: string;
  limit?: number;
  refresh?: boolean;
}

interface JiraGetProjectIssuesArgs {
  project_key: string;
  limit?: number;
  startAt?: number;
}

interface JiraGetEpicIssuesArgs {
  epic_key: string;
  limit?: number;
  startAt?: number;
}

interface JiraGetSprintsFromBoardArgs {
  board_id: string;
  state?: string;
  startAt?: number;
  limit?: number;
}

interface JiraCreateSprintArgs {
  board_id: string;
  sprint_name: string;
  start_date: string;
  end_date: string;
  goal?: string;
}

interface JiraGetSprintIssuesArgs {
  sprint_id: string;
  fields?: string;
  startAt?: number;
  limit?: number;
}

interface JiraUpdateSprintArgs {
  sprint_id: string;
  sprint_name?: string;
  state?: string;
  start_date?: string;
  end_date?: string;
  goal?: string;
}

interface JiraCreateIssueArgs {
  project_key: string;
  summary: string;
  issue_type: string;
  assignee?: string;
  description?: string;
  components?: string;
  additional_fields?: string;
}

interface JiraUpdateIssueArgs {
  issue_key: string;
  fields: string;
  additional_fields?: string;
  attachments?: string;
}

interface JiraDeleteIssueArgs {
  issue_key: string;
}

interface JiraAddCommentArgs {
  issue_key: string;
  comment: string;
}

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  authToken: string;
}>();

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
    console.error('Error: Jira access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
    return '';
  }

  const authDataJson = JSON.parse(authData);
  return authDataJson.access_token ?? '';
}

// Helper function to get Jira client from async local storage
async function getJiraClient(): Promise<JiraClient> {
  const store = asyncLocalStorage.getStore();
  if (!store) {
    throw new Error('Auth token not found in AsyncLocalStorage');
  }
  return await createJiraClient(store.authToken);
}

// Create a Jira API client
async function createJiraClient(authToken: string): Promise<JiraClient> {
  // First, fetch the accessible resources to get the correct baseUrl
  const accessibleResourcesUrl = 'https://api.atlassian.com/oauth/token/accessible-resources';

  try {
    const response = await fetch(accessibleResourcesUrl, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch accessible resources (${response.status}): ${errorText}`);
    }

    // Define the type for the resources
    interface JiraResource {
      id: string;
      name: string;
      url: string;
      scopes: string[];
      avatarUrl: string;
    }

    const resources = await response.json() as JiraResource[];

    // If no resources are found, throw an error
    if (!resources || resources.length === 0) {
      throw new Error('No accessible Jira resources found for this user');
    }

    // Use the first resource's cloud ID
    const cloudId = resources[0].id;
    // Store the site URL as well for reference
    const siteUrl = resources[0].url;

    return {
      baseUrl: siteUrl,
      cloudId,
      authToken,
      async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
        // Construct URL using the proper format
        const url = path.startsWith('http')
          ? path
          : `https://api.atlassian.com/ex/jira/${cloudId}${path.startsWith('/') ? path : '/' + path}`;

        const headers: Record<string, string> = {
          ...options.headers as Record<string, string>,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${authToken}`
        };

        const response = await fetch(url, {
          ...options,
          headers,
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Jira API error (${response.status}): ${errorText}`);
        }

        // Handle 204 No Content responses
        if (response.status === 204) {
          return {} as T;
        }

        return response.json() as Promise<T>;
      },
    };
  } catch (error) {
    console.error('Error creating Jira client:', error);
    throw error;
  }
}

// Tool definitions
const searchIssuesTool: Tool = {
  name: "jira_search_issues",
  description: "Search for Jira issues using JQL",
  inputSchema: {
    type: "object",
    properties: {
      jql: {
        type: "string",
        description: "JQL query string to search for issues",
      },
      maxResults: {
        type: "number",
        description: "Maximum number of results to return (default: 20)",
      },
      fields: {
        type: "array",
        items: {
          type: "string",
        },
        description: "Fields to include in the response",
      },
    },
    required: ["jql"],
  },
  annotations: {
    category: "JIRA_ISSUE",
    readOnlyHint: true,
  },
};

const createIssueTool: Tool = {
  name: "jira_create_issue",
  description: "Create a new Jira issue with optional Epic link or parent for subtasks",
  inputSchema: {
    type: "object",
    properties: {
      project_key: {
        type: "string",
        description: "The JIRA project key (e.g. 'PROJ', 'DEV', 'SUPPORT'). This is the prefix of issue keys in your project. Never assume what it might be, always ask the user.",
      },
      summary: {
        type: "string",
        description: "Summary/title of the issue",
      },
      issue_type: {
        type: "string",
        description: "Issue type (e.g. 'Task', 'Bug', 'Story', 'Epic', 'Subtask'). The available types depend on your project configuration. For subtasks, use 'Subtask' (not 'Sub-task') and include parent in additional_fields.",
      },
      assignee: {
        type: "string",
        description: "Assignee of the ticket (accountID, full name or e-mail)",
      },
      description: {
        type: "string",
        description: "Issue description",
        default: "",
      },
      components: {
        type: "string",
        description: "Comma-separated list of component names to assign (e.g., 'Frontend,API')",
        default: "",
      },
      additional_fields: {
        type: "string",
        description: "Optional JSON string of additional fields to set. Examples:\n"
          + '- Set priority: {"priority": {"name": "High"}}\n'
          + '- Add labels: {"labels": ["frontend", "urgent"]}\n'
          + '- Link to parent (for any issue type): {"parent": "PROJ-123"}\n'
          + '- Set Fix Version/s: {"fixVersions": [{"id": "10020"}]}\n'
          + '- Custom fields: {"customfield_10010": "value"}',
        default: "{}",
      },
    },
    required: ["project_key", "summary", "issue_type"],
  },
  annotations: {
    category: "JIRA_ISSUE",
  },
};

const getIssueTool: Tool = {
  name: "jira_get_issue",
  description: "Get details of a specific Jira issue including its Epic links and relationship information",
  inputSchema: {
    type: "object",
    properties: {
      issue_key: {
        type: "string",
        description: "Jira issue key (e.g., 'PROJ-123')",
      },
      fields: {
        type: "string",
        description: "Fields to return. Can be a comma-separated list (e.g., 'summary,status,customfield_10010'), '*all' for all fields (including custom fields), or omitted for essential fields only",
        default: DEFAULT_READ_JIRA_FIELDS.join(","),
      },
      expand: {
        type: "string",
        description: "Optional fields to expand. Examples: 'renderedFields' (for rendered content), 'transitions' (for available status transitions), 'changelog' (for history)",
      },
      comment_limit: {
        type: "integer",
        description: "Maximum number of comments to include (0 or null for no comments)",
        minimum: 0,
        maximum: 100,
        default: 10,
      },
      properties: {
        type: "string",
        description: "A comma-separated list of issue properties to return",
      },
      update_history: {
        type: "boolean",
        description: "Whether to update the issue view history for the requesting user",
        default: true,
      },
    },
    required: ["issue_key"],
  },
  annotations: {
    category: "JIRA_ISSUE",
    readOnlyHint: true,
  },
};

const updateIssueTool: Tool = {
  name: "jira_update_issue",
  description: "Update an existing Jira issue including changing status, adding Epic links, updating fields, etc.",
  inputSchema: {
    type: "object",
    properties: {
      issue_key: {
        type: "string",
        description: "Jira issue key (e.g., 'PROJ-123')",
      },
      fields: {
        type: "string",
        description: "A valid JSON object of fields to update as a string. Example: '{\"summary\": \"New title\", \"description\": \"Updated description\", \"priority\": {\"name\": \"High\"}, \"assignee\": \"john.doe\"}'",
      },
      additional_fields: {
        type: "string",
        description: "Optional JSON string of additional fields to update. Use this for custom fields or more complex updates.",
        default: "{}",
      },
      attachments: {
        type: "string",
        description: "Optional JSON string or comma-separated list of file paths to attach to the issue. Example: \"/path/to/file1.txt,/path/to/file2.txt\" or \"[\"/path/to/file1.txt\",\"/path/to/file2.txt\"]\"",
      },
    },
    required: ["issue_key", "fields"],
  },
  annotations: {
    category: "JIRA_ISSUE",
  },
};

const addCommentTool: Tool = {
  name: "jira_add_comment",
  description: "Add a comment to a Jira issue",
  inputSchema: {
    type: "object",
    properties: {
      issue_key: {
        type: "string",
        description: "Jira issue key (e.g., 'PROJ-123')",
      },
      comment: {
        type: "string",
        description: "Comment text in Markdown format",
      },
    },
    required: ["issue_key", "comment"],
  },
  annotations: {
    category: "JIRA_COMMENT",
  },
};

const searchTool: Tool = {
  name: "jira_search",
  description: "Search Jira issues using JQL (Jira Query Language)",
  inputSchema: {
    type: "object",
    properties: {
      jql: {
        type: "string",
        description: "JQL query string (Jira Query Language). Examples:\n"
          + '- Find Epics: "issuetype = Epic AND project = PROJ"\n'
          + '- Find issues in Epic: "parent = PROJ-123"\n'
          + "- Find by status: \"status = 'In Progress' AND project = PROJ\"\n"
          + '- Find by assignee: "assignee = currentUser()"\n'
          + '- Find recently updated: "updated >= -7d AND project = PROJ"\n'
          + '- Find by label: "labels = frontend AND project = PROJ"\n'
          + '- Find by priority: "priority = High AND project = PROJ"',
      },
      fields: {
        type: "string",
        description: "Comma-separated fields to return in the results. Use '*all' for all fields, or specify individual fields like 'summary,status,assignee,priority'",
        default: DEFAULT_READ_JIRA_FIELDS.join(","),
      },
      limit: {
        type: "number",
        description: "Maximum number of results (1-50)",
        default: 10,
        minimum: 1,
        maximum: 50,
      },
      startAt: {
        type: "number",
        description: "Starting index for pagination (0-based)",
        default: 0,
        minimum: 0,
      },
      projects_filter: {
        type: "string",
        description: "Comma-separated list of project keys to filter results by. Overrides the environment variable JIRA_PROJECTS_FILTER if provided.",
      },
    },
    required: ["jql"],
  },
  annotations: {
    category: "JIRA_SEARCH",
    readOnlyHint: true,
  },
};

const searchFieldsTool: Tool = {
  name: "jira_search_fields",
  description: "Search Jira fields by keyword with fuzzy match",
  inputSchema: {
    type: "object",
    properties: {
      keyword: {
        type: "string",
        description: "Keyword for fuzzy search. If left empty, lists the first 'limit' available fields in their default order.",
        default: "",
      },
      limit: {
        type: "number",
        description: "Maximum number of results",
        default: 10,
        minimum: 1,
      },
      refresh: {
        type: "boolean",
        description: "Whether to force refresh the field list",
        default: false,
      },
    },
    required: [],
  },
  annotations: {
    category: "JIRA_FIELD",
    readOnlyHint: true,
  },
};

const getProjectIssuesTool: Tool = {
  name: "jira_get_project_issues",
  description: "Get all issues for a specific Jira project",
  inputSchema: {
    type: "object",
    properties: {
      project_key: {
        type: "string",
        description: "The project key",
      },
      limit: {
        type: "number",
        description: "Maximum number of results (1-50)",
        default: 10,
        minimum: 1,
        maximum: 50,
      },
      startAt: {
        type: "number",
        description: "Starting index for pagination (0-based)",
        default: 0,
        minimum: 0,
      },
    },
    required: ["project_key"],
  },
  annotations: {
    category: "JIRA_PROJECT",
    readOnlyHint: true,
  },
};

const getEpicIssuesTool: Tool = {
  name: "jira_get_epic_issues",
  description: "Get all issues linked to a specific epic",
  inputSchema: {
    type: "object",
    properties: {
      epic_key: {
        type: "string",
        description: "The key of the epic (e.g., 'PROJ-123')",
      },
      limit: {
        type: "number",
        description: "Maximum number of issues to return (1-50)",
        default: 10,
        minimum: 1,
        maximum: 50,
      },
      startAt: {
        type: "number",
        description: "Starting index for pagination (0-based)",
        default: 0,
        minimum: 0,
      },
    },
    required: ["epic_key"],
  },
  annotations: {
    category: "JIRA_ISSUE",
    readOnlyHint: true,
  },
};

const getSprintsFromBoardTool: Tool = {
  name: "jira_get_sprints_from_board",
  description: "Get jira sprints from board by state",
  inputSchema: {
    type: "object",
    properties: {
      board_id: {
        type: "string",
        description: "The id of board (e.g., '1000')",
      },
      state: {
        type: "string",
        description: "Sprint state (e.g., 'active', 'future', 'closed')",
      },
      startAt: {
        type: "number",
        description: "Starting index for pagination (0-based)",
        default: 0,
      },
      limit: {
        type: "number",
        description: "Maximum number of results (1-50)",
        default: 10,
        minimum: 1,
        maximum: 50,
      },
    },
  },
  annotations: {
    category: "JIRA_SPRINT",
    readOnlyHint: true,
  },
};

const createSprintTool: Tool = {
  name: "jira_create_sprint",
  description: "Create Jira sprint for a board",
  inputSchema: {
    type: "object",
    properties: {
      board_id: {
        type: "string",
        description: "The id of board (e.g., '1000')",
      },
      sprint_name: {
        type: "string",
        description: "Name of the sprint (e.g., 'Sprint 1')",
      },
      start_date: {
        type: "string",
        description: "Start time for sprint (ISO 8601 format)",
      },
      end_date: {
        type: "string",
        description: "End time for sprint (ISO 8601 format)",
      },
      goal: {
        type: "string",
        description: "Goal of the sprint",
      },
    },
    required: [
      "board_id",
      "sprint_name",
      "start_date",
      "end_date",
    ],
  },
  annotations: {
    category: "JIRA_SPRINT",
  },
};

const getSprintIssuesTool: Tool = {
  name: "jira_get_sprint_issues",
  description: "Get jira issues from sprint",
  inputSchema: {
    type: "object",
    properties: {
      sprint_id: {
        type: "string",
        description: "The id of sprint (e.g., '10001')",
      },
      fields: {
        type: "string",
        description: "Comma-separated fields to return in the results. Use '*all' for all fields, or specify individual fields like 'summary,status,assignee,priority'",
        default: DEFAULT_READ_JIRA_FIELDS.join(","),
      },
      startAt: {
        type: "number",
        description: "Starting index for pagination (0-based)",
        default: 0,
      },
      limit: {
        type: "number",
        description: "Maximum number of results (1-50)",
        default: 10,
        minimum: 1,
        maximum: 50,
      },
    },
    required: ["sprint_id"],
  },
  annotations: {
    category: "JIRA_SPRINT",
    readOnlyHint: true,
  },
};

const updateSprintTool: Tool = {
  name: "jira_update_sprint",
  description: "Update jira sprint",
  inputSchema: {
    type: "object",
    properties: {
      sprint_id: {
        type: "string",
        description: "The id of sprint (e.g., '10001')",
      },
      sprint_name: {
        type: "string",
        description: "Optional: New name for the sprint",
      },
      state: {
        type: "string",
        description: "Optional: New state for the sprint (future|active|closed)",
      },
      start_date: {
        type: "string",
        description: "Optional: New start date for the sprint",
      },
      end_date: {
        type: "string",
        description: "Optional: New end date for the sprint",
      },
      goal: {
        type: "string",
        description: "Optional: New goal for the sprint",
      },
    },
    required: ["sprint_id"],
  },
  annotations: {
    category: "JIRA_SPRINT",
  },
};

const deleteIssueTool: Tool = {
  name: "jira_delete_issue",
  description: "Delete an existing Jira issue",
  inputSchema: {
    type: "object",
    properties: {
      issue_key: {
        type: "string",
        description: "Jira issue key (e.g. PROJ-123)",
      },
    },
    required: ["issue_key"],
  },
  annotations: {
    category: "JIRA_ISSUE",
  },
};

const getLinkTypesTool: Tool = {
  name: "jira_get_link_types",
  description: "Get all available issue link types",
  inputSchema: {
    type: "object",
    properties: {},
    required: [],
  },
  annotations: {
    category: "JIRA_LINK",
    readOnlyHint: true,
  },
};

const getJiraMcpServer = () => {
  const server = new Server(
    {
      name: "jira-service",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(
    ListToolsRequestSchema,
    async () => {
      return {
        tools: [
          searchTool,
          getIssueTool,
          searchFieldsTool,
          getProjectIssuesTool,
          getEpicIssuesTool,
          getSprintsFromBoardTool,
          createSprintTool,
          getSprintIssuesTool,
          updateSprintTool,
          createIssueTool,
          updateIssueTool,
          deleteIssueTool,
          addCommentTool,
          getLinkTypesTool,
        ],
      };
    }
  );

  server.setRequestHandler(
    CallToolRequestSchema,
    async (request: CallToolRequest) => {
      try {
        // Validate the request parameters
        if (!request.params?.name) {
          throw new Error("Missing tool name");
        }

        const jira = await getJiraClient();

        // Process the tool call based on the tool name
        switch (request.params.name) {
          case "jira_search": {
            const args = request.params.arguments as unknown as JiraSearchArgs;
            if (!args.jql) {
              throw new Error("Missing required argument: jql");
            }

            const searchParams = new URLSearchParams();
            searchParams.append('jql', args.jql);

            if (args.limit) {
              searchParams.append('maxResults', String(args.limit));
            } else {
              searchParams.append('maxResults', "10");
            }

            if (args.startAt !== undefined) {
              searchParams.append('startAt', String(args.startAt));
            }

            if (args.fields) {
              if (args.fields === "*all") {
                searchParams.append('fields', "*all");
              } else {
                searchParams.append('fields', args.fields);
              }
            } else {
              searchParams.append('fields', DEFAULT_READ_JIRA_FIELDS.join(','));
            }

            // Filter by project if specified
            const projectsFilter = args.projects_filter || process.env.JIRA_PROJECTS_FILTER;
            if (projectsFilter && !args.jql.toLowerCase().includes("project =")) {
              const projects = projectsFilter.split(',').map(p => p.trim());
              let projectCondition = "";

              if (projects.length === 1) {
                projectCondition = `project = ${projects[0]}`;
              } else if (projects.length > 1) {
                projectCondition = `project in (${projects.join(',')})`;
              }

              if (projectCondition) {
                args.jql = `${args.jql} AND ${projectCondition}`;
                searchParams.set('jql', args.jql);
              }
            }

            const response = await jira.fetch<any>(`/rest/api/3/search?${searchParams.toString()}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_get_issue": {
            const args = request.params.arguments as unknown as JiraGetIssueArgs;
            if (!args.issue_key) {
              throw new Error("Missing required argument: issue_key");
            }

            const searchParams = new URLSearchParams();

            if (args.fields) {
              if (args.fields === "*all") {
                searchParams.append('fields', "*all");
              } else {
                searchParams.append('fields', args.fields);
              }
            } else {
              searchParams.append('fields', DEFAULT_READ_JIRA_FIELDS.join(','));
            }

            if (args.expand) {
              searchParams.append('expand', args.expand);
            }

            if (args.properties) {
              searchParams.append('properties', args.properties);
            }

            if (args.update_history !== undefined) {
              searchParams.append('updateHistory', String(args.update_history));
            }

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await jira.fetch<any>(`/rest/api/3/issue/${args.issue_key}${query}`);

            // Get comments if comment_limit > 0
            if (args.comment_limit && args.comment_limit > 0) {
              const commentsParams = new URLSearchParams();
              commentsParams.append('maxResults', String(args.comment_limit));
              commentsParams.append('orderBy', 'created');

              const commentsResponse = await jira.fetch<any>(
                `/rest/api/3/issue/${args.issue_key}/comment?${commentsParams.toString()}`
              );

              response.comments = commentsResponse.comments;
            }

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_search_fields": {
            const args = request.params.arguments as unknown as JiraSearchFieldsArgs;

            // Get all fields
            const response = await jira.fetch<any>('/rest/api/3/field');

            // Filter and sort by keyword if provided
            let filteredFields = response;
            if (args.keyword && args.keyword.trim() !== '') {
              const keyword = args.keyword.toLowerCase();
              filteredFields = response.filter((field: any) => {
                const name = (field.name || '').toLowerCase();
                const id = (field.id || '').toLowerCase();
                const desc = (field.description || '').toLowerCase();

                return name.includes(keyword) || id.includes(keyword) || desc.includes(keyword);
              });
            }

            // Limit results
            const limit = args.limit || 10;
            const limitedFields = filteredFields.slice(0, limit);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(limitedFields),
                },
              ],
            };
          }

          case "jira_get_project_issues": {
            const args = request.params.arguments as unknown as JiraGetProjectIssuesArgs;
            if (!args.project_key) {
              throw new Error("Missing required argument: project_key");
            }

            // Use JQL to search for project issues
            const jql = `project = ${args.project_key}`;
            const searchParams = new URLSearchParams();
            searchParams.append('jql', jql);
            searchParams.append('maxResults', String(args.limit || 10));
            searchParams.append('startAt', String(args.startAt || 0));
            searchParams.append('fields', DEFAULT_READ_JIRA_FIELDS.join(','));

            const response = await jira.fetch<any>(`/rest/api/3/search?${searchParams.toString()}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_get_epic_issues": {
            const args = request.params.arguments as unknown as JiraGetEpicIssuesArgs;
            if (!args.epic_key) {
              throw new Error("Missing required argument: epic_key");
            }

            // First get the Epic to confirm it exists and is of type Epic
            const epicResponse = await jira.fetch<any>(`/rest/api/3/issue/${args.epic_key}?fields=issuetype`);

            if (epicResponse.fields.issuetype.name !== 'Epic') {
              throw new Error(`Issue ${args.epic_key} is not an Epic`);
            }

            // Use JQL to search for issues in the Epic
            const jql = `"Epic Link" = ${args.epic_key} OR parent = ${args.epic_key}`;
            const searchParams = new URLSearchParams();
            searchParams.append('jql', jql);
            searchParams.append('maxResults', String(args.limit || 10));
            searchParams.append('startAt', String(args.startAt || 0));
            searchParams.append('fields', DEFAULT_READ_JIRA_FIELDS.join(','));

            const response = await jira.fetch<any>(`/rest/api/3/search?${searchParams.toString()}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_get_sprints_from_board": {
            const args = request.params.arguments as unknown as JiraGetSprintsFromBoardArgs;
            if (!args.board_id) {
              throw new Error("Missing required argument: board_id");
            }

            const searchParams = new URLSearchParams();

            if (args.state) {
              searchParams.append('state', args.state);
            }

            searchParams.append('maxResults', String(args.limit || 10));
            searchParams.append('startAt', String(args.startAt || 0));

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await jira.fetch<any>(`/rest/agile/1.0/board/${args.board_id}/sprint${query}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_create_sprint": {
            const args = request.params.arguments as unknown as JiraCreateSprintArgs;
            if (!args.board_id || !args.sprint_name || !args.start_date || !args.end_date) {
              throw new Error("Missing required arguments for sprint creation");
            }

            const payload = {
              name: args.sprint_name,
              startDate: args.start_date,
              endDate: args.end_date,
              originBoardId: args.board_id,
            };

            if (args.goal) {
              Object.assign(payload, { goal: args.goal });
            }

            const response = await jira.fetch<any>('/rest/agile/1.0/sprint', {
              method: 'POST',
              body: JSON.stringify(payload),
            });

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_get_sprint_issues": {
            const args = request.params.arguments as unknown as JiraGetSprintIssuesArgs;
            if (!args.sprint_id) {
              throw new Error("Missing required argument: sprint_id");
            }

            const searchParams = new URLSearchParams();

            if (args.fields) {
              if (args.fields === "*all") {
                searchParams.append('fields', "*all");
              } else {
                searchParams.append('fields', args.fields);
              }
            } else {
              searchParams.append('fields', DEFAULT_READ_JIRA_FIELDS.join(','));
            }

            searchParams.append('maxResults', String(args.limit || 10));
            searchParams.append('startAt', String(args.startAt || 0));

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await jira.fetch<any>(`/rest/agile/1.0/sprint/${args.sprint_id}/issue${query}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_update_sprint": {
            const args = request.params.arguments as unknown as JiraUpdateSprintArgs;
            if (!args.sprint_id) {
              throw new Error("Missing required argument: sprint_id");
            }

            const payload: any = {};

            if (args.sprint_name) payload.name = args.sprint_name;
            if (args.goal) payload.goal = args.goal;
            if (args.start_date) payload.startDate = args.start_date;
            if (args.end_date) payload.endDate = args.end_date;
            if (args.state) payload.state = args.state;

            if (Object.keys(payload).length === 0) {
              throw new Error("At least one field must be provided to update");
            }

            const response = await jira.fetch<any>(`/rest/agile/1.0/sprint/${args.sprint_id}`, {
              method: 'PUT',
              body: JSON.stringify(payload),
            });

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_create_issue": {
            const args = request.params.arguments as unknown as JiraCreateIssueArgs;
            if (!args.project_key || !args.issue_type || !args.summary) {
              throw new Error("Missing required arguments for issue creation");
            }

            // Construct issue creation payload
            const payload: any = {
              fields: {
                project: {
                  key: args.project_key,
                },
                issuetype: {
                  name: args.issue_type,
                },
                summary: args.summary,
              },
            };

            // Add description if provided
            if (args.description) {
              payload.fields.description = {
                type: "doc",
                version: 1,
                content: [
                  {
                    type: "paragraph",
                    content: [
                      {
                        type: "text",
                        text: args.description,
                      },
                    ],
                  },
                ],
              };
            }

            // Add assignee if provided
            if (args.assignee) {
              if (args.assignee.toLowerCase() === 'currentuser()') {
                try {
                  const currentUser = await jira.fetch<any>('/rest/api/3/myself');
                  if (currentUser && currentUser.accountId) {
                    payload.fields.assignee = { accountId: currentUser.accountId };
                  } else {
                    throw new Error("Failed to fetch current user's accountId for assignee.");
                  }
                } catch (e) {
                  throw new Error(`Error resolving currentUser for assignee: ${(e as Error).message}`);
                }
              } else if (args.assignee.includes('@')) {
                payload.fields.assignee = { emailAddress: args.assignee };
              } else if (args.assignee.startsWith('user:') || args.assignee.length > 20) { // Heuristic for accountId
                payload.fields.assignee = { accountId: args.assignee };
              } else {
                payload.fields.assignee = { name: args.assignee };
              }
            }

            // Add components if provided
            if (args.components) {
              const componentNames = args.components.split(',').map(c => c.trim());
              payload.fields.components = componentNames.map(name => ({ name }));
            }

            // Add additional fields if provided
            if (args.additional_fields) {
              try {
                const additionalFields = JSON.parse(args.additional_fields);
                Object.entries(additionalFields).forEach(([key, value]) => {
                  payload.fields[key] = value;
                });
              } catch (e) {
                throw new Error(`Invalid JSON in additional_fields: ${(e as Error).message}`);
              }
            }

            const response = await jira.fetch<any>('/rest/api/3/issue', {
              method: 'POST',
              body: JSON.stringify(payload),
            });

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_update_issue": {
            const args = request.params.arguments as unknown as JiraUpdateIssueArgs;
            if (!args.issue_key || !args.fields) {
              throw new Error("Missing required arguments: issue_key and fields");
            }

            let fieldsObj: any = {};
            try {
              fieldsObj = JSON.parse(args.fields);
            } catch (e) {
              throw new Error(`Invalid JSON in fields: ${(e as Error).message}`);
            }

            // Resolve currentUser() for assignee
            if (fieldsObj.assignee) {
              let assigneeValue = fieldsObj.assignee;

              // Check if assignee is provided as a string "currentUser()"
              // or as an object like { "id": "currentUser()" } or { "name": "currentUser()" }
              if (
                (typeof assigneeValue === 'string' && assigneeValue.toLowerCase() === 'currentuser()') ||
                (typeof assigneeValue === 'object' && assigneeValue !== null &&
                  (String(assigneeValue.id).toLowerCase() === 'currentuser()' || String(assigneeValue.name).toLowerCase() === 'currentuser()')
                )
              ) {
                try {
                  const currentUser = await jira.fetch<any>('/rest/api/3/myself');
                  if (currentUser && currentUser.accountId) {
                    fieldsObj.assignee = { accountId: currentUser.accountId };
                  } else {
                    throw new Error("Failed to fetch current user's accountId.");
                  }
                } catch (e) {
                  throw new Error(`Error resolving currentUser for assignee: ${(e as Error).message}`);
                }
              }
            }

            // Construct issue update payload
            const payload: any = {
              fields: fieldsObj,
            };

            // Add additional fields if provided
            if (args.additional_fields) {
              try {
                const additionalFields = JSON.parse(args.additional_fields);
                Object.entries(additionalFields).forEach(([key, value]) => {
                  payload.fields[key] = value;
                });
              } catch (e) {
                throw new Error(`Invalid JSON in additional_fields: ${(e as Error).message}`);
              }
            }

            // Format description if provided
            if (payload.fields.description && typeof payload.fields.description === 'string') {
              payload.fields.description = {
                type: "doc",
                version: 1,
                content: [
                  {
                    type: "paragraph",
                    content: [
                      {
                        type: "text",
                        text: payload.fields.description,
                      },
                    ],
                  },
                ],
              };
            }

            // Only send request if there are fields to update
            let responseText = "";
            if (Object.keys(payload.fields).length > 0) {
              const response = await jira.fetch<any>(`/rest/api/3/issue/${args.issue_key}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
              });

              responseText = JSON.stringify(response);
            }

            // Get updated issue to return in response
            const updatedIssue = await jira.fetch<any>(`/rest/api/3/issue/${args.issue_key}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(updatedIssue),
                },
              ],
            };
          }

          case "jira_delete_issue": {
            const args = request.params.arguments as unknown as JiraDeleteIssueArgs;
            if (!args.issue_key) {
              throw new Error("Missing required argument: issue_key");
            }

            const response = await jira.fetch<any>(`/rest/api/3/issue/${args.issue_key}`, {
              method: 'DELETE'
            });

            // Note: Jira DELETE issue often returns 204 No Content on success.
            // If the response is empty or undefined, return a success message.
            // Otherwise, return the actual response.
            const responseText = response ? JSON.stringify(response) : JSON.stringify({ message: `Issue ${args.issue_key} deleted successfully (status 204)` });

            return {
              content: [
                {
                  type: "text",
                  text: responseText,
                },
              ],
            };
          }

          case "jira_add_comment": {
            const args = request.params.arguments as unknown as JiraAddCommentArgs;
            if (!args.issue_key || !args.comment) {
              throw new Error("Missing required arguments: issue_key and comment");
            }

            const payload = {
              body: {
                type: "doc",
                version: 1,
                content: [
                  {
                    type: "paragraph",
                    content: [
                      {
                        type: "text",
                        text: args.comment,
                      },
                    ],
                  },
                ],
              },
            };

            const response = await jira.fetch<any>(`/rest/api/3/issue/${args.issue_key}/comment`, {
              method: 'POST',
              body: JSON.stringify(payload),
            });

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "jira_get_link_types": {
            const response = await jira.fetch<any>('/rest/api/3/issueLinkType');

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          default:
            throw new Error(`Unknown tool: ${request.params.name}`);
        }
      } catch (error) {
        console.error("Error executing tool:", error);

        if (error instanceof z.ZodError) {
          throw new Error(`Invalid input: ${JSON.stringify(error.errors)}`);
        }

        throw error;
      }
    }
  );

  return server;
};

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const authToken = extractAccessToken(req);

  const server = getJiraMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ authToken }, async () => {
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
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport(`/messages`, res);

  // Set up cleanup when connection closes
  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    transports.delete(transport.sessionId);
  });

  transports.set(transport.sessionId, transport);

  const server = getJiraMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    const authToken = extractAccessToken(req);

    asyncLocalStorage.run({ authToken }, async () => {
      await transport!.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Jira MCP Server running on port ${PORT}`);
}); 