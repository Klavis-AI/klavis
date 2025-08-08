import { MiroClient } from '../../client/miroClient.js';

export class AppCardHandler {
  constructor(private miroClient: MiroClient) {}

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
    }
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

    return this.miroClient.makeRequest(`/boards/${boardId}/app_cards`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getAppCard(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/app_cards/${itemId}`, {
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
    }
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

    return this.miroClient.makeRequest(`/boards/${boardId}/app_cards/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteAppCard(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/app_cards/${itemId}`, {
      method: 'DELETE',
    });
  }
}
