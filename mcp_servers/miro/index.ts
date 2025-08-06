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

  // ================== BOARDS ==================
  // START ======
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
    sharingPolicy?: {
      access: 'private' | 'view' | 'comment' | 'edit';
      inviteToAccountAndBoardLinkAccess?: 'no_access' | 'viewer' | 'commenter' | 'editor';
      organizationAccess?: 'private' | 'view' | 'comment' | 'edit';
      teamAccess?: 'private' | 'view' | 'comment' | 'edit';
    };
    permissionsPolicy?: {
      collaborationToolsStartAccess?: 'all_editors' | 'board_owners_and_coowners';
      copyAccess?: 'anyone' | 'team_members' | 'team_editors' | 'board_owner';
      sharingAccess?: 'owner_and_coowners' | 'team_members_with_editing_rights';
    };
    teamId?: string;
    projectId?: string;
  }): Promise<any> {
    const payload: any = {
      name: data.name,
    };

    if (data.description) {
      payload.description = data.description;
    }

    if (data.sharingPolicy || data.permissionsPolicy) {
      payload.policy = {};

      if (data.sharingPolicy) {
        payload.policy.sharingPolicy = data.sharingPolicy;
      }

      if (data.permissionsPolicy) {
        payload.policy.permissionsPolicy = data.permissionsPolicy;
      }
    }

    if (data.teamId) {
      payload.teamId = data.teamId;
    }

    if (data.projectId) {
      payload.projectId = data.projectId;
    }

    return this.makeRequest('/boards', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getSpecificBoard(boardId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}`, {
      method: 'GET',
    });
  }

  async updateBoard(
    boardId: string,
    data: {
      name?: string;
      description?: string;
      teamId?: string;
      projectId?: string;
      policy?: {
        sharingPolicy?: {
          access?: 'private' | 'view' | 'comment' | 'edit';
          inviteToAccountAndBoardLinkAccess?: 'no_access' | 'viewer' | 'commenter' | 'editor';
          organizationAccess?: 'private' | 'view' | 'comment' | 'edit';
          teamAccess?: 'private' | 'view' | 'comment' | 'edit';
        };
        permissionsPolicy?: {
          collaborationToolsStartAccess?: 'all_editors' | 'board_owners_and_coowners';
          copyAccess?: 'anyone' | 'team_members' | 'team_editors' | 'board_owner';
          sharingAccess?: 'team_members_with_editing_rights' | 'owner_and_coowners';
        };
      };
    },
  ): Promise<any> {
    const payload: any = {};

    if (data.name !== undefined) {
      if (data.name.length < 1 || data.name.length > 60) {
        throw new Error('Board name must be between 1 and 60 characters');
      }
      payload.name = data.name;
    }

    if (data.description !== undefined) {
      if (data.description.length > 300) {
        throw new Error('Board description must not exceed 300 characters');
      }
      payload.description = data.description;
    }

    if (data.teamId !== undefined) {
      payload.teamId = data.teamId;
    }

    if (data.projectId !== undefined) {
      payload.projectId = data.projectId;
    }

    if (data.policy) {
      payload.policy = {};

      if (data.policy.sharingPolicy) {
        payload.policy.sharingPolicy = data.policy.sharingPolicy;
      }

      if (data.policy.permissionsPolicy) {
        payload.policy.permissionsPolicy = data.policy.permissionsPolicy;
      }
    }

    return this.makeRequest(`/boards/${boardId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteBoard(boardId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}`, {
      method: 'DELETE',
    });
  }
  // End ======
  // ================== BOARDS ==================

  // ================== BOARD MEMBERS ==================
  // START ======
  async getBoardMembers(boardId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/members`, {
      method: 'GET',
    });
  }

  async updateBoardMemberRole(
    boardId: string,
    userId: string,
    role: 'viewer' | 'commenter' | 'editor' | 'coowner' | 'owner',
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
  // End ======
  // ================== BOARD MEMBERS ==================

  // ================== ITEMS ==================
  // START ======

  async getBoardItems(boardId: string, limit: number = 50, type?: string): Promise<any> {
    let endpoint = `/boards/${boardId}/items?limit=${limit}`;
    if (type) {
      endpoint += `&type=${type}`;
    }
    return this.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getSpecificBoardItem(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'GET',
    });
  }

  async updateItemPosition(
    boardId: string,
    itemId: string,
    data: {
      position?: { x: number; y: number };
      parentId?: string | null;
    },
  ): Promise<any> {
    const payload: any = {};

    if (data.position) {
      payload.position = {
        x: data.position.x,
        y: data.position.y,
      };
    }

    if (data.parentId !== undefined) {
      payload.parent = data.parentId ? { id: data.parentId } : null;
    }

    return this.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteBoardItem(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'DELETE',
    });
  }
  // End ======
  // ================== ITEMS ==================

  // ================== APP CARD ITEMS ==================
  // START ======
  async createAppCard(
    boardId: string,
    data: {
      title?: string;
      description?: string;
      status?: 'disconnected' | 'connected' | 'disabled';
      fields?: Array<{
        name: string;
        value: string;
        type?: string;
      }>;
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      fillColor?: string;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {
      data: {
        title: data.title || 'sample app card item',
        description: data.description,
        status: data.status || 'disconnected',
      },
      style: {
        fillColor: data.fillColor || '#2d9bf0',
      },
    };

    if (data.fields && data.fields.length > 0) {
      payload.data.fields = data.fields;
    }

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x || 0,
        y: data.y || 0,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId) {
      payload.parent = {
        id: data.parentId,
      };
    }

    return this.makeRequest(`/boards/${boardId}/app_cards`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getAppCard(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/app_cards/${itemId}`, {
      method: 'GET',
    });
  }

  async updateAppCard(
    boardId: string,
    itemId: string,
    data: {
      title?: string;
      description?: string;
      status?: 'disconnected' | 'connected' | 'disabled';
      fields?: Array<{
        name: string;
        value: string;
        type?: string;
      }>;
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      fillColor?: string;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {};

    if (
      data.title !== undefined ||
      data.description !== undefined ||
      data.status !== undefined ||
      data.fields !== undefined
    ) {
      payload.data = {};
      if (data.title !== undefined) payload.data.title = data.title;
      if (data.description !== undefined) payload.data.description = data.description;
      if (data.status !== undefined) payload.data.status = data.status;
      if (data.fields !== undefined) payload.data.fields = data.fields;
    }

    if (data.fillColor !== undefined) {
      payload.style = {
        fillColor: data.fillColor,
      };
    }

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x,
        y: data.y,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId !== undefined) {
      payload.parent = data.parentId ? { id: data.parentId } : null;
    }

    return this.makeRequest(`/boards/${boardId}/app_cards/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteAppCard(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/app_cards/${itemId}`, {
      method: 'DELETE',
    });
  }
  // End ======
  // ================== APP CARD ITEMS ==================

  // ================== CARD ITEMS ==================
  // START ======
  async createCard(
    boardId: string,
    data: {
      title?: string;
      description?: string;
      assigneeId?: string;
      dueDate?: string;
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      cardTheme?: string;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {
      data: {
        title: data.title || 'sample card item',
      },
      style: {
        cardTheme: data.cardTheme || '#2d9bf0',
      },
    };

    if (data.description !== undefined) payload.data.description = data.description;
    if (data.assigneeId !== undefined) payload.data.assigneeId = data.assigneeId;
    if (data.dueDate !== undefined) payload.data.dueDate = data.dueDate;

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x || 0,
        y: data.y || 0,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId) {
      payload.parent = {
        id: data.parentId,
      };
    }

    return this.makeRequest(`/boards/${boardId}/cards`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getCard(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/cards/${itemId}`, {
      method: 'GET',
    });
  }

  async updateCard(
    boardId: string,
    itemId: string,
    data: {
      title?: string;
      description?: string;
      assigneeId?: string;
      dueDate?: string;
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      cardTheme?: string;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {};

    if (
      data.title !== undefined ||
      data.description !== undefined ||
      data.assigneeId !== undefined ||
      data.dueDate !== undefined
    ) {
      payload.data = {};
      if (data.title !== undefined) payload.data.title = data.title;
      if (data.description !== undefined) payload.data.description = data.description;
      if (data.assigneeId !== undefined) payload.data.assigneeId = data.assigneeId;
      if (data.dueDate !== undefined) payload.data.dueDate = data.dueDate;
    }

    if (data.cardTheme !== undefined) {
      payload.style = {
        cardTheme: data.cardTheme,
      };
    }

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x,
        y: data.y,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId !== undefined) {
      payload.parent = data.parentId ? { id: data.parentId } : null;
    }

    return this.makeRequest(`/boards/${boardId}/cards/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteCard(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/cards/${itemId}`, {
      method: 'DELETE',
    });
  }
  // End ======
  // ================== CARD ITEMS ==================

  // ================== SHAPE ITEMS ==================
  // START ======
  async createShape(
    boardId: string,
    data: {
      content?: string;
      shape?:
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
        | 'wedge_round_rectangle_callout'
        | 'star'
        | 'flow_chart_predefined_process'
        | 'cloud'
        | 'cross'
        | 'can'
        | 'right_arrow'
        | 'left_arrow'
        | 'left_right_arrow'
        | 'left_brace'
        | 'right_brace';
      borderColor?: string;
      borderOpacity?: number;
      borderStyle?: 'normal' | 'dotted' | 'dashed';
      borderWidth?: number;
      color?: string;
      fillColor?: string;
      fillOpacity?: number;
      fontFamily?: string;
      fontSize?: number;
      textAlign?: 'left' | 'center' | 'right';
      textAlignVertical?: 'top' | 'middle' | 'bottom';
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {
      data: {
        content: data.content || '',
        shape: data.shape || 'rectangle',
      },
      style: {
        borderColor: data.borderColor || '#1a1a1a',
        borderOpacity:
          data.borderOpacity !== undefined
            ? data.borderOpacity.toString()
            : data.borderColor
              ? '1.0'
              : '0.0',
        borderStyle: data.borderStyle || 'normal',
        borderWidth: data.borderWidth !== undefined ? data.borderWidth.toString() : '2.0',
        color: data.color || '#1a1a1a',
        fillColor: data.fillColor || '#ffffff',
        fillOpacity:
          data.fillOpacity !== undefined
            ? data.fillOpacity.toString()
            : data.fillColor
              ? '1.0'
              : '0.0',
        fontFamily: data.fontFamily || 'arial',
        fontSize: data.fontSize !== undefined ? data.fontSize.toString() : '14',
        textAlign: data.textAlign || 'center',
        textAlignVertical: data.textAlignVertical || 'top',
      },
    };

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x || 0,
        y: data.y || 0,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId) {
      payload.parent = {
        id: data.parentId,
      };
    }

    return this.makeRequest(`/boards/${boardId}/shapes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getShape(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/shapes/${itemId}`, {
      method: 'GET',
    });
  }

  async updateShape(
    boardId: string,
    itemId: string,
    data: {
      content?: string;
      shape?:
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
        | 'wedge_round_rectangle_callout'
        | 'star'
        | 'flow_chart_predefined_process'
        | 'cloud'
        | 'cross'
        | 'can'
        | 'right_arrow'
        | 'left_arrow'
        | 'left_right_arrow'
        | 'left_brace'
        | 'right_brace';
      borderColor?: string;
      borderOpacity?: number;
      borderStyle?: 'normal' | 'dotted' | 'dashed';
      borderWidth?: number;
      color?: string;
      fillColor?: string;
      fillOpacity?: number;
      fontFamily?: string;
      fontSize?: number;
      textAlign?: 'left' | 'center' | 'right';
      textAlignVertical?: 'top' | 'middle' | 'bottom';
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      rotation?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {};

    if (data.content !== undefined || data.shape !== undefined) {
      payload.data = {};
      if (data.content !== undefined) payload.data.content = data.content;
      if (data.shape !== undefined) payload.data.shape = data.shape;
    }

    if (
      data.borderColor !== undefined ||
      data.borderOpacity !== undefined ||
      data.borderStyle !== undefined ||
      data.borderWidth !== undefined ||
      data.color !== undefined ||
      data.fillColor !== undefined ||
      data.fillOpacity !== undefined ||
      data.fontFamily !== undefined ||
      data.fontSize !== undefined ||
      data.textAlign !== undefined ||
      data.textAlignVertical !== undefined
    ) {
      payload.style = {};
      if (data.borderColor !== undefined) payload.style.borderColor = data.borderColor;
      if (data.borderOpacity !== undefined)
        payload.style.borderOpacity = data.borderOpacity.toString();
      if (data.borderStyle !== undefined) payload.style.borderStyle = data.borderStyle;
      if (data.borderWidth !== undefined) payload.style.borderWidth = data.borderWidth.toString();
      if (data.color !== undefined) payload.style.color = data.color;
      if (data.fillColor !== undefined) payload.style.fillColor = data.fillColor;
      if (data.fillOpacity !== undefined) payload.style.fillOpacity = data.fillOpacity.toString();
      if (data.fontFamily !== undefined) payload.style.fontFamily = data.fontFamily;
      if (data.fontSize !== undefined) payload.style.fontSize = data.fontSize.toString();
      if (data.textAlign !== undefined) payload.style.textAlign = data.textAlign;
      if (data.textAlignVertical !== undefined)
        payload.style.textAlignVertical = data.textAlignVertical;
    }

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x,
        y: data.y,
      };
    }

    if (data.width || data.height || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height) payload.geometry.height = data.height;
      if (data.rotation !== undefined) payload.geometry.rotation = data.rotation;
    }

    if (data.parentId !== undefined) {
      payload.parent = data.parentId ? { id: data.parentId } : null;
    }

    return this.makeRequest(`/boards/${boardId}/shapes/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteShape(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/shapes/${itemId}`, {
      method: 'DELETE',
    });
  }
  // End ======
  // ================== SHAPE ITEMS ==================

  // ================== STICKY NOTE ITEMS ==================
  // START ======
  async createStickyNote(
    boardId: string,
    data: {
      content: string;
      shape?: 'square' | 'rectangle';
      fillColor?:
        | 'gray'
        | 'light_yellow'
        | 'yellow'
        | 'orange'
        | 'light_green'
        | 'green'
        | 'dark_green'
        | 'cyan'
        | 'light_pink'
        | 'pink'
        | 'violet'
        | 'red'
        | 'light_blue'
        | 'blue'
        | 'dark_blue'
        | 'black';
      textAlign?: 'left' | 'center' | 'right';
      textAlignVertical?: 'top' | 'middle' | 'bottom';
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {
      data: {
        content: data.content,
        shape: data.shape || 'square',
      },
      style: {
        fillColor: data.fillColor || 'light_yellow',
        textAlign: data.textAlign || 'center',
        textAlignVertical: data.textAlignVertical || 'top',
      },
    };

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x || 0,
        y: data.y || 0,
      };
    }

    if (data.width || data.height) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height && !data.width) payload.geometry.height = data.height;
    }

    if (data.parentId) {
      payload.parent = {
        id: data.parentId,
      };
    }

    return this.makeRequest(`/boards/${boardId}/sticky_notes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getStickyNote(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/sticky_notes/${itemId}`, {
      method: 'GET',
    });
  }

  async updateStickyNote(
    boardId: string,
    itemId: string,
    data: {
      content?: string;
      shape?: 'square' | 'rectangle';
      fillColor?:
        | 'gray'
        | 'light_yellow'
        | 'yellow'
        | 'orange'
        | 'light_green'
        | 'green'
        | 'dark_green'
        | 'cyan'
        | 'light_pink'
        | 'pink'
        | 'violet'
        | 'red'
        | 'light_blue'
        | 'blue'
        | 'dark_blue'
        | 'black';
      textAlign?: 'left' | 'center' | 'right';
      textAlignVertical?: 'top' | 'middle' | 'bottom';
      x?: number;
      y?: number;
      width?: number;
      height?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {};

    if (data.content !== undefined || data.shape !== undefined) {
      payload.data = {};
      if (data.content !== undefined) payload.data.content = data.content;
      if (data.shape !== undefined) payload.data.shape = data.shape;
    }

    if (
      data.fillColor !== undefined ||
      data.textAlign !== undefined ||
      data.textAlignVertical !== undefined
    ) {
      payload.style = {};
      if (data.fillColor !== undefined) payload.style.fillColor = data.fillColor;
      if (data.textAlign !== undefined) payload.style.textAlign = data.textAlign;
      if (data.textAlignVertical !== undefined)
        payload.style.textAlignVertical = data.textAlignVertical;
    }

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x,
        y: data.y,
      };
    }

    if (data.width || data.height) {
      payload.geometry = {};
      if (data.width) payload.geometry.width = data.width;
      if (data.height && !data.width) payload.geometry.height = data.height;
    }

    if (data.parentId !== undefined) {
      payload.parent = data.parentId ? { id: data.parentId } : null;
    }

    return this.makeRequest(`/boards/${boardId}/sticky_notes/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteStickyNote(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/sticky_notes/${itemId}`, {
      method: 'DELETE',
    });
  }
  // End ======
  // ================== STICKY NOTE ITEMS ==================

  // ================== TEXT ITEMS ==================
  // START ======
  async createText(
    boardId: string,
    data: {
      content: string;
      color?: string;
      fillColor?: string;
      fillOpacity?: number;
      fontFamily?: string;
      fontSize?: number;
      textAlign?: 'left' | 'center' | 'right';
      x?: number;
      y?: number;
      width?: number;
      rotation?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {
      data: {
        content: data.content,
      },
      style: {
        color: data.color || '#1a1a1a',
        fillColor: data.fillColor || '#ffffff',
        fillOpacity:
          data.fillOpacity !== undefined
            ? data.fillOpacity.toString()
            : data.fillColor
              ? '1.0'
              : '0.0',
        fontFamily: data.fontFamily || 'arial',
        fontSize: data.fontSize !== undefined ? data.fontSize.toString() : '14',
        textAlign: data.textAlign || 'center',
      },
    };

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x || 0,
        y: data.y || 0,
      };
    }

    if (data.width || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) {
        const minWidth = (data.fontSize || 14) * 1.7;
        payload.geometry.width = Math.max(data.width, minWidth);
      }
      if (data.rotation !== undefined) {
        payload.geometry.rotation = data.rotation;
      }
    }

    if (data.parentId) {
      payload.parent = {
        id: data.parentId,
      };
    }

    return this.makeRequest(`/boards/${boardId}/texts`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getText(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/texts/${itemId}`, {
      method: 'GET',
    });
  }

  async updateText(
    boardId: string,
    itemId: string,
    data: {
      content?: string;
      color?: string;
      fillColor?: string;
      fillOpacity?: number;
      fontFamily?: string;
      fontSize?: number;
      textAlign?: 'left' | 'center' | 'right';
      x?: number;
      y?: number;
      width?: number;
      rotation?: number;
      parentId?: string;
    },
  ): Promise<any> {
    const payload: any = {};

    if (data.content !== undefined) {
      payload.data = {
        content: data.content,
      };
    }

    if (
      data.color !== undefined ||
      data.fillColor !== undefined ||
      data.fillOpacity !== undefined ||
      data.fontFamily !== undefined ||
      data.fontSize !== undefined ||
      data.textAlign !== undefined
    ) {
      payload.style = {};
      if (data.color !== undefined) payload.style.color = data.color;
      if (data.fillColor !== undefined) payload.style.fillColor = data.fillColor;
      if (data.fillOpacity !== undefined) payload.style.fillOpacity = data.fillOpacity.toString();
      if (data.fontFamily !== undefined) payload.style.fontFamily = data.fontFamily;
      if (data.fontSize !== undefined) payload.style.fontSize = data.fontSize.toString();
      if (data.textAlign !== undefined) payload.style.textAlign = data.textAlign;
    }

    if (data.x !== undefined || data.y !== undefined) {
      payload.position = {
        x: data.x,
        y: data.y,
      };
    }

    if (data.width || data.rotation !== undefined) {
      payload.geometry = {};
      if (data.width) {
        const minWidth = (data.fontSize || 14) * 1.7;
        payload.geometry.width = Math.max(data.width, minWidth);
      }
      if (data.rotation !== undefined) {
        payload.geometry.rotation = data.rotation;
      }
    }

    if (data.parentId !== undefined) {
      payload.parent = data.parentId ? { id: data.parentId } : null;
    }

    return this.makeRequest(`/boards/${boardId}/texts/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteText(boardId: string, itemId: string): Promise<any> {
    return this.makeRequest(`/boards/${boardId}/texts/${itemId}`, {
      method: 'DELETE',
    });
  }
  // End ======
  // ================== TEXT ITEMS ==================
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

// ================== BOARDS ==================
// START ======
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
// END ======
// ================== BOARDS ==================

// ================== BOARD MEMBERS ==================
// START ======
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
// END ======
// ================== BOARD MEMBERS ==================

// ================== ITEMS ==================
// START ======
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
// END ======
// ================== ITEMS ==================

// ================== APP CARD ITEMS ==================
// START ======
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
// END ======
// ================== APP CARD ITEMS ==================

// ================== CARD ITEMS ==================
// START ======
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
// END ======
// ================== CARD ITEMS ==================

// ================== SHAPE ITEMS ==================
// START ======
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
// END ======
// ================== SHAPE ITEMS ==================

// ================== STICKY NOTE ITEMS ==================
// START ======
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
// END ======
// ================== STICKY NOTE ITEMS ==================

// ================== TEXT ITEMS ==================
// START ======
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
// End ======
// ================== TEXT ITEMS ==================

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
          GET_SPECIFIC_BOARD_TOOL,
          GET_BOARD_ITEMS_TOOL,
          GET_SPECIFIC_BOARD_ITEM_TOOL,
          UPDATE_ITEM_POSITION_TOOL,
          DELETE_BOARD_ITEM_TOOL,
          GET_BOARD_MEMBERS_TOOL,
          UPDATE_BOARD_MEMBER_ROLE_TOOL,
          REMOVE_BOARD_MEMBER_TOOL,
          ADD_APP_CARD_TOOL,
          GET_APP_CARD_TOOL,
          UPDATE_APP_CARD_TOOL,
          DELETE_APP_CARD_TOOL,
          ADD_CARD_TOOL,
          GET_CARD_TOOL,
          UPDATE_CARD_TOOL,
          DELETE_CARD_TOOL,
          ADD_SHAPE_TOOL,
          GET_SHAPE_TOOL,
          UPDATE_SHAPE_TOOL,
          DELETE_SHAPE_TOOL,
          ADD_STICKY_NOTE_TOOL,
          GET_STICKY_NOTE_TOOL,
          UPDATE_STICKY_NOTE_TOOL,
          DELETE_STICKY_NOTE_TOOL,
          ADD_TEXT_TOOL,
          GET_TEXT_TOOL,
          UPDATE_TEXT_TOOL,
          DELETE_TEXT_TOOL,
        ],
      };
    });

    mcpServerInstance.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          // ================== BOARDS ==================
          // START ======
          case 'miro_create_board': {
            const client = getMiroClient();
            const result = await client.createBoard({
              name: (args as any)?.name,
              description: (args as any)?.description,
              sharingPolicy: (args as any)?.access
                ? {
                    access: (args as any)?.access,
                  }
                : undefined,
              teamId: (args as any)?.teamId,
              projectId: (args as any)?.projectId,
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

          case 'miro_get_specific_board': {
            const client = getMiroClient();
            const result = await client.getSpecificBoard((args as any)?.board_id);

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

            let policy: any = undefined;

            const hasSharingPolicy =
              (args as any)?.access ||
              (args as any)?.invite_to_account_and_board_link_access ||
              (args as any)?.organization_access ||
              (args as any)?.team_access;

            const hasPermissionsPolicy =
              (args as any)?.collaboration_tools_start_access ||
              (args as any)?.copy_access ||
              (args as any)?.sharing_access;

            if (hasSharingPolicy || hasPermissionsPolicy) {
              policy = {};

              if (hasSharingPolicy) {
                policy.sharingPolicy = {};
                if ((args as any)?.access) policy.sharingPolicy.access = (args as any).access;
                if ((args as any)?.invite_to_account_and_board_link_access) {
                  policy.sharingPolicy.inviteToAccountAndBoardLinkAccess = (
                    args as any
                  ).invite_to_account_and_board_link_access;
                }
                if ((args as any)?.organization_access)
                  policy.sharingPolicy.organizationAccess = (args as any).organization_access;
                if ((args as any)?.team_access)
                  policy.sharingPolicy.teamAccess = (args as any).team_access;
              }

              if (hasPermissionsPolicy) {
                policy.permissionsPolicy = {};
                if ((args as any)?.collaboration_tools_start_access) {
                  policy.permissionsPolicy.collaborationToolsStartAccess = (
                    args as any
                  ).collaboration_tools_start_access;
                }
                if ((args as any)?.copy_access)
                  policy.permissionsPolicy.copyAccess = (args as any).copy_access;
                if ((args as any)?.sharing_access)
                  policy.permissionsPolicy.sharingAccess = (args as any).sharing_access;
              }
            }

            const result = await client.updateBoard((args as any)?.board_id, {
              name: (args as any)?.name,
              description: (args as any)?.description,
              teamId: (args as any)?.team_id,
              projectId: (args as any)?.project_id,
              policy: policy,
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
          // End ======
          // ================== BOARDS ==================

          // ================== BOARD MEMBERS ==================
          // START ======
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
          // End ======
          // ================== BOARD MEMBERS ==================

          // ================== ITEMS ==================
          // START ======
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

          case 'miro_get_specific_board_item': {
            const client = getMiroClient();
            const result = await client.getSpecificBoardItem(
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

          case 'miro_update_item_position': {
            const client = getMiroClient();

            const position =
              (args as any)?.x !== undefined || (args as any)?.y !== undefined
                ? {
                    x: (args as any)?.x,
                    y: (args as any)?.y,
                  }
                : undefined;

            let parentId: string | null | undefined = undefined;

            if ((args as any)?.attach_to_canvas === true) {
              parentId = null;
            } else if ((args as any)?.parent_id !== undefined) {
              parentId = (args as any)?.parent_id === 'null' ? null : (args as any)?.parent_id;
            }

            const result = await client.updateItemPosition(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                position: position,
                parentId: parentId,
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
          // End ======
          // ================== ITEMS ==================

          // ================== APP CARD ITEMS ==================
          // START ======
          case 'miro_add_app_card_item': {
            const client = getMiroClient();
            const result = await client.createAppCard((args as any)?.board_id, {
              title: (args as any)?.title,
              description: (args as any)?.description,
              status: (args as any)?.status,
              fields: (args as any)?.fields,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              rotation: (args as any)?.rotation,
              fillColor: (args as any)?.fill_color,
              parentId: (args as any)?.parent_id,
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

          case 'miro_get_app_card_item': {
            const client = getMiroClient();
            const result = await client.getAppCard((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_app_card_item': {
            const client = getMiroClient();
            const result = await client.updateAppCard(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                title: (args as any)?.title,
                description: (args as any)?.description,
                status: (args as any)?.status,
                fields: (args as any)?.fields,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                rotation: (args as any)?.rotation,
                fillColor: (args as any)?.fill_color,
                parentId: (args as any)?.parent_id,
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

          case 'miro_delete_app_card_item': {
            const client = getMiroClient();
            const result = await client.deleteAppCard(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: 'App card deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== APP CARD ITEMS ==================

          // ================== CARD ITEMS ==================
          // START ======
          case 'miro_add_card_item': {
            const client = getMiroClient();
            const result = await client.createCard((args as any)?.board_id, {
              title: (args as any)?.title,
              description: (args as any)?.description,
              assigneeId: (args as any)?.assignee_id,
              dueDate: (args as any)?.due_date,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              rotation: (args as any)?.rotation,
              cardTheme: (args as any)?.card_theme,
              parentId: (args as any)?.parent_id,
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

          case 'miro_get_card_item': {
            const client = getMiroClient();
            const result = await client.getCard((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_card_item': {
            const client = getMiroClient();
            const result = await client.updateCard(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                title: (args as any)?.title,
                description: (args as any)?.description,
                assigneeId: (args as any)?.assignee_id,
                dueDate: (args as any)?.due_date,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                rotation: (args as any)?.rotation,
                cardTheme: (args as any)?.card_theme,
                parentId: (args as any)?.parent_id,
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

          case 'miro_delete_card_item': {
            const client = getMiroClient();
            const result = await client.deleteCard((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: 'Card deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== CARD ITEMS ==================

          // ================== SHAPE ITEMS ==================
          // START ======
          case 'miro_add_shape': {
            const client = getMiroClient();
            const result = await client.createShape((args as any)?.board_id, {
              content: (args as any)?.content,
              shape: (args as any)?.shape,
              borderColor: (args as any)?.border_color,
              borderOpacity: (args as any)?.border_opacity,
              borderStyle: (args as any)?.border_style,
              borderWidth: (args as any)?.border_width,
              color: (args as any)?.color,
              fillColor: (args as any)?.fill_color,
              fillOpacity: (args as any)?.fill_opacity,
              fontFamily: (args as any)?.font_family,
              fontSize: (args as any)?.font_size,
              textAlign: (args as any)?.text_align,
              textAlignVertical: (args as any)?.text_align_vertical,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              rotation: (args as any)?.rotation,
              parentId: (args as any)?.parent_id,
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

          case 'miro_get_shape': {
            const client = getMiroClient();
            const result = await client.getShape((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_shape': {
            const client = getMiroClient();
            const result = await client.updateShape(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                content: (args as any)?.content,
                shape: (args as any)?.shape,
                borderColor: (args as any)?.border_color,
                borderOpacity: (args as any)?.border_opacity,
                borderStyle: (args as any)?.border_style,
                borderWidth: (args as any)?.border_width,
                color: (args as any)?.color,
                fillColor: (args as any)?.fill_color,
                fillOpacity: (args as any)?.fill_opacity,
                fontFamily: (args as any)?.font_family,
                fontSize: (args as any)?.font_size,
                textAlign: (args as any)?.text_align,
                textAlignVertical: (args as any)?.text_align_vertical,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                rotation: (args as any)?.rotation,
                parentId: (args as any)?.parent_id,
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

          case 'miro_delete_shape': {
            const client = getMiroClient();
            const result = await client.deleteShape(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: 'Shape deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== SHAPE ITEMS ==================

          // ================== STICKY NOTE ITEMS ==================
          // START ======
          case 'miro_add_sticky_note': {
            const client = getMiroClient();
            const result = await client.createStickyNote((args as any)?.board_id, {
              content: (args as any)?.content,
              shape: (args as any)?.shape,
              fillColor: (args as any)?.fill_color,
              textAlign: (args as any)?.text_align,
              textAlignVertical: (args as any)?.text_align_vertical,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              height: (args as any)?.height,
              parentId: (args as any)?.parent_id,
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

          case 'miro_get_sticky_note': {
            const client = getMiroClient();
            const result = await client.getStickyNote(
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

          case 'miro_update_sticky_note': {
            const client = getMiroClient();
            const result = await client.updateStickyNote(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                content: (args as any)?.content,
                shape: (args as any)?.shape,
                fillColor: (args as any)?.fill_color,
                textAlign: (args as any)?.text_align,
                textAlignVertical: (args as any)?.text_align_vertical,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                height: (args as any)?.height,
                parentId: (args as any)?.parent_id,
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

          case 'miro_delete_sticky_note': {
            const client = getMiroClient();
            const result = await client.deleteStickyNote(
              (args as any)?.board_id,
              (args as any)?.item_id,
            );

            return {
              content: [
                {
                  type: 'text',
                  text: 'Sticky note deleted successfully',
                },
              ],
            };
          }
          // End ======
          // ================== STICKY NOTE ITEMS ==================

          // ================== TEXT ITEMS ==================
          // START ======
          case 'miro_add_text_item': {
            const client = getMiroClient();
            const result = await client.createText((args as any)?.board_id, {
              content: (args as any)?.content,
              color: (args as any)?.color,
              fillColor: (args as any)?.fill_color,
              fillOpacity: (args as any)?.fill_opacity,
              fontFamily: (args as any)?.font_family,
              fontSize: (args as any)?.font_size,
              textAlign: (args as any)?.text_align,
              x: (args as any)?.x,
              y: (args as any)?.y,
              width: (args as any)?.width,
              rotation: (args as any)?.rotation,
              parentId: (args as any)?.parent_id,
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

          case 'miro_get_text_item': {
            const client = getMiroClient();
            const result = await client.getText((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case 'miro_update_text_item': {
            const client = getMiroClient();
            const result = await client.updateText(
              (args as any)?.board_id,
              (args as any)?.item_id,
              {
                content: (args as any)?.content,
                color: (args as any)?.color,
                fillColor: (args as any)?.fill_color,
                fillOpacity: (args as any)?.fill_opacity,
                fontFamily: (args as any)?.font_family,
                fontSize: (args as any)?.font_size,
                textAlign: (args as any)?.text_align,
                x: (args as any)?.x,
                y: (args as any)?.y,
                width: (args as any)?.width,
                rotation: (args as any)?.rotation,
                parentId: (args as any)?.parent_id,
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

          case 'miro_delete_text_item': {
            const client = getMiroClient();
            const result = await client.deleteText((args as any)?.board_id, (args as any)?.item_id);

            return {
              content: [
                {
                  type: 'text',
                  text: 'Text deleted successfully',
                },
              ],
            };
          }

          // End ======
          // ================== TEXT ITEMS ==================

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
