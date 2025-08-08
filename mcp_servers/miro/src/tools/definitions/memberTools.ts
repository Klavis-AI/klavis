import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Get all members and their roles for a specific board.
 */
const GET_BOARD_MEMBERS_TOOL: Tool = {
  name: 'miro_get_board_members',
  description: 'Get all members and their roles for a specific board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to get members for',
      },
    },
    required: ['board_id'],
  },
};

/**
 * Update the role of an existing board member.
 */
const UPDATE_BOARD_MEMBER_ROLE_TOOL: Tool = {
  name: 'miro_update_board_member_role',
  description: 'Update the role of an existing board member.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board',
      },
      user_id: {
        type: 'string',
        description: 'ID of the user whose role to update',
      },
      role: {
        type: 'string',
        description: 'New role to assign',
        enum: ['viewer', 'commenter', 'editor'],
      },
    },
    required: ['board_id', 'user_id', 'role'],
  },
};

/**
 * Remove a member from a board.
 */
const REMOVE_BOARD_MEMBER_TOOL: Tool = {
  name: 'miro_remove_board_member',
  description: 'Remove a member from a board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board',
      },
      user_id: {
        type: 'string',
        description: 'ID of the user to remove',
      },
    },
    required: ['board_id', 'user_id'],
  },
};

export const MEMBER_TOOLS = [
  GET_BOARD_MEMBERS_TOOL,
  UPDATE_BOARD_MEMBER_ROLE_TOOL,
  REMOVE_BOARD_MEMBER_TOOL,
] as const;
