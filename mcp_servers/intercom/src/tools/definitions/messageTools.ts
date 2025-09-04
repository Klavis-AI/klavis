import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * Create a message
 */
const CREATE_MESSAGE_TOOL: Tool = {
  name: 'intercom_create_message',
  description:
    'Create a message that has been initiated by an admin. The conversation can be an in-app message or an email.',
  inputSchema: {
    type: 'object',
    properties: {
      message_type: {
        type: 'string',
        description: 'The kind of message being created.',
        enum: ['in_app', 'email'],
        example: 'in_app',
      },
      subject: {
        type: 'string',
        description: 'The title of the email (required if message_type is email).',
        example: 'Thanks for everything',
      },
      body: {
        type: 'string',
        description: 'The content of the message. HTML and plaintext are supported.',
        example: 'Hello there',
      },
      template: {
        type: 'string',
        description: 'The style of the outgoing message. Possible values: plain or personal.',
        enum: ['plain', 'personal'],
        example: 'plain',
      },
      from: {
        type: 'object',
        description: 'The sender of the message. If not provided, the default sender will be used.',
        properties: {
          type: {
            type: 'string',
            description: 'Always admin.',
            enum: ['admin'],
            example: 'admin',
          },
          id: {
            type: 'integer',
            description: 'The identifier for the admin which is given by Intercom.',
            example: 394051,
          },
        },
        required: ['type', 'id'],
      },
      to: {
        type: 'object',
        description: 'The recipient of the message.',
        properties: {
          type: {
            type: 'string',
            description: 'The role associated to the contact - user or lead.',
            enum: ['user', 'lead'],
            example: 'user',
          },
          id: {
            type: 'string',
            description: 'The identifier for the contact which is given by Intercom.',
            example: '536e564f316c83104c000020',
          },
        },
        required: ['type', 'id'],
      },
      created_at: {
        type: 'integer',
        format: 'date-time',
        description:
          'The time the message was created. If not provided, the current time will be used.',
        example: 1590000000,
      },
      create_conversation_without_contact_reply: {
        type: 'boolean',
        description:
          'Whether a conversation should be opened in the inbox for the message without the contact replying. Defaults to false if not provided.',
        default: false,
        example: true,
      },
    },
    anyOf: [
      {
        title: 'Email message',
        required: ['message_type', 'subject', 'body', 'template', 'from', 'to'],
        properties: {
          message_type: { enum: ['email'] },
        },
      },
      {
        title: 'In-app message',
        required: ['message_type', 'body', 'from', 'to'],
        properties: {
          message_type: { enum: ['in_app'] },
        },
      },
    ],
  },
};

/**
 * List messages
 */
const LIST_MESSAGES_TOOL: Tool = {
  name: 'intercom_list_messages',
  description: 'List all messages sent from your workspace with pagination support.',
  inputSchema: {
    type: 'object',
    properties: {
      starting_after: {
        type: 'string',
        description: 'The cursor to use in pagination for retrieving the next page of results',
      },
      per_page: {
        type: 'integer',
        description: 'Number of results per page (default: 50, max: 150)',
        minimum: 1,
        maximum: 150,
        default: 50,
      },
    },
    required: [],
  },
};

/**
 * Get a message by ID
 */
const GET_MESSAGE_TOOL: Tool = {
  name: 'intercom_get_message',
  description: 'Retrieve a specific message by its ID.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the message which is given by Intercom',
        example: '2001',
      },
    },
    required: ['id'],
  },
};

/**
 * Create a note
 */
const CREATE_NOTE_TOOL: Tool = {
  name: 'intercom_create_note',
  description: 'Add a note to a specific contact.',
  inputSchema: {
    type: 'object',
    properties: {
      body: {
        type: 'string',
        description: 'The text of the note',
        example: 'Customer called about pricing questions',
      },
      contact_id: {
        type: 'string',
        description:
          'The unique identifier of the contact (lead or user) which is given by Intercom',
        example: '677c55ef6abd011ad17ff541',
      },
      admin_id: {
        type: 'string',
        description: 'The unique identifier of the admin creating the note',
        example: '991266214',
      },
    },
    required: ['body', 'contact_id', 'admin_id'],
  },
};

/**
 * List notes for a contact
 */
const LIST_NOTES_TOOL: Tool = {
  name: 'intercom_list_notes',
  description: 'List all notes attached to a specific contact.',
  inputSchema: {
    type: 'object',
    properties: {
      contact_id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '677c55ef6abd011ad17ff541',
      },
      starting_after: {
        type: 'string',
        description: 'The cursor to use in pagination for retrieving the next page of results',
      },
      per_page: {
        type: 'integer',
        description: 'Number of results per page (default: 50, max: 150)',
        minimum: 1,
        maximum: 150,
        default: 50,
      },
    },
    required: ['contact_id'],
  },
};

/**
 * Get a note by ID
 */
const GET_NOTE_TOOL: Tool = {
  name: 'intercom_get_note',
  description: 'Retrieve a specific note by its ID.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the note which is given by Intercom',
        example: '17495962',
      },
    },
    required: ['id'],
  },
};

/**
 * Send a user-initiated message
 */
const SEND_USER_MESSAGE_TOOL: Tool = {
  name: 'intercom_send_user_message',
  description:
    'Create a conversation that has been initiated by a contact (user or lead). The conversation can be an in-app message only.',
  inputSchema: {
    type: 'object',
    properties: {
      from: {
        type: 'object',
        description: 'The contact who initiated the conversation',
        properties: {
          type: {
            type: 'string',
            enum: ['lead', 'user', 'contact'],
            description: 'The role associated to the contact - user, lead, or contact',
            example: 'user',
          },
          id: {
            type: 'string',
            description: 'The identifier for the contact which is given by Intercom',
            format: 'uuid',
            minLength: 24,
            maxLength: 24,
            example: '536e564f316c83104c000020',
          },
        },
        required: ['type', 'id'],
      },
      body: {
        type: 'string',
        description: 'The content of the message. HTML is not supported',
        example: 'Hello, I need help with my order',
      },
      created_at: {
        type: 'integer',
        format: 'date-time',
        description:
          'The time the conversation was created as a UTC Unix timestamp. If not provided, the current time will be used',
        example: 1671028894,
      },
    },
    required: ['from', 'body'],
  },
};

export const MESSAGE_TOOLS = [
  CREATE_MESSAGE_TOOL,
  LIST_MESSAGES_TOOL,
  GET_MESSAGE_TOOL,
  CREATE_NOTE_TOOL,
  LIST_NOTES_TOOL,
  GET_NOTE_TOOL,
  SEND_USER_MESSAGE_TOOL,
] as const;
