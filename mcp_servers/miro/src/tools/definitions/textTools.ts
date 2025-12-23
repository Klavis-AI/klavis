import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Add a text item on a Miro board.
 */
const ADD_TEXT_TOOL: Tool = {
  name: 'miro_add_text_item',
  description: 'Add a text item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the text to',
      },
      content: {
        type: 'string',
        description: 'Text content to display',
      },
      color: {
        type: 'string',
        description: 'Text color in hex format (e.g., #1a1a1a)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_color: {
        type: 'string',
        description: 'Background color in hex format (e.g., #ffffff)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_opacity: {
        type: 'number',
        description: 'Background opacity (0.0 to 1.0)',
        minimum: 0,
        maximum: 1,
      },
      font_family: {
        type: 'string',
        description: 'Font family',
        enum: [
          'arial',
          'abril_fatface',
          'bangers',
          'eb_garamond',
          'georgia',
          'graduate',
          'gravitas_one',
          'fredoka_one',
          'nixie_one',
          'open_sans',
          'permanent_marker',
          'pt_sans',
          'pt_sans_narrow',
          'pt_serif',
          'rammetto_one',
          'roboto',
          'roboto_condensed',
          'roboto_slab',
          'caveat',
          'times_new_roman',
          'titan_one',
          'lemon_tuesday',
          'roboto_mono',
          'noto_sans',
          'plex_sans',
          'plex_serif',
          'plex_mono',
          'spoof',
          'tiempos_text',
          'formular',
        ],
        default: 'arial',
      },
      font_size: {
        type: 'number',
        description: 'Font size (minimum 1)',
        minimum: 1,
      },
      text_align: {
        type: 'string',
        description: 'Text alignment',
        enum: ['left', 'center', 'right'],
        default: 'center',
      },
      x: {
        type: 'number',
        description: 'X coordinate for the text position',
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the text position',
      },
      width: {
        type: 'number',
        description: 'Width of the text box in pixels (minimum 1.7 times font size)',
      },
      rotation: {
        type: 'number',
        description: 'Rotation angle in degrees',
      },
      parent_id: {
        type: 'string',
        description: 'ID of parent frame to attach the text to',
      },
    },
    required: ['board_id', 'content'],
  },
};

/**
 * Get information about a specific text item on a Miro board.
 */
const GET_TEXT_TOOL: Tool = {
  name: 'miro_get_text_item',
  description: 'Get information about a specific text item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the text',
      },
      item_id: {
        type: 'string',
        description: 'ID of the text item to retrieve',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Update a text item on a Miro board.
 */
const UPDATE_TEXT_TOOL: Tool = {
  name: 'miro_update_text_item',
  description: 'Update a text item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the text',
      },
      item_id: {
        type: 'string',
        description: 'ID of the text item to update',
      },
      content: {
        type: 'string',
        description: 'New text content to display',
      },
      color: {
        type: 'string',
        description: 'New text color in hex format (e.g., #1a1a1a)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_color: {
        type: 'string',
        description: 'New background color in hex format (e.g., #ffffff)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_opacity: {
        type: 'number',
        description: 'New background opacity (0.0 to 1.0)',
        minimum: 0,
        maximum: 1,
      },
      font_family: {
        type: 'string',
        description: 'New font family',
        enum: [
          'arial',
          'abril_fatface',
          'bangers',
          'eb_garamond',
          'georgia',
          'graduate',
          'gravitas_one',
          'fredoka_one',
          'nixie_one',
          'open_sans',
          'permanent_marker',
          'pt_sans',
          'pt_sans_narrow',
          'pt_serif',
          'rammetto_one',
          'roboto',
          'roboto_condensed',
          'roboto_slab',
          'caveat',
          'times_new_roman',
          'titan_one',
          'lemon_tuesday',
          'roboto_mono',
          'noto_sans',
          'plex_sans',
          'plex_serif',
          'plex_mono',
          'spoof',
          'tiempos_text',
          'formular',
        ],
      },
      font_size: {
        type: 'number',
        description: 'New font size (minimum 1)',
        minimum: 1,
      },
      text_align: {
        type: 'string',
        description: 'New text alignment',
        enum: ['left', 'center', 'right'],
      },
      x: {
        type: 'number',
        description: 'New X coordinate for the text position',
      },
      y: {
        type: 'number',
        description: 'New Y coordinate for the text position',
      },
      width: {
        type: 'number',
        description: 'New width of the text box in pixels (minimum 1.7 times font size)',
      },
      rotation: {
        type: 'number',
        description: 'New rotation angle in degrees',
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
 * Delete a text item from a Miro board.
 */
const DELETE_TEXT_TOOL: Tool = {
  name: 'miro_delete_text_item',
  description: 'Delete a text item from a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the text',
      },
      item_id: {
        type: 'string',
        description: 'ID of the text item to delete',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

export const TEXT_TOOLS = [
  ADD_TEXT_TOOL,
  GET_TEXT_TOOL,
  UPDATE_TEXT_TOOL,
  DELETE_TEXT_TOOL,
] as const;
