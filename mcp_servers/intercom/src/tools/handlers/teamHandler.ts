import { IntercomClient } from '../../client/intercomClient.js';
import { validateTeamId, validateAdminId, validateRequiredFields } from '../../utils/validation.js';

export class TeamHandler {
  constructor(private intercomClient: IntercomClient) {}

  async listTeams(): Promise<any> {
    return this.intercomClient.makeRequest('/teams', {
      method: 'GET',
    });
  }

  async getTeam(teamId: string): Promise<any> {
    if (!validateTeamId(teamId)) {
      throw new Error('Invalid team ID provided');
    }

    return this.intercomClient.makeRequest(`/teams/${teamId}`, {
      method: 'GET',
    });
  }

  async listAdmins(): Promise<any> {
    return this.intercomClient.makeRequest('/admins', {
      method: 'GET',
    });
  }

  async getAdmin(adminId: number): Promise<any> {
    if (!validateAdminId(adminId.toString())) {
      throw new Error('Invalid admin ID provided');
    }

    return this.intercomClient.makeRequest(`/admins/${adminId}`, {
      method: 'GET',
    });
  }

  async getCurrentAdmin(): Promise<any> {
    return this.intercomClient.makeRequest('/me', {
      method: 'GET',
    });
  }

  async setAdminAway(
    adminId: number,
    data: {
      awayModeEnabled: boolean;
      awayModeReassign: boolean;
    },
  ): Promise<any> {
    if (!validateAdminId(adminId.toString())) {
      throw new Error('Invalid admin ID provided');
    }

    const validation = validateRequiredFields(data, ['awayModeEnabled', 'awayModeReassign']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload = {
      away_mode_enabled: data.awayModeEnabled,
      away_mode_reassign: data.awayModeReassign,
    };

    return this.intercomClient.makeRequest(`/admins/${adminId}/away`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async listAdminActivityLogs(data: {
    createdAtAfter: string;
    createdAtBefore?: string;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['createdAtAfter']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const params = new URLSearchParams();
    params.append('created_at_after', data.createdAtAfter);

    if (data.createdAtBefore) {
      params.append('created_at_before', data.createdAtBefore);
    }

    return this.intercomClient.makeRequest(`/admins/activity_logs?${params.toString()}`, {
      method: 'GET',
    });
  }
}
