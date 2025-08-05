import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  Tool,
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

dotenv.config();

const MIRO_API_URL = 'https://api.miro.com/v2';

const asyncLocalStorage = new AsyncLocalStorage<{
  miroClient: MiroClient;
}>();

let mcpServerInstance: Server | null = null;

class MiroClient {
  private accessToken: string;
  private baseUrl: string;

  constructor(accessToken: string, baseUrl: string = MIRO_API_URL) {
    this.accessToken = accessToken;
    this.baseUrl = baseUrl;
  }

  private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      Authorization: `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Miro API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return response.json();
  }

  async getBoards(limit: number = 25, teamId?: string): Promise<any> {
    let endpoint = `/boards?limit=${limit}`;
    if (teamId) {
      endpoint += `&team_id=${teamId}`;
    }
    return this.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async createBoard(data: {
    name: string;
    description?: string;
    sharingPolicy?: 'private' | 'view' | 'comment' | 'edit';
    teamId?: string;
  }): Promise<any> {
    return this.makeRequest('/boards', {
      method: 'POST',
      body: JSON.stringify({
        name: data.name,
        description: data.description,
        policy: {
          sharingPolicy: data.sharingPolicy || 'private',
        },
        teamId: data.teamId,
      }),
    });
  }

  async getBoardDetails(boardId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}`, {
      method: 'GET',
    });
  }

  async updateBoard(
    boardId: string,
    data: {
      name?: string;
      description?: string;
      sharingPolicy?: 'private' | 'view' | 'comment' | 'edit';
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        name: data.name,
        description: data.description,
        policy: data.sharingPolicy ? { sharingPolicy: data.sharingPolicy } : undefined,
      }),
    });
  }

  async deleteBoard(boardId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}`, {
      method: 'DELETE',
    });
  }

  async getBoardItems(boardId: string, limit: number = 50, type?: string): Promise<any> {
    let endpoint = `/boards/${boardId}/items?limit=${limit}`;
    if (type) {
      endpoint += `&type=${type}`;
    }
    return this.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getBoardItem(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'GET',
    });
  }

  async createBoardItem(
    boardId: string,
    data: {
      type: 'shape' | 'text' | 'sticker' | 'image' | 'frame' | 'card' | 'embed';
      content: any;
      position?: { x: number; y: number };
      style?: any;
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items`, {
      method: 'POST',
      body: JSON.stringify({
        type: data.type,
        data: data.content,
        position: data.position,
        style: data.style,
      }),
    });
  }

  async updateBoardItem(
    boardId: string,
    itemId: string,
    data: {
      content?: any;
      position?: { x: number; y: number };
      style?: any;
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        data: data.content,
        position: data.position,
        style: data.style,
      }),
    });
  }

  async deleteBoardItem(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'DELETE',
    });
  }

  async getTeams(): Promise<any> {
    return this.makeRequest('/teams', {
      method: 'GET',
    });
  }

  async getTeamMembers(teamId: string): Promise<any> {
    return this.makeRequest(`/teams/${teamId}/members`, {
      method: 'GET',
    });
  }

  async createWebhook(
    boardId: string,
    data: {
      url: string;
      events: string[];
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/webhooks`, {
      method: 'POST',
      body: JSON.stringify({
        url: data.url,
        events: data.events,
      }),
    });
  }

  async getWebhooks(boardId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/webhooks`, {
      method: 'GET',
    });
  }

  async deleteWebhook(boardId: string, webhookId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/webhooks/${webhookId}`, {
      method: 'DELETE',
    });
  }

  async exportBoard(boardId: string, format: 'pdf' | 'png' | 'jpeg'): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/export?format=${format}`, {
      method: 'GET',
    });
  }

  async createComment(boardId: string, itemId: string, text: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items/${itemId}/comments`, {
      method: 'POST',
      body: JSON.stringify({
        text,
      }),
    });
  }

  async getComments(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items/${itemId}/comments`, {
      method: 'GET',
    });
  }
  async createStickyNote(
    boardId: string,
    data: {
      content: string;
      x?: number;
      y?: number;
      color?: 'yellow' | 'green' | 'blue' | 'red' | 'gray' | 'orange' | 'purple' | 'pink';
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/stickers`, {
      method: 'POST',
      body: JSON.stringify({
        data: {
          content: data.content,
          shape: 'square',
        },
        position: {
          x: data.x || 0,
          y: data.y || 0,
        },
        style: {
          fillColor: data.color || 'yellow',
          textAlign: 'center',
          textAlignVertical: 'middle',
        },
      }),
    });
  }

  async createShape(
    boardId: string,
    data: {
      content?: string;
      shape:
        | 'rectangle'
        | 'round_rectangle'
        | 'circle'
        | 'triangle'
        | 'rhombus'
        | 'parallelogram'
        | 'trapezoid'
        | 'pentagon'
        | 'hexagon'
        | 'octagon'
        | 'wedge_round_rectangle'
        | 'star'
        | 'flow_chart_predefined_process'
        | 'cloud'
        | 'cross'
        | 'can'
        | 'right_arrow'
        | 'left_arrow'
        | 'top_arrow'
        | 'bottom_arrow'
        | 'arrows'
        | 'bracket';
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      color?: string;
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/shapes`, {
      method: 'POST',
      body: JSON.stringify({
        data: {
          content: data.content || '',
          shape: data.shape,
        },
        position: {
          x: data.x || 0,
          y: data.y || 0,
        },
        geometry: {
          width: data.width || 100,
          height: data.height || 100,
        },
        style: {
          fillColor: data.color || 'blue',
          borderColor: '#1a1a1a',
          borderWidth: '2.0',
          borderOpacity: '1.0',
          fillOpacity: '1.0',
        },
      }),
    });
  }

  async createTextItem(
    boardId: string,
    data: {
      content: string;
      x?: number;
      y?: number;
      width?: number;
      fontSize?: number;
      color?: string;
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/texts`, {
      method: 'POST',
      body: JSON.stringify({
        data: {
          content: data.content,
        },
        position: {
          x: data.x || 0,
          y: data.y || 0,
        },
        geometry: {
          width: data.width || 200,
        },
        style: {
          fontSize: data.fontSize ? `${data.fontSize}px` : '14px',
          textColor: data.color || '#1a1a1a',
          backgroundOpacity: '0.0',
          borderOpacity: '0.0',
        },
      }),
    });
  }

  async createConnector(
    boardId: string,
    data: {
      startItemId: string;
      endItemId: string;
      shape?: 'straight' | 'elbowed' | 'curved';
      style?: {
        strokeColor?: string;
        strokeWidth?: string;
        strokeStyle?: 'normal' | 'dotted' | 'dashed';
      };
      captions?: Array<{
        content: string;
        position: number;
      }>;
    },
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/connectors`, {
      method: 'POST',
      body: JSON.stringify({
        startItem: {
          id: data.startItemId,
        },
        endItem: {
          id: data.endItemId,
        },
        shape: data.shape || 'curved',
        style: {
          strokeColor: data.style?.strokeColor || '#000000',
          strokeWidth: data.style?.strokeWidth || '2.0',
          strokeStyle: data.style?.strokeStyle || 'normal',
        },
        captions:
          data.captions?.map((caption) => ({
            content: caption.content,
            position: caption.position,
            textAlignVertical: 'middle',
            textAlign: 'center',
          })) || [],
      }),
    });
  }

  async inviteCollaborator(
    boardId: string,
    data: {
      email?: string; 
      emails?: string[]; 
      role?: 'viewer' | 'commenter' | 'editor';
      message?: string;
    },
  ): Promise<any> {
    
    let emailsToInvite: string[];

    if (data.emails) {
      emailsToInvite = data.emails;
    } else if (data.email) {
      emailsToInvite = [data.email];
    } else {
      throw new Error('Either email or emails must be provided');
    }

    return this.makeRequest(`/boards/${boardId}/members`, {
      method: 'POST',
      body: JSON.stringify({
        emails: emailsToInvite,
        role: data.role || 'editor',
        message: data.message || '',
      }),
    });
  }

  async getBoardMembers(boardId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/members`, {
      method: 'GET',
    });
  }

  async updateBoardMemberRole(
    boardId: string,
    userId: string,
    role: 'viewer' | 'commenter' | 'editor',
  ): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/members/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        role,
      }),
    });
  }

  async removeBoardMember(boardId: string, userId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/members/${userId}`, {
      method: 'DELETE',
    });
  }
}

function getMiroClient() {
  const store = asyncLocalStorage.getStore();
  if (!store || !store.miroClient) {
    throw new Error('Store not found in AsyncLocalStorage');
  }
  if (!store.miroClient) {
    throw new Error('Miro client not found in AsyncLocalStorage');
  }
  return store.miroClient;
}

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
      sharingPolicy: {
        type: 'string',
        description: 'Board sharing policy',
        enum: ['private', 'view', 'comment', 'edit'], 
        default: 'private',
      },
      teamId: {
        type: 'string',
        description: 'Optional team ID to create the board under',
      },
    },
    required: ['name'],
  },
};

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

const GET_BOARD_DETAILS_TOOL: Tool = {
  name: 'miro_get_board_details',
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

const ADD_STICKY_NOTE_TOOL: Tool = {
  name: 'miro_add_sticky_note',
  description: 'Add a sticky note to a Miro board at specified coordinates.',
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
        maxLength: 8000, 
      },
      x: {
        type: 'number',
        description: 'X coordinate for the sticky note position (default: 0)',
        default: 0,
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the sticky note position (default: 0)',
        default: 0,
      },
      color: {
        type: 'string',
        description: 'Color of the sticky note',
        enum: ['yellow', 'green', 'blue', 'red', 'gray', 'orange', 'purple', 'pink'], 
        default: 'yellow',
      },
      width: {
        type: 'number',
        description: 'Width of the sticky note (default: auto)',
        minimum: 50,
        maximum: 1000,
      },
    },
    required: ['board_id', 'content'],
  },
};

const ADD_SHAPE_TOOL: Tool = {
  name: 'miro_add_shape',
  description: 'Add a shape to a Miro board with customizable properties.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the shape to',
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
          'wedge_round_rectangle',
          'star',
          'flow_chart_predefined_process',
          'cloud',
          'cross',
          'can',
          'right_arrow',
          'left_arrow',
          'top_arrow',
          'bottom_arrow',
          'arrows',
          'bracket',
        ], 
      },
      content: {
        type: 'string',
        description: 'Optional text content inside the shape',
        maxLength: 8000,
      },
      x: {
        type: 'number',
        description: 'X coordinate for the shape position (default: 0)',
        default: 0,
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the shape position (default: 0)',
        default: 0,
      },
      width: {
        type: 'number',
        description: 'Width of the shape (default: 100, min: 10, max: 32767)',
        default: 100,
        minimum: 10,
        maximum: 32767,
      },
      height: {
        type: 'number',
        description: 'Height of the shape (default: 100, min: 10, max: 32767)',
        default: 100,
        minimum: 10,
        maximum: 32767,
      },
      color: {
        type: 'string',
        description: 'Fill color of the shape in HEX format (default: #2d9bf0)',
        default: '#2d9bf0',
        pattern: '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', 
      },
      borderColor: {
        type: 'string',
        description: 'Border color in HEX format (default: #1a1a1a)',
        default: '#1a1a1a',
        pattern: '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
      },
    },
    required: ['board_id', 'shape'],
  },
};

const ADD_TEXT_ITEM_TOOL: Tool = {
  name: 'miro_add_text_item',
  description: 'Add a text item to a Miro board with formatting options.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the text to',
      },
      content: {
        type: 'string',
        description: 'Text content to add',
        maxLength: 8000,
      },
      x: {
        type: 'number',
        description: 'X coordinate for the text position (default: 0)',
        default: 0,
      },
      y: {
        type: 'number',
        description: 'Y coordinate for the text position (default: 0)',
        default: 0,
      },
      width: {
        type: 'number',
        description: 'Width of the text box (default: 200, min: 50, max: 32767)',
        default: 200,
        minimum: 50,
        maximum: 32767,
      },
      fontSize: {
        type: 'number',
        description: 'Font size in pixels (default: 14, min: 1, max: 200)',
        default: 14,
        minimum: 1,
        maximum: 200,
      },
      color: {
        type: 'string',
        description: 'Color of the text in HEX format (default: #1a1a1a)',
        default: '#1a1a1a',
        pattern: '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
      },
      textAlign: {
        type: 'string',
        description: 'Text alignment',
        enum: ['left', 'center', 'right'],
        default: 'left',
      },
    },
    required: ['board_id', 'content'],
  },
};

const CREATE_CONNECTOR_TOOL: Tool = {
  name: 'miro_create_connector',
  description: 'Create a connector between two items on a Miro board with customizable style.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the items',
      },
      start_item_id: {
        type: 'string',
        description: 'ID of the starting item for the connector',
      },
      end_item_id: {
        type: 'string',
        description: 'ID of the ending item for the connector',
      },
      shape: {
        type: 'string',
        description: 'Shape of the connector line',
        enum: ['straight', 'elbowed', 'curved'],
        default: 'curved',
      },
      style: {
        type: 'string',
        description: 'Style of the connector line',
        enum: ['normal', 'dashed', 'dotted'],
        default: 'normal',
      },
      strokeColor: {
        type: 'string',
        description: 'Color of the connector line in HEX format',
        default: '#000000',
        pattern: '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
      },
      captions: {
        type: 'array',
        description: 'Text labels to add along the connector',
        items: {
          type: 'object',
          properties: {
            content: { type: 'string' },
            position: {
              type: 'number',
              description: 'Position along connector (0-1)',
              minimum: 0,
              maximum: 1,
            },
          },
        },
      },
    },
    required: ['board_id', 'start_item_id', 'end_item_id'],
  },
};

const INVITE_COLLABORATOR_TOOL: Tool = {
  name: 'miro_invite_collaborator',
  description: 'Invite one or more collaborators to a Miro board with specified access level.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to invite the collaborator to',
      },
      emails: {
        type: 'array',
        description: 'Email addresses of the people to invite',
        items: {
          type: 'string',
          format: 'email',
        },
        minItems: 1,
      },
      role: {
        type: 'string',
        description: 'Access level to assign to the collaborator',
        enum: ['viewer', 'commenter', 'editor'],
        default: 'editor',
      },
      message: {
        type: 'string',
        description: 'Personalized message to include with the invitation',
        maxLength: 500,
      },
    },
    required: ['board_id', 'emails'],
  },
};

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

const UPDATE_BOARD_TOOL: Tool = {
  name: 'miro_update_board',
  description: "Update an existing Miro board's name, description, or sharing policy.",
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to update',
      },
      name: {
        type: 'string',
        description: 'New name for the board',
      },
      description: {
        type: 'string',
        description: 'New description for the board',
      },
      sharingPolicy: {
        type: 'string',
        description: 'New sharing policy for the board',
        enum: ['private', 'view', 'comment', 'edit'],
      },
    },
    required: ['board_id'],
  },
};

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

const GET_BOARD_ITEM_TOOL: Tool = {
  name: 'miro_get_board_item',
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

const UPDATE_BOARD_ITEM_TOOL: Tool = {
  name: 'miro_update_board_item',
  description: 'Update properties of an existing board item.',
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
      content: {
        type: 'object',
        description: 'Updated content for the item',
      },
      position: {
        type: 'object',
        description: 'New position for the item',
        properties: {
          x: { type: 'number' },
          y: { type: 'number' },
        },
      },
      style: {
        type: 'object',
        description: 'Updated style properties for the item',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

const GET_TEAMS_TOOL: Tool = {
  name: 'miro_get_teams',
  description: 'Get all teams accessible to the current user.',
  inputSchema: {
    type: 'object',
    properties: {},
  },
};

const GET_TEAM_MEMBERS_TOOL: Tool = {
  name: 'miro_get_team_members',
  description: 'Get members of a specific team.',
  inputSchema: {
    type: 'object',
    properties: {
      team_id: {
        type: 'string',
        description: 'ID of the team to get members for',
      },
    },
    required: ['team_id'],
  },
};

const CREATE_WEBHOOK_TOOL: Tool = {
  name: 'miro_create_webhook',
  description: 'Create a webhook to receive notifications about board events.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to create webhook for',
      },
      url: {
        type: 'string',
        format: 'uri',
        description: 'URL to send webhook notifications to',
      },
      events: {
        type: 'array',
        description: 'List of events to subscribe to',
        items: {
          type: 'string',
          enum: [
            'item_created',
            'item_updated',
            'item_deleted',
            'board_updated',
            'board_shared',
            'board_member_added',
            'board_member_removed',
            'board_member_role_updated',
          ],
        },
        minItems: 1,
      },
    },
    required: ['board_id', 'url', 'events'],
  },
};

const GET_WEBHOOKS_TOOL: Tool = {
  name: 'miro_get_webhooks',
  description: 'Get all webhooks configured for a board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to get webhooks for',
      },
    },
    required: ['board_id'],
  },
};

const DELETE_WEBHOOK_TOOL: Tool = {
  name: 'miro_delete_webhook',
  description: 'Delete a specific webhook from a board.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the webhook',
      },
      webhook_id: {
        type: 'string',
        description: 'ID of the webhook to delete',
      },
    },
    required: ['board_id', 'webhook_id'],
  },
};

const EXPORT_BOARD_TOOL: Tool = {
  name: 'miro_export_board',
  description: 'Export a board in the specified format.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to export',
      },
      format: {
        type: 'string',
        description: 'Export format',
        enum: ['pdf', 'png', 'jpeg'],
        default: 'pdf',
      },
    },
    required: ['board_id'],
  },
};

const CREATE_COMMENT_TOOL: Tool = {
  name: 'miro_create_comment',
  description: 'Add a comment to a specific board item.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the item',
      },
      item_id: {
        type: 'string',
        description: 'ID of the item to comment on',
      },
      text: {
        type: 'string',
        description: 'Comment text',
        maxLength: 8000,
      },
    },
    required: ['board_id', 'item_id', 'text'],
  },
};

const GET_COMMENTS_TOOL: Tool = {
  name: 'miro_get_comments',
  description: 'Get all comments for a specific board item.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board containing the item',
      },
      item_id: {
        type: 'string',
        description: 'ID of the item to get comments for',
      },
    },
    required: ['board_id', 'item_id'],
  },
};

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

const CREATE_BOARD_ITEM_TOOL: Tool = {
  name: 'miro_create_board_item',
  description: 'Create a generic board item with flexible type and content.',
  inputSchema: {
    type: 'object',
    properties: {
      board_id: {
        type: 'string',
        description: 'ID of the board to add the item to',
      },
      type: {
        type: 'string',
        description: 'Type of item to create',
        enum: ['shape', 'text', 'sticker', 'image', 'frame', 'card', 'embed'],
      },
      content: {
        type: 'object',
        description: 'Content data for the item (structure depends on type)',
      },
      position: {
        type: 'object',
        description: 'Position of the item on the board',
        properties: {
          x: { type: 'number', default: 0 },
          y: { type: 'number', default: 0 },
        },
      },
      style: {
        type: 'object',
        description: 'Style properties for the item',
      },
    },
    required: ['board_id', 'type', 'content'],
  },
};

function safeLog(
  level: 'error' | 'debug' | 'info' | 'notice' | 'warning' | 'critical' | 'alert' | 'emergency',
  data: any,
): void {
  try {
    const logData = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
    console.log(`[${level.toUpperCase()}] ${logData}`);
  } catch (error) {
    console.log(`[${level.toUpperCase()}] [LOG_ERROR] Could not serialize log data`);
  }
}

const getMiroMcpServer = () => {
  if (!mcpServerInstance) {
    mcpServerInstance = new Server(
      {
        name: 'miro-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    mcpServerInstance.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          CREATE_BOARD_TOOL,
          UPDATE_BOARD_TOOL,
          DELETE_BOARD_TOOL,
          LIST_BOARDS_TOOL,
          GET_BOARD_DETAILS_TOOL,
          EXPORT_BOARD_TOOL,
          GET_BOARD_ITEMS_TOOL,
          GET_BOARD_ITEM_TOOL,
          CREATE_BOARD_ITEM_TOOL,
          UPDATE_BOARD_ITEM_TOOL,
          ADD_STICKY_NOTE_TOOL,
          ADD_SHAPE_TOOL,
          ADD_TEXT_ITEM_TOOL,
          CREATE_CONNECTOR_TOOL,
          DELETE_BOARD_ITEM_TOOL,
          INVITE_COLLABORATOR_TOOL,
          GET_BOARD_MEMBERS_TOOL,
          UPDATE_BOARD_MEMBER_ROLE_TOOL,
          REMOVE_BOARD_MEMBER_TOOL,
          CREATE_COMMENT_TOOL,
          GET_COMMENTS_TOOL,
          CREATE_WEBHOOK_TOOL,
          GET_WEBHOOKS_TOOL,
          DELETE_WEBHOOK_TOOL,
          GET_TEAMS_TOOL,
          GET_TEAM_MEMBERS_TOOL,
        ],
        categories: [
          {
            name: 'board_management',
            description: 'Tools for creating and managing Miro boards',
          },
          {
            name: 'content_management',
            description: 'Tools for adding and managing content on boards',
          },
          {
            name: 'collaboration',
            description: 'Tools for managing board collaborators and comments',
          },
          {
            name: 'integrations',
            description: 'Tools for webhook integrations and external connections',
          },
          {
            name: 'teams_orgs',
            description: 'Tools for team and organization management',
          },
        ],
        organization: {
          board_management: [
            'miro_create_board',
            'miro_update_board',
            'miro_delete_board',
            'miro_list_boards',
            'miro_get_board_details',
            'miro_export_board',
          ],
          content_management: [
            'miro_get_board_items',
            'miro_get_board_item',
            'miro_create_board_item',
            'miro_update_board_item',
            'miro_add_sticky_note',
            'miro_add_shape',
            'miro_add_text_item',
            'miro_create_connector',
            'miro_delete_board_item',
          ],
          collaboration: [
            'miro_invite_collaborator',
            'miro_get_board_members',
            'miro_update_board_member_role',
            'miro_remove_board_member',
            'miro_create_comment',
            'miro_get_comments',
          ],
          integrations: ['miro_create_webhook', 'miro_get_webhooks', 'miro_delete_webhook'],
          teams_orgs: ['miro_get_teams', 'miro_get_team_members'],
        },
      };
    });

    mcpServerInstance.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'miro_create_board': {
            const client = getMiroClient();
            const result = await client.createBoard({
              name: (args as any)?.name,
              description: (args as any)?.description,
              sharingPolicy: (args as any)?.string || 'private',
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_list_boards': {
            const client = getMiroClient();
            const result = await client.getBoards((args?.limit as number) || 25);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_board_details': {
            const client = getMiroClient();
            const result = await client.getBoardDetails((args as any)?.board_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_board_items': {
            const client = getMiroClient();
            const result = await client.getBoardItems(
              (args as any)?.board_id,
              (args?.limit as number) || 50,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_add_sticky_note': {
            const client = getMiroClient();
            const result = await client.createStickyNote((args as any)?.board_id, {
              content: (args as any)?.content,
              x: (args as any)?.x || 0,
              y: (args as any)?.y || 0,
              color: (args as any)?.color || 'yellow',
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_add_shape': {
            const client = getMiroClient();
            const result = await client.createShape((args as any)?.board_id, {
              shape: (args as any)?.shape,
              content: (args as any)?.content,
              x: (args as any)?.x || 0,
              y: (args as any)?.y || 0,
              width: (args as any)?.width || 100,
              height: (args as any)?.height || 100,
              color: (args as any)?.color || 'blue',
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_add_text_item': {
            const client = getMiroClient();
            const result = await client.createTextItem((args as any)?.board_id, {
              content: (args as any)?.content,
              x: (args as any)?.x || 0,
              y: (args as any)?.y || 0,
              fontSize: (args as any)?.fontSize || 14,
              color: (args as any)?.color || 'black',
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_create_connector': {
            const client = getMiroClient();
            const result = await client.createConnector((args as any)?.board_id, {
              startItemId: (args as any)?.start_item_id,
              endItemId: (args as any)?.end_item_id,
              shape: (args as any)?.shape || 'curved',
              style: {
                strokeColor: (args as any)?.stroke_color || '#000000',
                strokeWidth: (args as any)?.stroke_width || '2.0',
                strokeStyle: (args as any)?.stroke_style || 'normal',
              },
              captions: (args as any)?.captions,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_invite_collaborator': {
            const client = getMiroClient();
            const result = await client.inviteCollaborator((args as any)?.board_id, {
              emails: (args as any)?.emails,
              role: (args as any)?.role || 'editor',
              message: (args as any)?.message,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_board_item': {
            const client = getMiroClient();
            const result = await client.deleteBoardItem(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_board': {
            const client = getMiroClient();
            const result = await client.updateBoard((args as any)?.board_id, {
              name: (args as any)?.name,
              description: (args as any)?.description,
              sharingPolicy: (args as any)?.sharingPolicy,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_board': {
            const client = getMiroClient();
            const result = await client.deleteBoard((args as any)?.board_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_board_item': {
            const client = getMiroClient();
            const result = await client.getBoardItem(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_board_item': {
            const client = getMiroClient();
            const result = await client.updateBoardItem(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                content: (args as any)?.content,
                position: (args as any)?.position
                  ? {
                      x: (args as any)?.position?.x,
                      y: (args as any)?.position?.y,
                    }
                  : undefined,
                style: (args as any)?.style,
              },
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_teams': {
            const client = getMiroClient();
            const result = await client.getTeams();

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_team_members': {
            const client = getMiroClient();
            const result = await client.getTeamMembers((args as any)?.team_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_create_webhook': {
            const client = getMiroClient();
            const result = await client.createWebhook((args as any)?.board_id, {
              url: (args as any)?.url,
              events: (args as any)?.events || [],
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_webhooks': {
            const client = getMiroClient();
            const result = await client.getWebhooks((args as any)?.board_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_delete_webhook': {
            const client = getMiroClient();
            const result = await client.deleteWebhook(
              (args as any)?.board_id,
              (args as any)?.webhook_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_export_board': {
            const client = getMiroClient();
            const result = await client.exportBoard(
              (args as any)?.board_id,
              (args as any)?.format || 'pdf',
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_create_comment': {
            const client = getMiroClient();
            const result = await client.createComment(
              (args as any)?.board_id,
              (args as any)?.item_id,
              (args as any)?.text,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_comments': {
            const client = getMiroClient();
            const result = await client.getComments(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_get_board_members': {
            const client = getMiroClient();
            const result = await client.getBoardMembers((args as any)?.board_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_board_member_role': {
            const client = getMiroClient();
            const result = await client.updateBoardMemberRole(
              (args as any)?.board_id,
              (args as any)?.user_id,
              (args as any)?.role || 'editor',
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_remove_board_member': {
            const client = getMiroClient();
            const result = await client.removeBoardMember(
              (args as any)?.board_id,
              (args as any)?.user_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_create_board_item': {
            const client = getMiroClient();
            const result = await client.createBoardItem((args as any)?.board_id, {
              type: (args as any)?.type,
              content: (args as any)?.content,
              position: (args as any)?.position
                ? {
                    x: (args as any)?.position?.x || 0,
                    y: (args as any)?.position?.y || 0,
                  }
                : { x: 0, y: 0 },
              style: (args as any)?.style,
            });

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error: any) {
        safeLog('error', `Tool ${name} failed: ${error.message}`);
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  return mcpServerInstance;
};

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const accessToken = process.env.MIRO_ACCESS_TOKEN || (req.headers['x-auth-token'] as string);

  if (!accessToken) {
    console.error(
      'Error: Miro access token is missing. Provide it via MIRO_ACCESS_TOKEN env var or x-auth-token header.',
    );
    return res.status(401).json({
      jsonrpc: '2.0',
      error: {
        code: -32001,
        message: 'Missing Miro access token',
      },
      id: null,
    });
  }

  if (!accessToken.startsWith('Bearer ') && !accessToken.match(/^[a-zA-Z0-9_-]+$/)) {
    return res.status(401).json({
      jsonrpc: '2.0',
      error: {
        code: -32001,
        message: 'Invalid token format',
      },
      id: null,
    });
  }

  const miroClient = new MiroClient(accessToken);

  const server = getMiroMcpServer();

  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    await server.connect(transport);

    asyncLocalStorage.run({ miroClient }, async () => {
      await transport.handleRequest(req, res, req.body);
    });

    res.on('close', () => {
      console.log('Request closed');
      transport.close();
    });
  } catch (error: any) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: `Internal server error: ${error.message}`,
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: Response) => {
  console.log('Received GET MCP request');
  res.writeHead(405).end(
    JSON.stringify({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'Method not allowed.',
      },
      id: null,
    }),
  );
});

app.delete('/mcp', async (req: Request, res: Response) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(
    JSON.stringify({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'Method not allowed.',
      },
      id: null,
    }),
  );
});

app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  });
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

const transports = new Map<string, SSEServerTransport>();

app.get('/sse', async (req, res) => {
  try {
    const accessToken = process.env.MIRO_ACCESS_TOKEN || (req.headers['x-auth-token'] as string);

    if (!accessToken) {
      console.error('SSE connection rejected: Missing access token');
      return res.status(401).json({ error: 'Missing Miro access token' });
    }

    const transport = new SSEServerTransport('/messages', res);

    res.on('close', async () => {
      console.log(`SSE connection closed for session: ${transport.sessionId}`);
      try {
        transports.delete(transport.sessionId);
        await transport.close(); 
      } catch (error) {
        console.error('Error during SSE cleanup:', error);
      }
    });

    res.on('error', (error) => {
      console.error(`SSE connection error for session ${transport.sessionId}:`, error);
      transports.delete(transport.sessionId);
    });

    transports.set(transport.sessionId, transport);

    const server = getMiroMcpServer(); 
    await server.connect(transport);

    console.log(`SSE connection established with session: ${transport.sessionId}`);
  } catch (error) {
    console.error('Error establishing SSE connection:', error);
    if (!res.headersSent) {
      res.status(500).json({ error: 'Failed to establish SSE connection' });
    }
  }
});

app.post('/messages', async (req, res) => {
  try {
    const sessionId = req.query.sessionId as string;

    if (!sessionId) {
      return res.status(400).json({ error: 'Missing sessionId parameter' });
    }

    const transport = transports.get(sessionId);
    if (!transport) {
      console.error(`Transport not found for session ID: ${sessionId}`);
      return res.status(404).json({ error: 'Transport not found or session expired' });
    }

    const accessToken = process.env.MIRO_ACCESS_TOKEN || (req.headers['x-auth-token'] as string);

    if (!accessToken) {
      console.error('Message rejected: Missing access token');
      return res.status(401).json({ error: 'Missing Miro access token' });
    }

    if (!accessToken.match(/^[a-zA-Z0-9_-]+$/) && !accessToken.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Invalid token format' });
    }

    const miroClient = new MiroClient(accessToken);

    await asyncLocalStorage.run({ miroClient }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } catch (error: any) {
    console.error('Error handling message:', error);
    if (!res.headersSent) {
      res.status(500).json({ error: `Message handling failed: ${error.message}` });
    }
  }
});

app.delete('/sse/:sessionId', async (req, res) => {
  const sessionId = req.params.sessionId;
  const transport = transports.get(sessionId);

  if (transport) {
    try {
      await transport.close();
      transports.delete(sessionId);
      console.log(`Session ${sessionId} manually terminated`);
      res.status(200).json({ message: 'Session terminated' });
    } catch (error) {
      console.error(`Error terminating session ${sessionId}:`, error);
      res.status(500).json({ error: 'Failed to terminate session' });
    }
  } else {
    res.status(404).json({ error: 'Session not found' });
  }
});

app.get('/sse/status', (req, res) => {
  res.json({
    activeConnections: transports.size,
    sessions: Array.from(transports.keys()),
    timestamp: new Date().toISOString(),
  });
});

app.listen(5000, () => {
  console.log('Miro MCP server running on port 5000');
});
