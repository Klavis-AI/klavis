import { IntercomClient } from '../../client/intercomClient.js';
import {
  validateConversationId,
  validateContactId,
  validatePaginationParams,
  validateRequiredFields,
} from '../../utils/validation.js';

export class ConversationHandler {
  constructor(private intercomClient: IntercomClient) {}

  async listConversations(data: {
    startingAfter?: string;
    perPage?: number;
    displayAs?: 'plaintext';
  }): Promise<any> {
    const params = new URLSearchParams();

    if (data.startingAfter) {
      params.append('starting_after', data.startingAfter);
    }

    if (data.perPage) {
      params.append('per_page', data.perPage.toString());
    }

    if (data.displayAs) {
      params.append('display_as', data.displayAs);
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/conversations?${queryString}` : '/conversations';

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getConversation(conversationId: number, displayAs?: 'plaintext'): Promise<any> {
    if (!validateConversationId(conversationId.toString())) {
      throw new Error('Invalid conversation ID provided');
    }

    const params = new URLSearchParams();
    if (displayAs) {
      params.append('display_as', displayAs);
    }

    const queryString = params.toString();
    const endpoint = queryString
      ? `/conversations/${conversationId}?${queryString}`
      : `/conversations/${conversationId}`;

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async createConversation(data: {
    from: {
      type: 'lead' | 'user' | 'contact';
      id: string;
    };
    body: string;
    createdAt?: number;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['from', 'body']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!validateContactId(data.from.id)) {
      throw new Error('Invalid contact ID in from field');
    }

    const payload: any = {
      from: data.from,
      body: data.body,
    };

    if (data.createdAt !== undefined) {
      payload.created_at = data.createdAt;
    }

    return this.intercomClient.makeRequest('/conversations', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateConversation(
    conversationId: number,
    data: {
      displayAs?: 'plaintext';
      read?: boolean;
      title?: string;
      customAttributes?: Record<string, any>;
    },
  ): Promise<any> {
    if (!validateConversationId(conversationId.toString())) {
      throw new Error('Invalid conversation ID provided');
    }

    const payload: any = {};

    if (data.read !== undefined) payload.read = data.read;
    if (data.title !== undefined) payload.title = data.title;
    if (data.customAttributes !== undefined) payload.custom_attributes = data.customAttributes;

    const params = new URLSearchParams();
    if (data.displayAs) {
      params.append('display_as', data.displayAs);
    }

    const queryString = params.toString();
    const endpoint = queryString
      ? `/conversations/${conversationId}?${queryString}`
      : `/conversations/${conversationId}`;

    return this.intercomClient.makeRequest(endpoint, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteConversation(conversationId: number): Promise<any> {
    if (!validateConversationId(conversationId.toString())) {
      throw new Error('Invalid conversation ID provided');
    }

    return this.intercomClient.makeRequest(`/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  }

  async searchConversations(data: {
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

    return this.intercomClient.makeRequest('/conversations/search', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async replyToConversation(
    conversationId: string,
    data: {
      messageType?: 'comment' | 'note' | 'quick_reply';
      type?: 'admin' | 'user';
      adminId?: string;
      intercomUserId?: string;
      body?: string;
      attachmentUrls?: string[];
    },
  ): Promise<any> {
    if (!validateConversationId(conversationId)) {
      throw new Error('Invalid conversation ID provided');
    }

    const payload: any = {};

    if (data.messageType !== undefined) payload.message_type = data.messageType;
    if (data.type !== undefined) payload.type = data.type;
    if (data.adminId !== undefined) payload.admin_id = data.adminId;
    if (data.intercomUserId !== undefined) payload.intercom_user_id = data.intercomUserId;
    if (data.body !== undefined) payload.body = data.body;
    if (data.attachmentUrls !== undefined) payload.attachment_urls = data.attachmentUrls;

    return this.intercomClient.makeRequest(`/conversations/${conversationId}/reply`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async manageConversation(
    conversationId: number,
    data: {
      messageType: 'close' | 'snoozed' | 'open' | 'assignment';
      adminId: string;
      assigneeId?: string;
      type?: 'admin' | 'team';
      body?: string;
      snoozedUntil?: number;
    },
  ): Promise<any> {
    if (!validateConversationId(conversationId.toString())) {
      throw new Error('Invalid conversation ID provided');
    }

    const validation = validateRequiredFields(data, ['messageType', 'adminId']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload: any = {
      message_type: data.messageType,
      admin_id: data.adminId,
    };

    if (data.assigneeId !== undefined) payload.assignee_id = data.assigneeId;
    if (data.type !== undefined) payload.type = data.type;
    if (data.body !== undefined) payload.body = data.body;
    if (data.snoozedUntil !== undefined) payload.snoozed_until = data.snoozedUntil;

    return this.intercomClient.makeRequest(`/conversations/${conversationId}/reply`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async attachContactToConversation(
    conversationId: string,
    data: {
      adminId: string;
      customer: {
        intercomUserId: string;
      };
    },
  ): Promise<any> {
    if (!validateConversationId(conversationId)) {
      throw new Error('Invalid conversation ID provided');
    }

    const validation = validateRequiredFields(data, ['adminId', 'customer']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!validateContactId(data.customer.intercomUserId)) {
      throw new Error('Invalid intercom user ID provided');
    }

    const payload = {
      admin_id: data.adminId,
      customer: {
        intercom_user_id: data.customer.intercomUserId,
      },
    };

    return this.intercomClient.makeRequest(`/conversations/${conversationId}/customers`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async detachContactFromConversation(
    conversationId: string,
    contactId: string,
    data: {
      adminId: string;
      customer: {
        intercomUserId: string;
      };
    },
  ): Promise<any> {
    if (!validateConversationId(conversationId)) {
      throw new Error('Invalid conversation ID provided');
    }

    if (!validateContactId(contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    const validation = validateRequiredFields(data, ['adminId', 'customer']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload = {
      admin_id: data.adminId,
      customer: {
        intercom_user_id: data.customer.intercomUserId,
      },
    };

    return this.intercomClient.makeRequest(
      `/conversations/${conversationId}/customers/${contactId}`,
      {
        method: 'DELETE',
        body: JSON.stringify(payload),
      },
    );
  }

  async redactConversation(data: {
    type: 'conversation_part' | 'source';
    conversationId: string;
    conversationPartId?: string;
    sourceId?: string;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['type', 'conversationId']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!validateConversationId(data.conversationId)) {
      throw new Error('Invalid conversation ID provided');
    }

    // Validate conditional required fields
    if (data.type === 'conversation_part' && !data.conversationPartId) {
      throw new Error('conversation_part_id is required when type is conversation_part');
    }

    if (data.type === 'source' && !data.sourceId) {
      throw new Error('source_id is required when type is source');
    }

    const payload: any = {
      type: data.type,
      conversation_id: data.conversationId,
    };

    if (data.conversationPartId) payload.conversation_part_id = data.conversationPartId;
    if (data.sourceId) payload.source_id = data.sourceId;

    return this.intercomClient.makeRequest('/conversations/redact', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async convertConversationToTicket(
    conversationId: number,
    data: {
      ticketTypeId: string;
      attributes?: Record<string, any>;
    },
  ): Promise<any> {
    if (!validateConversationId(conversationId.toString())) {
      throw new Error('Invalid conversation ID provided');
    }

    const validation = validateRequiredFields(data, ['ticketTypeId']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload: any = {
      ticket_type_id: data.ticketTypeId,
    };

    if (data.attributes !== undefined) {
      payload.attributes = data.attributes;
    }

    return this.intercomClient.makeRequest(`/conversations/${conversationId}/convert`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}
