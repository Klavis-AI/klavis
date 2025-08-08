import { MiroClient } from '../../client/miroClient.js';

export class ItemHandler {
  constructor(private miroClient: MiroClient) {}

  async getBoardItems(boardId: string, limit: number = 50, type?: string): Promise<any> {
    let endpoint = `/boards/${boardId}/items?limit=${limit}`;
    if (type) {
      endpoint += `&type=${type}`;
    }
    return this.miroClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getSpecificBoardItem(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'GET',
    });
  }

  async updateItemPosition(
    boardId: string,
    itemId: string,
    data: {
      position?: { x: number; y: number };
      parentId?: string | null;
    }
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

    return this.miroClient.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteBoardItem(boardId: string, itemId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/items/${itemId}`, {
      method: 'DELETE',
    });
  }
}
