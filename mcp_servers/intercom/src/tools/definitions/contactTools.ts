import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * List all contacts in Intercom workspace
 */
const LIST_CONTACTS_TOOL: Tool = {
  name: 'intercom_list_contacts',
  description:
    'List all contacts (users or leads) in your Intercom workspace with pagination support.',
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
 * Get a specific contact by ID
 */
const GET_CONTACT_TOOL: Tool = {
  name: 'intercom_get_contact',
  description: 'Retrieve a specific contact by their Intercom ID.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
    },
    required: ['id'],
  },
};

/**
 * Create a new contact
 */
const CREATE_CONTACT_TOOL: Tool = {
  name: 'intercom_create_contact',
  description: 'Create a new contact in Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {
      role: {
        type: 'string',
        description: 'The role of the contact',
        enum: ['user', 'lead'],
      },
      external_id: {
        type: 'string',
        description: 'A unique identifier for the contact which is given to Intercom',
      },
      email: {
        type: 'string',
        format: 'email',
        description: 'The contacts email',
        example: 'jdoe@example.com',
      },
      phone: {
        type: 'string',
        description: 'The contacts phone number',
        example: '+353871234567',
        nullable: true,
      },
      name: {
        type: 'string',
        description: 'The contacts name',
        example: 'John Doe',
        nullable: true,
      },
      avatar: {
        type: 'string',
        format: 'uri',
        description: 'An image URL containing the avatar of a contact',
        example: 'https://www.example.com/avatar_image.jpg',
        nullable: true,
      },
      signed_up_at: {
        type: 'integer',
        format: 'date-time',
        description: 'The time specified for when a contact signed up (UNIX timestamp)',
        example: 1571672154,
        nullable: true,
      },
      last_seen_at: {
        type: 'integer',
        format: 'date-time',
        description: 'The time when the contact was last seen (UNIX timestamp)',
        example: 1571672154,
        nullable: true,
      },
      owner_id: {
        type: 'integer',
        description: 'The id of an admin that has been assigned account ownership of the contact',
        example: 123,
        nullable: true,
      },
      unsubscribed_from_emails: {
        type: 'boolean',
        description: 'Whether the contact is unsubscribed from emails',
        example: true,
        nullable: true,
      },
      custom_attributes: {
        type: 'object',
        description: 'The custom attributes which are set for the contact',
        nullable: true,
        additionalProperties: true,
      },
    },
    anyOf: [
      {
        required: ['email'],
        title: 'Create contact with email',
      },
      {
        required: ['external_id'],
        title: 'Create contact with external_id',
      },
      {
        required: ['role'],
        title: 'Create contact with role',
      },
    ],
  },
};

/**
 * Update an existing contact
 */
const UPDATE_CONTACT_TOOL: Tool = {
  name: 'intercom_update_contact',
  description: 'Update an existing contact in Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
      role: {
        type: 'string',
        description: 'The role of the contact',
        enum: ['user', 'lead'],
      },
      external_id: {
        type: 'string',
        description: 'A unique identifier for the contact which is given to Intercom',
      },
      email: {
        type: 'string',
        format: 'email',
        description: 'The contacts email',
        example: 'jdoe@example.com',
      },
      phone: {
        type: 'string',
        description: 'The contacts phone number',
        example: '+353871234567',
        nullable: true,
      },
      name: {
        type: 'string',
        description: 'The contacts name',
        example: 'John Doe',
        nullable: true,
      },
      avatar: {
        type: 'string',
        format: 'uri',
        description: 'An image URL containing the avatar of a contact',
        example: 'https://www.example.com/avatar_image.jpg',
        nullable: true,
      },
      signed_up_at: {
        type: 'integer',
        format: 'date-time',
        description: 'The time specified for when a contact signed up (UNIX timestamp)',
        example: 1571672154,
        nullable: true,
      },
      last_seen_at: {
        type: 'integer',
        format: 'date-time',
        description: 'The time when the contact was last seen (UNIX timestamp)',
        example: 1571672154,
        nullable: true,
      },
      owner_id: {
        type: 'integer',
        description: 'The id of an admin that has been assigned account ownership of the contact',
        example: 123,
        nullable: true,
      },
      unsubscribed_from_emails: {
        type: 'boolean',
        description: 'Whether the contact is unsubscribed from emails',
        example: true,
        nullable: true,
      },
      custom_attributes: {
        type: 'object',
        description: 'The custom attributes which are set for the contact',
        nullable: true,
        additionalProperties: true,
      },
    },
    required: ['id'],
  },
};

/**
 * Search contacts with query filters
 */
const SEARCH_CONTACTS_TOOL: Tool = {
  name: 'intercom_search_contacts',
  description:
    'Search contacts using query filters and operators with advanced search capabilities.',
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
                example: 'email',
              },
              operator: {
                type: 'string',
                enum: ['=', '!=', 'IN', 'NIN', '<', '>', '~', '!~', '^', '$'],
                description: 'The operator to use for the search',
                example: '=',
              },
              value: {
                oneOf: [
                  { type: 'string' },
                  { type: 'integer' },
                  { type: 'array', items: { oneOf: [{ type: 'string' }, { type: 'integer' }] } },
                ],
                description: 'The value to search for',
                example: 'user@example.com',
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
            description: 'Number of results per page (default: 50, max: 150)',
            minimum: 1,
            maximum: 150,
            default: 50,
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
 * Delete a contact
 */
const DELETE_CONTACT_TOOL: Tool = {
  name: 'intercom_delete_contact',
  description: 'Delete a single contact from Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
    },
    required: ['id'],
  },
};

/**
 * Merge a lead and a user
 */
const MERGE_CONTACT_TOOL: Tool = {
  name: 'intercom_merge_contact',
  description: 'Merge a contact with a role of lead into a contact with a role of user.',
  inputSchema: {
    type: 'object',
    properties: {
      from: {
        type: 'string',
        description: 'The unique identifier for the contact to merge away from (must be a lead)',
        example: '5d70dd30de4efd54f42fd526',
      },
      into: {
        type: 'string',
        description: 'The unique identifier for the contact to merge into (must be a user)',
        example: '5ba682d23d7cf92bef87bfd4',
      },
    },
    required: ['from', 'into'],
  },
};

/**
 * List notes for a contact
 */
const LIST_CONTACT_NOTES_TOOL: Tool = {
  name: 'intercom_list_contact_notes',
  description: 'List all notes attached to a specific contact.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
    },
    required: ['id'],
  },
};

/**
 * Create a note for a contact
 */
const CREATE_CONTACT_NOTE_TOOL: Tool = {
  name: 'intercom_create_contact_note',
  description: 'Add a note to a specific contact.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
      body: {
        type: 'string',
        description: 'The text of the note',
        example: 'New note content',
      },
      contact_id: {
        type: 'string',
        description: 'The unique identifier of the contact (alternative to id in path)',
        example: '123',
      },
      admin_id: {
        type: 'string',
        description: 'The unique identifier of the admin creating the note',
        example: '123',
      },
    },
    required: ['id', 'body'],
  },
};

/**
 * List tags attached to a contact
 */
const LIST_CONTACT_TAGS_TOOL: Tool = {
  name: 'intercom_list_contact_tags',
  description: 'List all tags attached to a specific contact.',
  inputSchema: {
    type: 'object',
    properties: {
      contact_id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
    },
    required: ['contact_id'],
  },
};

/**
 * Add tag to a contact
 */
const ADD_CONTACT_TAG_TOOL: Tool = {
  name: 'intercom_add_contact_tag',
  description: 'Add a tag to a specific contact.',
  inputSchema: {
    type: 'object',
    properties: {
      contact_id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
      id: {
        type: 'string',
        description: 'The unique identifier for the tag which is given by Intercom',
        example: '7522907',
      },
    },
    required: ['contact_id', 'id'],
  },
};

/**
 * Remove tag from a contact
 */
const REMOVE_CONTACT_TAG_TOOL: Tool = {
  name: 'intercom_remove_contact_tag',
  description: 'Remove a tag from a specific contact.',
  inputSchema: {
    type: 'object',
    properties: {
      contact_id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
      id: {
        type: 'string',
        description: 'The unique identifier for the tag which is given by Intercom',
        example: '7522907',
      },
    },
    required: ['contact_id', 'id'],
  },
};

export const CONTACT_TOOLS = [
  LIST_CONTACTS_TOOL,
  GET_CONTACT_TOOL,
  CREATE_CONTACT_TOOL,
  UPDATE_CONTACT_TOOL,
  SEARCH_CONTACTS_TOOL,
  DELETE_CONTACT_TOOL,
  MERGE_CONTACT_TOOL,
  LIST_CONTACT_NOTES_TOOL,
  CREATE_CONTACT_NOTE_TOOL,
  LIST_CONTACT_TAGS_TOOL,
  ADD_CONTACT_TAG_TOOL,
  REMOVE_CONTACT_TAG_TOOL,
] as const;
