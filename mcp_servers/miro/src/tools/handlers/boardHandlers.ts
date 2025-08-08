import { MiroClient } from '../../client/miroClient.js';

export class BoardHandler {
  constructor(private miroClient: MiroClient) {}

  async getBoards(limit: number = 25, teamId?: string): Promise<any> {
    let endpoint = `/boards?limit=${limit}`;
    if (teamId) {
      endpoint += `&team_id=${teamId}`;
    }
    return this.miroClient.makeRequest(endpoint, {
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

    return this.miroClient.makeRequest('/boards', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getSpecificBoard(boardId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}`, {
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
    }
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

    return this.miroClient.makeRequest(`/boards/${boardId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteBoard(boardId: string): Promise<any> {
    return this.miroClient.makeRequest(`/boards/${boardId}`, {
      method: 'DELETE',
    });
  }
}
