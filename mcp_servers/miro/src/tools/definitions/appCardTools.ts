import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Add an app card item on a Miro board.
 */
const ADD_APP_CARD_TOOL: Tool = {
  name: 'miro_add_app_card_item',
  description: 'Add an app card item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the app card to',
      },
      title: {
        type: 'string',
        description: 'Title of the app card',
      },
      description: {
        type: 'string',
        description: 'Description of the app card',
      },
      status: {
        type: 'string',
        description: 'Connection status of the app card',
        enum: ['disconnected', 'connected', 'disabled'],
        default: 'disconnected',
      },
      fields: {
        type: 'array',
        description: 'Custom preview fields for the app card',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Field name' },
            value: { type: 'string', description: 'Field value' },
            type: { type: 'string', description: 'Field type' },
          },
          required: ['name', 'value'],
        },
      },
      x: {
        type: 'number',
        description: 'X coordinate for the app card position',
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the app card position',
      },
      width: {
        type: 'number',
        description: 'Width of the app card in pixels',
      },
      height: {
        type: 'number',
        description: 'Height of the app card in pixels',
      },
      rotation: {
        type: 'number',
        description: 'Rotation angle in degrees',
      },
      fill_color: {
        type: 'string',
        description: 'Fill color in hex format (e.g., #2d9bf0)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      parent_id: {
        type: 'string',
        description: 'ID of parent frame to attach the app card to',
      },
    },
    required: ['board_id'],
  },
};

/**
 * Get information about a specific app card item on a Miro board.
 */
const GET_APP_CARD_TOOL: Tool = {
  name: 'miro_get_app_card_item',
  description: 'Get information about a specific app card item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the app card',
      },
      item_id: {
        type: 'string',
        description: 'ID of the app card item to retrieve',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Update an app card item on a Miro board.
 */
const UPDATE_APP_CARD_TOOL: Tool = {
  name: 'miro_update_app_card_item',
  description: 'Update an app card item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the app card',
      },
      item_id: {
        type: 'string',
        description: 'ID of the app card item to update',
      },
      title: {
        type: 'string',
        description: 'New title of the app card',
      },
      description: {
        type: 'string',
        description: 'New description of the app card',
      },
      status: {
        type: 'string',
        description: 'New connection status of the app card',
        enum: ['disconnected', 'connected', 'disabled'],
      },
      fields: {
        type: 'array',
        description: 'Updated custom preview fields for the app card',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Field name' },
            value: { type: 'string', description: 'Field value' },
            type: { type: 'string', description: 'Field type' },
          },
          required: ['name', 'value'],
        },
      },
      x: {
        type: 'number',
        description: 'New X coordinate for the app card position',
      },
      y: {
        type: 'number',
        description: 'New Y coordinate for the app card position',
      },
      width: {
        type: 'number',
        description: 'New width of the app card in pixels',
      },
      height: {
        type: 'number',
        description: 'New height of the app card in pixels',
      },
      rotation: {
        type: 'number',
        description: 'New rotation angle in degrees',
      },
      fill_color: {
        type: 'string',
        description: 'New fill color in hex format (e.g., #2d9bf0)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      parent_id: {
        type: 'string',
        description: 'New parent frame ID (use "null" to attach to canvas)',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Delete an app card item from a Miro board.
 */
const DELETE_APP_CARD_TOOL: Tool = {
  name: 'miro_delete_app_card_item',
  description: 'Delete an app card item from a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the app card',
      },
      item_id: {
        type: 'string',
        description: 'ID of the app card item to delete',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

export const APP_CARD_TOOLS = [
  ADD_APP_CARD_TOOL,
  GET_APP_CARD_TOOL,
  UPDATE_APP_CARD_TOOL,
  DELETE_APP_CARD_TOOL,
] as const;
