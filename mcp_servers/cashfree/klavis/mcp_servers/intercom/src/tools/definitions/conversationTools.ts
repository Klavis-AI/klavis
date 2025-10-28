import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * List all conversations
 */
const LIST_CONVERSATIONS_TOOL: Tool = {
  name: 'intercom_list_conversations',
  description: 'List all conversations in your Intercom workspace with pagination support.',
  inputSchema: {
    type: 'object',
    properties: {
      starting_after: {
        type: 'string',
        description: 'The cursor to use in pagination for retrieving the next page of results',
      },
      per_page: {
        type: 'integer',
        description: 'Number of results per page (default: 20, max: 150)',
        minimum: 1,
        maximum: 150,
        default: 20,
      },
      display_as: {
        type: 'string',
        description: 'Set to plaintext to retrieve conversation messages in plain text',
        enum: ['plaintext'],
      },
    },
    required: [],
  },
};

/**
 * Get a specific conversation by ID
 */
const GET_CONVERSATION_TOOL: Tool = {
  name: 'intercom_get_conversation',
  description: 'Retrieve a specific conversation by its ID with all conversation parts.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The id of the conversation to target',
        example: 123,
      },
      display_as: {
        type: 'string',
        description: 'Set to plaintext to retrieve conversation messages in plain text',
        enum: ['plaintext'],
      },
    },
    required: ['id'],
  },
};

/**
 * Create a new conversation
 */
const CREATE_CONVERSATION_TOOL: Tool = {
  name: 'intercom_create_conversation',
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
        example: 'Hello',
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

/**
 * Update a conversation
 */
const UPDATE_CONVERSATION_TOOL: Tool = {
  name: 'intercom_update_conversation',
  description: 'Update an existing conversation including custom attributes and read status.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The id of the conversation to target',
        example: 123,
      },
      display_as: {
        type: 'string',
        description: 'Set to plaintext to retrieve conversation messages in plain text',
        enum: ['plaintext'],
      },
      read: {
        type: 'boolean',
        description: 'Mark a conversation as read within Intercom',
        example: true,
      },
      title: {
        type: 'string',
        description: 'The title given to the conversation',
        example: 'Conversation Title',
      },
      custom_attributes: {
        type: 'object',
        description: 'The custom attributes which are set for the conversation',
        additionalProperties: true,
      },
    },
    required: ['id'],
  },
};

/**
 * Delete a conversation
 */
const DELETE_CONVERSATION_TOOL: Tool = {
  name: 'intercom_delete_conversation',
  description: 'Delete a single conversation from Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The id of the conversation to delete',
      },
    },
    required: ['id'],
  },
};

/**
 * Search conversations
 */
const SEARCH_CONVERSATIONS_TOOL: Tool = {
  name: 'intercom_search_conversations',
  description:
    'Search conversations using query filters and operators with advanced search capabilities.',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'object',
        description: 'Search query with filters',
        anyOf: [
          {
            title: 'Single filter search',
            type: 'object',
            properties: {
              field: {
                type: 'string',
                description: 'The field to search on',
                example: 'created_at',
              },
              operator: {
                type: 'string',
                enum: ['=', '!=', 'IN', 'NIN', '<', '>', '~', '!~', '^', '$'],
                description: 'The operator to use for the search',
                example: '>',
              },
              value: {
                oneOf: [
                  { type: 'string' },
                  { type: 'integer' },
                  { type: 'array', items: { oneOf: [{ type: 'string' }, { type: 'integer' }] } },
                ],
                description: 'The value to search for',
                example: '1306054154',
              },
            },
            required: ['field', 'operator', 'value'],
          },
          {
            title: 'Multiple filter search',
            type: 'object',
            properties: {
              operator: {
                type: 'string',
                enum: ['AND', 'OR'],
                description: 'Boolean operator to combine multiple filters',
                example: 'AND',
              },
              value: {
                type: 'array',
                description: 'Array of filter objects',
                items: {
                  type: 'object',
                  properties: {
                    field: { type: 'string' },
                    operator: {
                      type: 'string',
                      enum: ['=', '!=', 'IN', 'NIN', '<', '>', '~', '!~', '^', '$'],
                    },
                    value: {
                      oneOf: [
                        { type: 'string' },
                        { type: 'integer' },
                        {
                          type: 'array',
                          items: { oneOf: [{ type: 'string' }, { type: 'integer' }] },
                        },
                      ],
                    },
                  },
                  required: ['field', 'operator', 'value'],
                },
              },
            },
            required: ['operator', 'value'],
          },
        ],
      },
      pagination: {
        type: 'object',
        description: 'Pagination options',
        properties: {
          per_page: {
            type: 'integer',
            description: 'Number of results per page (default: 20, max: 150)',
            minimum: 1,
            maximum: 150,
            default: 20,
          },
          starting_after: {
            type: 'string',
            description: 'Cursor for pagination',
            nullable: true,
          },
        },
      },
    },
    required: ['query'],
  },
};

/**
 * Reply to a conversation
 */
const REPLY_CONVERSATION_TOOL: Tool = {
  name: 'intercom_reply_conversation',
  description:
    'Reply to a conversation with a message from an admin or on behalf of a contact, or with a note for admins.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description:
          'The Intercom provisioned identifier for the conversation or the string "last" to reply to the last part of the conversation',
        example: '123',
      },
      message_type: {
        type: 'string',
        description: 'The type of message being sent',
        enum: ['comment', 'note', 'quick_reply'],
      },
      type: {
        type: 'string',
        description: 'The type of reply - admin or user',
        enum: ['admin', 'user'],
      },
      admin_id: {
        type: 'string',
        description: 'The id of the admin who is replying to the conversation',
        example: '991266214',
      },
      intercom_user_id: {
        type: 'string',
        description: 'The Intercom user id for user replies',
      },
      body: {
        type: 'string',
        description: 'The content of the reply',
        example: 'Thanks for reaching out!',
      },
      attachment_urls: {
        type: 'array',
        description: 'A list of image URLs that will be added as attachments',
        items: {
          type: 'string',
          format: 'uri',
        },
      },
    },
    required: ['id'],
  },
};

/**
 * Manage a conversation (close, snooze, open, assign)
 */
const MANAGE_CONVERSATION_TOOL: Tool = {
  name: 'intercom_manage_conversation',
  description: 'Perform management actions on a conversation: close, snooze, open, or assign.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The id of the conversation to target',
        example: 123,
      },
      message_type: {
        type: 'string',
        description: 'The type of management action to perform',
        enum: ['close', 'snoozed', 'open', 'assignment'],
      },
      admin_id: {
        type: 'string',
        description: 'The id of the admin who is performing the action',
        example: '5017690',
      },
      assignee_id: {
        type: 'string',
        description:
          'The id of the admin or team to assign the conversation to (for assignment type)',
        example: '991266214',
      },
      type: {
        type: 'string',
        description: 'Type of assignee - admin or team',
        enum: ['admin', 'team'],
      },
      body: {
        type: 'string',
        description: 'Message body for close action',
        example: 'Goodbye :)',
      },
      snoozed_until: {
        type: 'integer',
        format: 'timestamp',
        description: 'The time you want the conversation to reopen (for snooze action)',
        example: 1673609604,
      },
    },
    required: ['id', 'message_type', 'admin_id'],
  },
};

/**
 * Attach a contact to a conversation
 */
const ATTACH_CONTACT_TO_CONVERSATION_TOOL: Tool = {
  name: 'intercom_attach_contact_to_conversation',
  description:
    'Add participants who are contacts to a conversation, on behalf of either another contact or an admin.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The identifier for the conversation as given by Intercom',
        example: '123',
      },
      admin_id: {
        type: 'string',
        description: 'The id of the admin performing the action',
        example: '991266214',
      },
      customer: {
        type: 'object',
        description: 'The contact to add to the conversation',
        properties: {
          intercom_user_id: {
            type: 'string',
            description: 'The Intercom user id of the contact to add',
            example: '677c55ef6abd011ad17ff541',
          },
        },
        required: ['intercom_user_id'],
      },
    },
    required: ['id', 'admin_id', 'customer'],
  },
};

/**
 * Detach a contact from a conversation
 */
const DETACH_CONTACT_FROM_CONVERSATION_TOOL: Tool = {
  name: 'intercom_detach_contact_from_conversation',
  description: 'Remove a contact from a group conversation.',
  inputSchema: {
    type: 'object',
    properties: {
      conversation_id: {
        type: 'string',
        description: 'The identifier for the conversation as given by Intercom',
        example: '123',
      },
      contact_id: {
        type: 'string',
        description: 'The identifier for the contact as given by Intercom',
        example: '123',
      },
      admin_id: {
        type: 'string',
        description: 'The id of the admin performing the action',
        example: '991266214',
      },
      customer: {
        type: 'object',
        description: 'The contact to remove from the conversation',
        properties: {
          intercom_user_id: {
            type: 'string',
            description: 'The Intercom user id of the contact to remove',
            example: '677c55ef6abd011ad17ff541',
          },
        },
        required: ['intercom_user_id'],
      },
    },
    required: ['conversation_id', 'contact_id', 'admin_id', 'customer'],
  },
};

/**
 * Redact a conversation part
 */
const REDACT_CONVERSATION_TOOL: Tool = {
  name: 'intercom_redact_conversation',
  description: 'Redact a conversation part or the source message of a conversation.',
  inputSchema: {
    type: 'object',
    properties: {
      type: {
        type: 'string',
        description: 'The type of resource being redacted',
        enum: ['conversation_part', 'source'],
        example: 'conversation_part',
      },
      conversation_id: {
        type: 'string',
        description: 'The id of the conversation',
        example: '19894788788',
      },
      conversation_part_id: {
        type: 'string',
        description: 'The id of the conversation_part (required when type is conversation_part)',
        example: '19381789428',
      },
      source_id: {
        type: 'string',
        description: 'The id of the source (required when type is source)',
        example: '19894781231',
      },
    },
    required: ['type', 'conversation_id'],
  },
};

/**
 * Convert a conversation to a ticket
 */
const CONVERT_CONVERSATION_TO_TICKET_TOOL: Tool = {
  name: 'intercom_convert_conversation_to_ticket',
  description: 'Convert a conversation to a ticket.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The id of the conversation to target',
        example: 123,
      },
      ticket_type_id: {
        type: 'string',
        description: 'The ID of the type of ticket you want to convert the conversation to',
        example: '1234',
      },
      attributes: {
        type: 'object',
        description: 'The attributes set on the ticket',
        additionalProperties: true,
      },
    },
    required: ['id', 'ticket_type_id'],
  },
};

export const CONVERSATION_TOOLS = [
  LIST_CONVERSATIONS_TOOL,
  GET_CONVERSATION_TOOL,
  CREATE_CONVERSATION_TOOL,
  UPDATE_CONVERSATION_TOOL,
  DELETE_CONVERSATION_TOOL,
  SEARCH_CONVERSATIONS_TOOL,
  REPLY_CONVERSATION_TOOL,
  MANAGE_CONVERSATION_TOOL,
  ATTACH_CONTACT_TO_CONVERSATION_TOOL,
  DETACH_CONTACT_FROM_CONVERSATION_TOOL,
  REDACT_CONVERSATION_TOOL,
  CONVERT_CONVERSATION_TO_TICKET_TOOL,
] as const;
