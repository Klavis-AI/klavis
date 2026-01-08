import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Get all items (widgets) from a specific board with optional filtering.
 */
const GET_BOARD_ITEMS_TOOL: Tool = {
  name: 'miro_get_board_items',
  description: 'Get all items (widgets) from a specific board with optional filtering.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to get items from',
      },
      limit: {
        type: 'number',
        description: 'Maximum number of items to return (default: 50, max: 100)',
        default: 50,
        minimum: 1,
        maximum: 100,
      },
      type: {
        type: 'string',
        description: 'Filter items by type (e.g., "shape", "text", "sticker")',
        enum: ['shape', 'text', 'sticker', 'image', 'frame', 'card', 'embed', 'connector'],
      },
    },
    required: ['board_id'],
  },
};

/**
 * Get detailed information about a specific item on a board.
 */
const GET_SPECIFIC_BOARD_ITEM_TOOL: Tool = {
  name: 'miro_get_specific_board_item',
  description: 'Get detailed information about a specific item on a board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the item',
      },
      item_id: {
        type: 'string',
        description: 'ID of the item to get details for',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Update the position or parent of an item on a Miro board.
 */
const UPDATE_ITEM_POSITION_TOOL: Tool = {
  name: 'miro_update_item_position',
  description: 'Update the position or parent of an item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the item',
      },
      item_id: {
        type: 'string',
        description: 'ID of the item to update',
      },
      x: {
        type: 'number',
        description: 'New X coordinate for the item position',
      },
      y: {
        type: 'number',
        description: 'New Y coordinate for the item position',
      },
      parent_id: {
        type: 'string',
        description:
          'ID of parent frame to attach item to (omit to keep current parent, use "null" to attach to canvas)',
      },
      attach_to_canvas: {
        type: 'boolean',
        description:
          'Set to true to attach item directly to canvas (removes from any parent frame)',
        default: false,
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Permanently delete a specific item from a Miro board.
 */
const DELETE_BOARD_ITEM_TOOL: Tool = {
  name: 'miro_delete_board_item',
  description: 'Permanently delete a specific item from a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the item',
      },
      item_id: {
        type: 'string',
        description: 'ID of the item to delete',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

export const ITEM_TOOLS = [
  GET_BOARD_ITEMS_TOOL,
  GET_SPECIFIC_BOARD_ITEM_TOOL,
  UPDATE_ITEM_POSITION_TOOL,
  DELETE_BOARD_ITEM_TOOL,
] as const;
