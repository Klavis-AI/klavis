import { MiroClient } from '../../client/miroClient.js';

export class StickyNoteHandler {
  constructor(private miroClient: MiroClient) {}

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

    return this.miroClient.makeRequest(`/boards/${boardId}/sticky_notes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getStickyNote(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/sticky_notes/${itemId}`, {
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

    return this.miroClient.makeRequest(`/boards/${boardId}/sticky_notes/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteStickyNote(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/sticky_notes/${itemId}`, {
      method: 'DELETE',
    });
  }
}
