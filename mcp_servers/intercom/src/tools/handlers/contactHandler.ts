import { IntercomClient } from '../../client/intercomClient.js';
import {
  validateContactId,
  validateEmail,
  validateRequiredFields,
  validatePaginationParams,
} from '../../utils/validation.js';

export class ContactHandler {
  constructor(private intercomClient: IntercomClient) {}

  async listContacts(data: { startingAfter?: string; perPage?: number }): Promise<any> {
    const params = new URLSearchParams();

    if (data.startingAfter) {
      params.append('starting_after', data.startingAfter);
    }

    if (data.perPage) {
      params.append('per_page', data.perPage.toString());
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/contacts?${queryString}` : '/contacts';

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getContact(contactId: string): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    return this.intercomClient.makeRequest(`/contacts/${contactId}`, {
      method: 'GET',
    });
  }

  async createContact(data: {
    role?: 'user' | 'lead';
    externalId?: string;
    email?: string;
    phone?: string;
    name?: string;
    avatar?: string;
    signedUpAt?: number;
    lastSeenAt?: number;
    ownerId?: number;
    unsubscribedFromEmails?: boolean;
    customAttributes?: Record<string, any>;
  }): Promise<any> {
    const payload: any = {};

    // At least one of email, external_id, or role is required
    if (!data.email && !data.externalId && !data.role) {
      throw new Error('At least one of email, external_id, or role must be provided');
    }

    if (data.role !== undefined) payload.role = data.role;
    if (data.externalId !== undefined) payload.external_id = data.externalId;
    if (data.email !== undefined) {
      if (!validateEmail(data.email)) {
        throw new Error('Invalid email format provided');
      }
      payload.email = data.email;
    }
    if (data.phone !== undefined) payload.phone = data.phone;
    if (data.name !== undefined) payload.name = data.name;
    if (data.avatar !== undefined) payload.avatar = data.avatar;
    if (data.signedUpAt !== undefined) payload.signed_up_at = data.signedUpAt;
    if (data.lastSeenAt !== undefined) payload.last_seen_at = data.lastSeenAt;
    if (data.ownerId !== undefined) payload.owner_id = data.ownerId;
    if (data.unsubscribedFromEmails !== undefined)
      payload.unsubscribed_from_emails = data.unsubscribedFromEmails;
    if (data.customAttributes !== undefined) payload.custom_attributes = data.customAttributes;

    return this.intercomClient.makeRequest('/contacts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateContact(
    contactId: string,
    data: {
      role?: 'user' | 'lead';
      externalId?: string;
      email?: string;
      phone?: string;
      name?: string;
      avatar?: string;
      signedUpAt?: number;
      lastSeenAt?: number;
      ownerId?: number;
      unsubscribedFromEmails?: boolean;
      customAttributes?: Record<string, any>;
    },
  ): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    const payload: any = {};

    if (data.role !== undefined) payload.role = data.role;
    if (data.externalId !== undefined) payload.external_id = data.externalId;
    if (data.email !== undefined) {
      if (!validateEmail(data.email)) {
        throw new Error('Invalid email format provided');
      }
      payload.email = data.email;
    }
    if (data.phone !== undefined) payload.phone = data.phone;
    if (data.name !== undefined) payload.name = data.name;
    if (data.avatar !== undefined) payload.avatar = data.avatar;
    if (data.signedUpAt !== undefined) payload.signed_up_at = data.signedUpAt;
    if (data.lastSeenAt !== undefined) payload.last_seen_at = data.lastSeenAt;
    if (data.ownerId !== undefined) payload.owner_id = data.ownerId;
    if (data.unsubscribedFromEmails !== undefined)
      payload.unsubscribed_from_emails = data.unsubscribedFromEmails;
    if (data.customAttributes !== undefined) payload.custom_attributes = data.customAttributes;

    return this.intercomClient.makeRequest(`/contacts/${contactId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteContact(contactId: string): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    return this.intercomClient.makeRequest(`/contacts/${contactId}`, {
      method: 'DELETE',
    });
  }

  async searchContacts(data: {
    query: any;
    pagination?: {
      perPage?: number;
      startingAfter?: string;
    };
  }): Promise<any> {
    const payload: any = {
      query: data.query,
    };

    if (data.pagination) {
      const validation = validatePaginationParams(undefined, data.pagination.perPage);
      if (!validation.isValid) {
        throw new Error(`Invalid pagination: ${validation.errors.join(', ')}`);
      }

      payload.pagination = {};
      if (data.pagination.perPage) payload.pagination.per_page = data.pagination.perPage;
      if (data.pagination.startingAfter)
        payload.pagination.starting_after = data.pagination.startingAfter;
    }

    return this.intercomClient.makeRequest('/contacts/search', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async mergeContact(fromContactId: string, intoContactId: string): Promise<any> {
    if (!validateContactId(fromContactId)) {
      throw new Error('Invalid "from" contact ID provided');
    }
    if (!validateContactId(intoContactId)) {
      throw new Error('Invalid "into" contact ID provided');
    }

    const payload = {
      from: fromContactId,
      into: intoContactId,
    };

    return this.intercomClient.makeRequest('/contacts/merge', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listContactNotes(contactId: string): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    return this.intercomClient.makeRequest(`/contacts/${contactId}/notes`, {
      method: 'GET',
    });
  }

  async createContactNote(
    contactId: string,
    data: {
      body: string;
      adminId?: string;
    },
  ): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    const validation = validateRequiredFields(data, ['body']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload: any = {
      body: data.body,
      contact_id: contactId,
    };

    if (data.adminId) {
      payload.admin_id = data.adminId;
    }

    return this.intercomClient.makeRequest('/notes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listContactTags(contactId: string): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    return this.intercomClient.makeRequest(`/contacts/${contactId}/tags`, {
      method: 'GET',
    });
  }

  async addContactTag(contactId: string, tagId: string): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    return this.intercomClient.makeRequest(`/contacts/${contactId}/tags`, {
      method: 'POST',
      body: JSON.stringify({ id: tagId }),
    });
  }

  async removeContactTag(contactId: string, tagId: string): Promise<any> {
    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    return this.intercomClient.makeRequest(`/contacts/${contactId}/tags/${tagId}`, {
      method: 'DELETE',
    });
  }
}
