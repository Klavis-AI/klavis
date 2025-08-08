import { MiroClient } from '../../client/miroClient.js';

export class TextHandler {
  constructor(private miroClient: MiroClient) {}

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
    }
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

    return this.miroClient.makeRequest(`/boards/${boardId}/texts`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getText(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/texts/${itemId}`, {
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
    }
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

    return this.miroClient.makeRequest(`/boards/${boardId}/texts/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteText(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/texts/${itemId}`, {
      method: 'DELETE',
    });
  }
}
