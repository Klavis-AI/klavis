import { MiroClient } from '../../client/miroClient.js';

export class CardHandler {
  constructor(private miroClient: MiroClient) {}

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

    return this.miroClient.makeRequest(`/boards/${boardId}/cards`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getCard(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/cards/${itemId}`, {
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

    return this.miroClient.makeRequest(`/boards/${boardId}/cards/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteCard(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/cards/${itemId}`, {
      method: 'DELETE',
    });
  }
}
