import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * List all teams
 */
const LIST_TEAMS_TOOL: Tool = {
  name: 'intercom_list_teams',
  description: 'List all teams in your Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
};

/**
 * Get a specific team by ID
 */
const GET_TEAM_TOOL: Tool = {
  name: 'intercom_get_team',
  description:
    'Retrieve a specific team by its ID, containing an array of admins that belong to this team.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier of a given team',
        example: '123',
      },
    },
    required: ['id'],
  },
};

/**
 * List all admins
 */
const LIST_ADMINS_TOOL: Tool = {
  name: 'intercom_list_admins',
  description: 'List all admins (teammates) in your Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
};

/**
 * Get a specific admin by ID
 */
const GET_ADMIN_TOOL: Tool = {
  name: 'intercom_get_admin',
  description: 'Retrieve the details of a single admin (teammate).',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The unique identifier of a given admin',
        example: 123,
      },
    },
    required: ['id'],
  },
};

/**
 * Get current admin (me)
 */
const GET_CURRENT_ADMIN_TOOL: Tool = {
  name: 'intercom_get_current_admin',
  description:
    'Identify the currently authorized admin along with the embedded app object (workspace).',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
};

/**
 * Set admin away status
 */
const SET_ADMIN_AWAY_TOOL: Tool = {
  name: 'intercom_set_admin_away',
  description: 'Set an admin as away for the Inbox, with options for reassigning conversations.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The unique identifier of a given admin',
        example: 123,
      },
      away_mode_enabled: {
        type: 'boolean',
        description: 'Set to true to change the status of the admin to away',
        example: true,
        default: true,
      },
      away_mode_reassign: {
        type: 'boolean',
        description: 'Set to true to assign any new conversation replies to your default inbox',
        example: false,
        default: false,
      },
    },
    required: ['id', 'away_mode_enabled', 'away_mode_reassign'],
  },
};

/**
 * List admin activity logs
 */
const LIST_ADMIN_ACTIVITY_LOGS_TOOL: Tool = {
  name: 'intercom_list_admin_activity_logs',
  description: 'Get a log of activities by all admins in an app within a specified timeframe.',
  inputSchema: {
    type: 'object',
    properties: {
      created_at_after: {
        type: 'string',
        description:
          'The start date that you request data for. It must be formatted as a UNIX timestamp.',
        example: '1677253093',
      },
      created_at_before: {
        type: 'string',
        description:
          'The end date that you request data for. It must be formatted as a UNIX timestamp.',
        example: '1677861493',
      },
    },
    required: ['created_at_after'],
  },
};

export const TEAM_TOOLS = [
  LIST_TEAMS_TOOL,
  GET_TEAM_TOOL,
  LIST_ADMINS_TOOL,
  GET_ADMIN_TOOL,
  GET_CURRENT_ADMIN_TOOL,
  SET_ADMIN_AWAY_TOOL,
  LIST_ADMIN_ACTIVITY_LOGS_TOOL,
] as const;
