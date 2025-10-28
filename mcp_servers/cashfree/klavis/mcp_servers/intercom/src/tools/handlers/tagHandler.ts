import { IntercomClient } from '../../client/intercomClient.js';
import {
  validateTagId,
  validateContactId,
  validateRequiredFields,
} from '../../utils/validation.js';

export class TagHandler {
  constructor(private intercomClient: IntercomClient) {}

  async listTags(): Promise<any> {
    return this.intercomClient.makeRequest('/tags', {
      method: 'GET',
    });
  }

  async getTag(tagId: string): Promise<any> {
    if (!validateTagId(tagId)) {
      throw new Error('Invalid tag ID provided');
    }

    return this.intercomClient.makeRequest(`/tags/${tagId}`, {
      method: 'GET',
    });
  }

  async createOrUpdateTag(data: { name: string; id?: string }): Promise<any> {
    const validation = validateRequiredFields(data, ['name']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload: any = {
      name: data.name,
    };

    if (data.id !== undefined) {
      payload.id = data.id;
    }

    return this.intercomClient.makeRequest('/tags', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async tagCompanies(data: {
    name: string;
    companies: Array<{
      id?: string;
      companyId?: string;
    }>;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['name', 'companies']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!Array.isArray(data.companies) || data.companies.length === 0) {
      throw new Error('At least one company must be provided');
    }

    // Validate each company has either id or companyId
    for (const company of data.companies) {
      if (!company.id && !company.companyId) {
        throw new Error('Each company must have either id or company_id');
      }
    }

    const payload = {
      name: data.name,
      companies: data.companies.map((company) => {
        const companyData: any = {};
        if (company.id) companyData.id = company.id;
        if (company.companyId) companyData.company_id = company.companyId;
        return companyData;
      }),
    };

    return this.intercomClient.makeRequest('/tags', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async untagCompanies(data: {
    name: string;
    companies: Array<{
      id?: string;
      companyId?: string;
    }>;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['name', 'companies']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!Array.isArray(data.companies) || data.companies.length === 0) {
      throw new Error('At least one company must be provided');
    }

    // Validate each company has either id or companyId
    for (const company of data.companies) {
      if (!company.id && !company.companyId) {
        throw new Error('Each company must have either id or company_id');
      }
    }

    const payload = {
      name: data.name,
      companies: data.companies.map((company) => {
        const companyData: any = {};
        if (company.id) companyData.id = company.id;
        if (company.companyId) companyData.company_id = company.companyId;
        return companyData;
      }),
      untag: true,
    };

    return this.intercomClient.makeRequest('/tags', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async tagUsers(data: {
    name: string;
    users: Array<{
      id: string;
    }>;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['name', 'users']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!Array.isArray(data.users) || data.users.length === 0) {
      throw new Error('At least one user must be provided');
    }

    // Validate each user has a valid ID
    for (const user of data.users) {
      if (!user.id || !validateContactId(user.id)) {
        throw new Error('Each user must have a valid ID');
      }
    }

    const payload = {
      name: data.name,
      users: data.users,
    };

    return this.intercomClient.makeRequest('/tags', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async deleteTag(tagId: string): Promise<any> {
    if (!validateTagId(tagId)) {
      throw new Error('Invalid tag ID provided');
    }

    return this.intercomClient.makeRequest(`/tags/${tagId}`, {
      method: 'DELETE',
    });
  }
}
