import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Add a card item on a Miro board.
 */
const ADD_CARD_TOOL: Tool = {
  name: 'miro_add_card_item',
  description: 'Add a card item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the card to',
      },
      title: {
        type: 'string',
        description: 'Title of the card',
      },
      description: {
        type: 'string',
        description: 'Description of the card',
      },
      assignee_id: {
        type: 'string',
        description: 'User ID of the person assigned to this card',
      },
      due_date: {
        type: 'string',
        description: 'Due date in ISO 8601 format (e.g., 2024-12-31T23:59:59Z)',
        format: 'date-time',
      },
      x: {
        type: 'number',
        description: 'X coordinate for the card position',
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the card position',
      },
      width: {
        type: 'number',
        description: 'Width of the card in pixels',
      },
      height: {
        type: 'number',
        description: 'Height of the card in pixels',
      },
      rotation: {
        type: 'number',
        description: 'Rotation angle in degrees',
      },
      card_theme: {
        type: 'string',
        description: 'Card theme color in hex format (e.g., #2d9bf0)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      parent_id: {
        type: 'string',
        description: 'ID of parent frame to attach the card to',
      },
    },
    required: ['board_id'],
  },
};

/**
 * Get information about a specific card item on a Miro board.
 */
const GET_CARD_TOOL: Tool = {
  name: 'miro_get_card_item',
  description: 'Get information about a specific card item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the card',
      },
      item_id: {
        type: 'string',
        description: 'ID of the card item to retrieve',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Update a card item on a Miro board.
 */
const UPDATE_CARD_TOOL: Tool = {
  name: 'miro_update_card_item',
  description: 'Update a card item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the card',
      },
      item_id: {
        type: 'string',
        description: 'ID of the card item to update',
      },
      title: {
        type: 'string',
        description: 'New title of the card',
      },
      description: {
        type: 'string',
        description: 'New description of the card',
      },
      assignee_id: {
        type: 'string',
        description: 'New assignee user ID for the card',
      },
      due_date: {
        type: 'string',
        description: 'New due date in ISO 8601 format (e.g., 2024-12-31T23:59:59Z)',
        format: 'date-time',
      },
      x: {
        type: 'number',
        description: 'New X coordinate for the card position',
      },
      y: {
        type: 'number',
        description: 'New Y coordinate for the card position',
      },
      width: {
        type: 'number',
        description: 'New width of the card in pixels',
      },
      height: {
        type: 'number',
        description: 'New height of the card in pixels',
      },
      rotation: {
        type: 'number',
        description: 'New rotation angle in degrees',
      },
      card_theme: {
        type: 'string',
        description: 'New card theme color in hex format (e.g., #2d9bf0)',
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
 * Delete a card item from a Miro board.
 */
const DELETE_CARD_TOOL: Tool = {
  name: 'miro_delete_card_item',
  description: 'Delete a card item from a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the card',
      },
      item_id: {
        type: 'string',
        description: 'ID of the card item to delete',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

export const CARD_TOOLS = [
  ADD_CARD_TOOL,
  GET_CARD_TOOL,
  UPDATE_CARD_TOOL,
  DELETE_CARD_TOOL,
] as const;
