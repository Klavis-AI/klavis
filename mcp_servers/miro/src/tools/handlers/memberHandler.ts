import { MiroClient } from '../../client/miroClient.js';

export class MemberHandler {
  constructor(private miroClient: MiroClient) {}

  async getBoardMembers(boardId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/members`, {
      method: 'GET',
    });
  }

  async updateBoardMemberRole(
    boardId: string,
    userId: string,
    role: 'viewer' | 'commenter' | 'editor' | 'coowner' | 'owner'
  ): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/members/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        role,
      }),
    });
  }

  async removeBoardMember(boardId: string, userId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}/members/${userId}`, {
      method: 'DELETE',
    });
  }
}
