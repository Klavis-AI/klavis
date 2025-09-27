import { IntercomClient } from '../../client/intercomClient.js';
import {
  validateMessageId,
  validateContactId,
  validateRequiredFields,
} from '../../utils/validation.js';

export class MessageHandler {
  constructor(private intercomClient: IntercomClient) {}

  async createMessage(data: {
    messageType: 'in_app' | 'email';
    subject?: string;
    body: string;
    template?: 'plain' | 'personal';
    from: {
      type: 'admin';
      id: number;
    };
    to: {
      type: 'user' | 'lead';
      id: string;
    };
    createdAt?: number;
    createConversationWithoutContactReply?: boolean;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['messageType', 'body', 'from', 'to']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    // Email messages require subject
    if (data.messageType === 'email' && !data.subject) {
      throw new Error('Subject is required for email messages');
    }

    // Email messages require template
    if (data.messageType === 'email' && !data.template) {
      throw new Error('Template is required for email messages');
    }

    if (!validateContactId(data.to.id)) {
      throw new Error('Invalid contact ID in "to" field');
    }

    const payload: any = {
      message_type: data.messageType,
      body: data.body,
      from: data.from,
      to: data.to,
    };

    if (data.subject !== undefined) payload.subject = data.subject;
    if (data.template !== undefined) payload.template = data.template;
    if (data.createdAt !== undefined) payload.created_at = data.createdAt;
    if (data.createConversationWithoutContactReply !== undefined) {
      payload.create_conversation_without_contact_reply =
        data.createConversationWithoutContactReply;
    }

    return this.intercomClient.makeRequest('/messages', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listMessages(data: { startingAfter?: string; perPage?: number }): Promise<any> {
    const params = new URLSearchParams();

    if (data.startingAfter) {
      params.append('starting_after', data.startingAfter);
    }

    if (data.perPage) {
      params.append('per_page', data.perPage.toString());
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/messages?${queryString}` : '/messages';

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getMessage(messageId: string): Promise<any> {
    if (!validateMessageId(messageId)) {
      throw new Error('Invalid message ID provided');
    }

    return this.intercomClient.makeRequest(`/messages/${messageId}`, {
      method: 'GET',
    });
  }

  async createNote(data: { body: string; contactId: string; adminId: string }): Promise<any> {
    const validation = validateRequiredFields(data, ['body', 'contactId', 'adminId']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!validateContactId(data.contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    const payload = {
      body: data.body,
      contact_id: data.contactId,
      admin_id: data.adminId,
    };

    return this.intercomClient.makeRequest('/notes', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listNotes(data: {
    contactId: string;
    startingAfter?: string;
    perPage?: number;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['contactId']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    if (!validateContactId(data.contactId)) {
      throw new Error('Invalid contact ID provided');
    }

    const params = new URLSearchParams();
    params.append('contact_id', data.contactId);

    if (data.startingAfter) {
      params.append('starting_after', data.startingAfter);
    }

    if (data.perPage) {
      params.append('per_page', data.perPage.toString());
    }

    return this.intercomClient.makeRequest(`/notes?${params.toString()}`, {
      method: 'GET',
    });
  }

  async getNote(noteId: string): Promise<any> {
    if (!noteId || typeof noteId !== 'string') {
      throw new Error('Invalid note ID provided');
    }

    return this.intercomClient.makeRequest(`/notes/${noteId}`, {
      method: 'GET',
    });
  }

  async sendUserMessage(data: {
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
      throw new Error('Invalid contact ID in "from" field');
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
}
