import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * List all tags
 */
const LIST_TAGS_TOOL: Tool = {
  name: 'intercom_list_tags',
  description: 'List all tags in your Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {},
    required: [],
  },
};

/**
 * Find a specific tag
 */
const GET_TAG_TOOL: Tool = {
  name: 'intercom_get_tag',
  description: 'Retrieve a specific tag by its ID.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier of a given tag',
        example: '123',
      },
    },
    required: ['id'],
  },
};

/**
 * Create or update a tag
 */
const CREATE_OR_UPDATE_TAG_TOOL: Tool = {
  name: 'intercom_create_or_update_tag',
  description: 'Create a new tag or update an existing tag by name or ID.',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description:
          'The name of the tag, which will be created if not found, or the new name for the tag if this is an update request. Names are case insensitive.',
        example: 'Independent',
      },
      id: {
        type: 'string',
        description: 'The id of tag to update (optional, only for updates)',
        example: '656452352',
      },
    },
    required: ['name'],
  },
};

/**
 * Tag companies
 */
const TAG_COMPANIES_TOOL: Tool = {
  name: 'intercom_tag_companies',
  description:
    "Tag a single company or a list of companies. If the tag doesn't exist, a new one will be created automatically.",
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: 'The name of the tag, which will be created if not found',
        example: 'Enterprise',
      },
      companies: {
        type: 'array',
        description: 'Array of companies to tag',
        items: {
          type: 'object',
          properties: {
            id: {
              type: 'string',
              description: 'The Intercom defined id representing the company',
              example: '531ee472cce572a6ec000006',
            },
            company_id: {
              type: 'string',
              description: 'The company id you have defined for the company',
              example: '6',
            },
          },
          oneOf: [{ required: ['id'] }, { required: ['company_id'] }],
        },
      },
    },
    required: ['name', 'companies'],
  },
};

/**
 * Untag companies
 */
const UNTAG_COMPANIES_TOOL: Tool = {
  name: 'intercom_untag_companies',
  description: 'Remove a tag from a single company or a list of companies.',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: 'The name of the tag which will be removed from the companies',
        example: 'Enterprise',
      },
      companies: {
        type: 'array',
        description: 'Array of companies to untag',
        items: {
          type: 'object',
          properties: {
            id: {
              type: 'string',
              description: 'The Intercom defined id representing the company',
              example: '531ee472cce572a6ec000006',
            },
            company_id: {
              type: 'string',
              description: 'The company id you have defined for the company',
              example: '6',
            },
          },
          oneOf: [{ required: ['id'] }, { required: ['company_id'] }],
        },
      },
      untag: {
        type: 'boolean',
        description: 'Always set to true for untag operations',
        enum: [true],
        default: true,
      },
    },
    required: ['name', 'companies', 'untag'],
  },
};

/**
 * Tag multiple users
 */
const TAG_USERS_TOOL: Tool = {
  name: 'intercom_tag_users',
  description:
    "Tag a list of users/contacts. If the tag doesn't exist, a new one will be created automatically.",
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: 'The name of the tag, which will be created if not found',
        example: 'VIP Customer',
      },
      users: {
        type: 'array',
        description: 'Array of users to tag',
        items: {
          type: 'object',
          properties: {
            id: {
              type: 'string',
              description: 'The Intercom defined id representing the user',
              example: '5f7f0d217289f8d2f4262080',
            },
          },
          required: ['id'],
        },
      },
    },
    required: ['name', 'users'],
  },
};

/**
 * Delete a tag
 */
const DELETE_TAG_TOOL: Tool = {
  name: 'intercom_delete_tag',
  description:
    'Delete a tag from your workspace. Note: tags with dependent objects (like segments) cannot be deleted.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier of a given tag',
        example: '123',
      },
    },
    required: ['id'],
  },
};

export const TAG_TOOLS = [
  LIST_TAGS_TOOL,
  GET_TAG_TOOL,
  CREATE_OR_UPDATE_TAG_TOOL,
  TAG_COMPANIES_TOOL,
  UNTAG_COMPANIES_TOOL,
  TAG_USERS_TOOL,
  DELETE_TAG_TOOL,
] as const;
