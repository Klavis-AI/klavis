import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Create a new Miro board with a specified name and optional description.
 */
const CREATE_BOARD_TOOL: Tool = {
  name: 'miro_create_board',
  description: 'Create a new Miro board with a specified name and optional description.',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: 'Name of the board to create',
      },
      description: {
        type: 'string',
        description: 'Optional description for the board',
      },
      access: {
        type: 'string',
        description: 'Board access level',
        enum: ['private', 'view', 'comment', 'edit'],
        default: 'private',
      },
      teamId: {
        type: 'string',
        description: 'Optional team ID to create the board under',
      },
      projectId: {
        type: 'string',
        description: 'Optional project ID to create the board under',
      },
    },
    required: ['name'],
  },
};

/**
 * Get a list of all boards accessible to the user.
 */
const LIST_BOARDS_TOOL: Tool = {
  name: 'miro_list_boards',
  description: 'Get a list of all boards accessible to the user.',
  inputSchema: {
    type: 'object',
    properties: {
      limit: {
        type: 'number',
        description: 'Maximum number of boards to return (default: 25, max: 100)',
        default: 25,
        minimum: 1,
        maximum: 100,
      },
      teamId: {
        type: 'string',
        description: 'Filter boards by team ID',
      },
    },
  },
};

/**
 * Get detailed information about a specific board including metadata and settings.
 */
const GET_SPECIFIC_BOARD_TOOL: Tool = {
  name: 'miro_get_specific_board',
  description: 'Get detailed information about a specific board including metadata and settings.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to get details for',
      },
    },
    required: ['board_id'],
  },
};

/**
 * Update an existing Miro board's properties including name, description, policies, and team/project assignment.
 */
const UPDATE_BOARD_TOOL: Tool = {
  name: 'miro_update_board',
  description:
    "Update an existing Miro board's properties including name, description, policies, and team/project assignment.",
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to update',
      },
      name: {
        type: 'string',
        description: 'New name for the board (1-60 characters)',
        minLength: 1,
        maxLength: 60,
      },
      description: {
        type: 'string',
        description: 'New description for the board (max 300 characters)',
        maxLength: 300,
      },
      team_id: {
        type: 'string',
        description: 'ID of team to move the board to',
      },
      project_id: {
        type: 'string',
        description: 'ID of project/space to add the board to',
      },
      access: {
        type: 'string',
        description: 'Public-level access to the board',
        enum: ['private', 'view', 'comment', 'edit'],
      },
      invite_to_account_and_board_link_access: {
        type: 'string',
        description: 'User role when inviting via invite link',
        enum: ['no_access', 'viewer', 'commenter', 'editor'],
      },
      organization_access: {
        type: 'string',
        description: 'Organization-level access to the board',
        enum: ['private', 'view', 'comment', 'edit'],
      },
      team_access: {
        type: 'string',
        description: 'Team-level access to the board',
        enum: ['private', 'view', 'comment', 'edit'],
      },
      collaboration_tools_start_access: {
        type: 'string',
        description: 'Who can start collaboration tools (timer, voting, etc.)',
        enum: ['all_editors', 'board_owners_and_coowners'],
      },
      copy_access: {
        type: 'string',
        description: 'Who can copy the board and download content',
        enum: ['anyone', 'team_members', 'team_editors', 'board_owner'],
      },
      sharing_access: {
        type: 'string',
        description: 'Who can change access and invite users',
        enum: ['team_members_with_editing_rights', 'owner_and_coowners'],
      },
    },
    required: ['board_id'],
  },
};

/**
 * Permanently delete a Miro board and all its contents.
 */
const DELETE_BOARD_TOOL: Tool = {
  name: 'miro_delete_board',
  description: 'Permanently delete a Miro board and all its contents.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to delete',
      },
    },
    required: ['board_id'],
  },
};

export const BOARD_TOOLS = [
  CREATE_BOARD_TOOL,
  LIST_BOARDS_TOOL,
  GET_SPECIFIC_BOARD_TOOL,
  UPDATE_BOARD_TOOL,
  DELETE_BOARD_TOOL,
] as const;
