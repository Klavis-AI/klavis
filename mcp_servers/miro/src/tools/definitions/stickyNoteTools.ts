import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Add a sticky note item on a Miro board.
 */
const ADD_STICKY_NOTE_TOOL: Tool = {
  name: 'miro_add_sticky_note',
  description: 'Add a sticky note item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the sticky note to',
      },
      content: {
        type: 'string',
        description: 'Text content of the sticky note',
      },
      shape: {
        type: 'string',
        description: 'Shape of the sticky note',
        enum: ['square', 'rectangle'],
        default: 'square',
      },
      fill_color: {
        type: 'string',
        description: 'Fill color of the sticky note',
        enum: [
          'gray',
          'light_yellow',
          'yellow',
          'orange',
          'light_green',
          'green',
          'dark_green',
          'cyan',
          'light_pink',
          'pink',
          'violet',
          'red',
          'light_blue',
          'blue',
          'dark_blue',
          'black',
        ],
        default: 'light_yellow',
      },
      text_align: {
        type: 'string',
        description: 'Horizontal text alignment',
        enum: ['left', 'center', 'right'],
        default: 'center',
      },
      text_align_vertical: {
        type: 'string',
        description: 'Vertical text alignment',
        enum: ['top', 'middle', 'bottom'],
        default: 'top',
      },
      x: {
        type: 'number',
        description: 'X coordinate for the sticky note position',
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the sticky note position',
      },
      width: {
        type: 'number',
        description: 'Width of the sticky note in pixels (cannot be used with height)',
      },
      height: {
        type: 'number',
        description: 'Height of the sticky note in pixels (cannot be used with width)',
      },
      parent_id: {
        type: 'string',
        description: 'ID of parent frame to attach the sticky note to',
      },
    },
    required: ['board_id', 'content'],
  },
};

/**
 * Get information about a specific sticky note item on a Miro board.
 */
const GET_STICKY_NOTE_TOOL: Tool = {
  name: 'miro_get_sticky_note',
  description: 'Get information about a specific sticky note item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the sticky note',
      },
      item_id: {
        type: 'string',
        description: 'ID of the sticky note item to retrieve',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Update a sticky note item on a Miro board.
 */
const UPDATE_STICKY_NOTE_TOOL: Tool = {
  name: 'miro_update_sticky_note',
  description: 'Update a sticky note item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the sticky note',
      },
      item_id: {
        type: 'string',
        description: 'ID of the sticky note item to update',
      },
      content: {
        type: 'string',
        description: 'New text content of the sticky note',
      },
      shape: {
        type: 'string',
        description: 'New shape of the sticky note',
        enum: ['square', 'rectangle'],
      },
      fill_color: {
        type: 'string',
        description: 'New fill color of the sticky note',
        enum: [
          'gray',
          'light_yellow',
          'yellow',
          'orange',
          'light_green',
          'green',
          'dark_green',
          'cyan',
          'light_pink',
          'pink',
          'violet',
          'red',
          'light_blue',
          'blue',
          'dark_blue',
          'black',
        ],
      },
      text_align: {
        type: 'string',
        description: 'New horizontal text alignment',
        enum: ['left', 'center', 'right'],
      },
      text_align_vertical: {
        type: 'string',
        description: 'New vertical text alignment',
        enum: ['top', 'middle', 'bottom'],
      },
      x: {
        type: 'number',
        description: 'New X coordinate for the sticky note position',
      },
      y: {
        type: 'number',
        description: 'New Y coordinate for the sticky note position',
      },
      width: {
        type: 'number',
        description: 'New width of the sticky note in pixels (cannot be used with height)',
      },
      height: {
        type: 'number',
        description: 'New height of the sticky note in pixels (cannot be used with width)',
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
 * Delete a sticky note item from a Miro board.
 */
const DELETE_STICKY_NOTE_TOOL: Tool = {
  name: 'miro_delete_sticky_note',
  description: 'Delete a sticky note item from a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the sticky note',
      },
      item_id: {
        type: 'string',
        description: 'ID of the sticky note item to delete',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

export const STICKY_NOTE_TOOLS = [
  ADD_STICKY_NOTE_TOOL,
  GET_STICKY_NOTE_TOOL,
  UPDATE_STICKY_NOTE_TOOL,
  DELETE_STICKY_NOTE_TOOL,
] as const;
