import { IntercomClient } from '../../client/intercomClient.js';
import {
  validateCompanyId,
  validateContactId,
  validateRequiredFields,
  validateUrl,
} from '../../utils/validation.js';

export class CompanyHandler {
  constructor(private intercomClient: IntercomClient) {}

  async listCompanies(data: {
    startingAfter?: string;
    perPage?: number;
    order?: 'asc' | 'desc';
  }): Promise<any> {
    const params = new URLSearchParams();

    if (data.startingAfter) {
      params.append('starting_after', data.startingAfter);
    }

    if (data.perPage) {
      params.append('per_page', data.perPage.toString());
    }

    if (data.order) {
      params.append('order', data.order);
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/companies?${queryString}` : '/companies';

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getCompany(companyId: string): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    return this.intercomClient.makeRequest(`/companies/${companyId}`, {
      method: 'GET',
    });
  }

  async createCompany(data: {
    name?: string;
    companyId?: string;
    plan?: string;
    size?: number;
    website?: string;
    industry?: string;
    remoteCreatedAt?: number;
    monthlySpend?: number;
    customAttributes?: Record<string, any>;
  }): Promise<any> {
    // At least one of name or companyId is required
    if (!data.name && !data.companyId) {
      throw new Error('At least one of name or company_id must be provided');
    }

    const payload: any = {};

    if (data.name !== undefined) payload.name = data.name;
    if (data.companyId !== undefined) payload.company_id = data.companyId;
    if (data.plan !== undefined) payload.plan = data.plan;
    if (data.size !== undefined) payload.size = data.size;
    if (data.website !== undefined) {
      if (data.website && !validateUrl(data.website)) {
        throw new Error('Invalid website URL format provided');
      }
      payload.website = data.website;
    }
    if (data.industry !== undefined) payload.industry = data.industry;
    if (data.remoteCreatedAt !== undefined) payload.remote_created_at = data.remoteCreatedAt;
    if (data.monthlySpend !== undefined) {
      // Validate monthly spend is within integer limits
      if (data.monthlySpend > 2147483647) {
        throw new Error('Monthly spend exceeds maximum allowed value (2147483647)');
      }
      payload.monthly_spend = Math.floor(data.monthlySpend); // Truncate to integer as per API spec
    }
    if (data.customAttributes !== undefined) payload.custom_attributes = data.customAttributes;

    return this.intercomClient.makeRequest('/companies', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateCompany(
    companyId: string,
    data: {
      name?: string;
      plan?: string;
      size?: number;
      website?: string;
      industry?: string;
      remoteCreatedAt?: number;
      monthlySpend?: number;
      customAttributes?: Record<string, any>;
    },
  ): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    const payload: any = {};

    if (data.name !== undefined) payload.name = data.name;
    if (data.plan !== undefined) payload.plan = data.plan;
    if (data.size !== undefined) payload.size = data.size;
    if (data.website !== undefined) {
      if (data.website && !validateUrl(data.website)) {
        throw new Error('Invalid website URL format provided');
      }
      payload.website = data.website;
    }
    if (data.industry !== undefined) payload.industry = data.industry;
    if (data.remoteCreatedAt !== undefined) payload.remote_created_at = data.remoteCreatedAt;
    if (data.monthlySpend !== undefined) {
      if (data.monthlySpend > 2147483647) {
        throw new Error('Monthly spend exceeds maximum allowed value (2147483647)');
      }
      payload.monthly_spend = Math.floor(data.monthlySpend);
    }
    if (data.customAttributes !== undefined) payload.custom_attributes = data.customAttributes;

    return this.intercomClient.makeRequest(`/companies/${companyId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteCompany(companyId: string): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    return this.intercomClient.makeRequest(`/companies/${companyId}`, {
      method: 'DELETE',
    });
  }

  async findCompany(externalCompanyId: string): Promise<any> {
    if (!externalCompanyId || typeof externalCompanyId !== 'string') {
      throw new Error('Valid external company ID must be provided');
    }

    const params = new URLSearchParams();
    params.append('company_id', externalCompanyId);

    return this.intercomClient.makeRequest(`/companies?${params.toString()}`, {
      method: 'GET',
    });
  }

  async listCompanyUsers(companyId: string): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    return this.intercomClient.makeRequest(`/companies/${companyId}/users`, {
      method: 'GET',
    });
  }

  async attachContactToCompany(companyId: string, contactId: string): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    const payload = {
      id: contactId,
    };

    return this.intercomClient.makeRequest(`/companies/${companyId}/contacts`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async detachContactFromCompany(companyId: string, contactId: string): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    return this.intercomClient.makeRequest(`/companies/${companyId}/contacts/${contactId}`, {
      method: 'DELETE',
    });
  }

  async listCompanySegments(companyId: string): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    return this.intercomClient.makeRequest(`/companies/${companyId}/segments`, {
      method: 'GET',
    });
  }

  async listCompanyTags(companyId: string): Promise<any> {
    if (!validateCompanyId(companyId)) {
      throw new Error('Invalid company ID provided');
    }

    return this.intercomClient.makeRequest(`/companies/${companyId}/tags`, {
      method: 'GET',
    });
  }

  async tagCompany(data: {
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

  async untagCompany(data: {
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
}
