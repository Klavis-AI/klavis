import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Add a shape item on a Miro board.
 */
const ADD_SHAPE_TOOL: Tool = {
  name: 'miro_add_shape',
  description: 'Add a shape item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the shape to',
      },
      content: {
        type: 'string',
        description: 'Text content to display on the shape',
      },
      shape: {
        type: 'string',
        description: 'Type of shape to create',
        enum: [
          'rectangle',
          'round_rectangle',
          'circle',
          'triangle',
          'rhombus',
          'parallelogram',
          'trapezoid',
          'pentagon',
          'hexagon',
          'octagon',
          'wedge_round_rectangle_callout',
          'star',
          'flow_chart_predefined_process',
          'cloud',
          'cross',
          'can',
          'right_arrow',
          'left_arrow',
          'left_right_arrow',
          'left_brace',
          'right_brace',
        ],
        default: 'rectangle',
      },
      border_color: {
        type: 'string',
        description: 'Border color in hex format (e.g., #1a1a1a)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      border_opacity: {
        type: 'number',
        description: 'Border opacity (0.0 to 1.0)',
        minimum: 0,
        maximum: 1,
      },
      border_style: {
        type: 'string',
        description: 'Border style',
        enum: ['normal', 'dotted', 'dashed'],
        default: 'normal',
      },
      border_width: {
        type: 'number',
        description: 'Border width (1 to 24)',
        minimum: 1,
        maximum: 24,
      },
      color: {
        type: 'string',
        description: 'Text color in hex format (e.g., #1a1a1a)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_color: {
        type: 'string',
        description: 'Fill color in hex format (e.g., #ffffff)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_opacity: {
        type: 'number',
        description: 'Fill opacity (0.0 to 1.0)',
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
        description: 'Font size (10 to 288)',
        minimum: 10,
        maximum: 288,
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
        description: 'X coordinate for the shape position',
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the shape position',
      },
      width: {
        type: 'number',
        description: 'Width of the shape in pixels',
      },
      height: {
        type: 'number',
        description: 'Height of the shape in pixels',
      },
      rotation: {
        type: 'number',
        description: 'Rotation angle in degrees',
      },
      parent_id: {
        type: 'string',
        description: 'ID of parent frame to attach the shape to',
      },
    },
    required: ['board_id'],
  },
};

/**
 * Get information about a specific shape item on a Miro board.
 */
const GET_SHAPE_TOOL: Tool = {
  name: 'miro_get_shape',
  description: 'Get information about a specific shape item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the shape',
      },
      item_id: {
        type: 'string',
        description: 'ID of the shape item to retrieve',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

/**
 * Update a shape item on a Miro board.
 */
const UPDATE_SHAPE_TOOL: Tool = {
  name: 'miro_update_shape',
  description: 'Update a shape item on a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the shape',
      },
      item_id: {
        type: 'string',
        description: 'ID of the shape item to update',
      },
      content: {
        type: 'string',
        description: 'New text content to display on the shape',
      },
      shape: {
        type: 'string',
        description: 'New type of shape',
        enum: [
          'rectangle',
          'round_rectangle',
          'circle',
          'triangle',
          'rhombus',
          'parallelogram',
          'trapezoid',
          'pentagon',
          'hexagon',
          'octagon',
          'wedge_round_rectangle_callout',
          'star',
          'flow_chart_predefined_process',
          'cloud',
          'cross',
          'can',
          'right_arrow',
          'left_arrow',
          'left_right_arrow',
          'left_brace',
          'right_brace',
        ],
      },
      border_color: {
        type: 'string',
        description: 'New border color in hex format (e.g., #1a1a1a)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      border_opacity: {
        type: 'number',
        description: 'New border opacity (0.0 to 1.0)',
        minimum: 0,
        maximum: 1,
      },
      border_style: {
        type: 'string',
        description: 'New border style',
        enum: ['normal', 'dotted', 'dashed'],
      },
      border_width: {
        type: 'number',
        description: 'New border width (1 to 24)',
        minimum: 1,
        maximum: 24,
      },
      color: {
        type: 'string',
        description: 'New text color in hex format (e.g., #1a1a1a)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_color: {
        type: 'string',
        description: 'New fill color in hex format (e.g., #ffffff)',
        pattern: '^#([A-Fa-f0-9]{6})$',
      },
      fill_opacity: {
        type: 'number',
        description: 'New fill opacity (0.0 to 1.0)',
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
        description: 'New font size (10 to 288)',
        minimum: 10,
        maximum: 288,
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
        description: 'New X coordinate for the shape position',
      },
      y: {
        type: 'number',
        description: 'New Y coordinate for the shape position',
      },
      width: {
        type: 'number',
        description: 'New width of the shape in pixels',
      },
      height: {
        type: 'number',
        description: 'New height of the shape in pixels',
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
 * Delete a shape item from a Miro board.
 */
const DELETE_SHAPE_TOOL: Tool = {
  name: 'miro_delete_shape',
  description: 'Delete a shape item from a Miro board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the shape',
      },
      item_id: {
        type: 'string',
        description: 'ID of the shape item to delete',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

export const SHAPE_TOOLS = [
  ADD_SHAPE_TOOL,
  GET_SHAPE_TOOL,
  UPDATE_SHAPE_TOOL,
  DELETE_SHAPE_TOOL,
] as const;
