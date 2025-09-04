import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * List all companies
 */
const LIST_COMPANIES_TOOL: Tool = {
  name: 'intercom_list_companies',
  description: 'List all companies in your Intercom workspace with pagination support.',
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
      order: {
        type: 'string',
        description: 'The order of the results',
        enum: ['asc', 'desc'],
        default: 'desc',
      },
    },
    required: [],
  },
};

/**
 * Get a specific company by ID
 */
const GET_COMPANY_TOOL: Tool = {
  name: 'intercom_get_company',
  description: 'Retrieve a specific company by their Intercom ID.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
    },
    required: ['id'],
  },
};

/**
 * Create a new company
 */
const CREATE_COMPANY_TOOL: Tool = {
  name: 'intercom_create_company',
  description: 'Create a new company in Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: 'The name of the Company',
        example: 'Intercom',
      },
      company_id: {
        type: 'string',
        description: "The company id you have defined for the company. Can't be updated",
        example: '625e90fc55ab113b6d92175f',
      },
      plan: {
        type: 'string',
        description: 'The name of the plan you have associated with the company',
        example: 'Enterprise',
      },
      size: {
        type: 'integer',
        description: 'The number of employees in this company',
        example: 100,
      },
      website: {
        type: 'string',
        description:
          "The URL for this company's website. Please note that the value specified here is not validated. Accepts any string",
        example: 'https://www.example.com',
      },
      industry: {
        type: 'string',
        description: 'The industry that this company operates in',
        example: 'Manufacturing',
      },
      remote_created_at: {
        type: 'integer',
        format: 'date-time',
        description: 'The time the company was created by you',
        example: 1394531169,
      },
      monthly_spend: {
        type: 'integer',
        description:
          'How much revenue the company generates for your business. Note that this will truncate floats. i.e. it only allow for whole integers, 155.98 will be truncated to 155. Note that this has an upper limit of 2**31-1 or 2147483647',
        example: 1000,
      },
      custom_attributes: {
        type: 'object',
        description:
          'A hash of key/value pairs containing any other data about the company you want Intercom to store',
        additionalProperties: true,
        example: {
          paid_subscriber: true,
          monthly_spend: 155.5,
          team_mates: 9,
        },
      },
    },
    anyOf: [
      {
        required: ['name'],
        title: 'Create company with name',
      },
      {
        required: ['company_id'],
        title: 'Create company with company_id',
      },
    ],
  },
};

/**
 * Update an existing company
 */
const UPDATE_COMPANY_TOOL: Tool = {
  name: 'intercom_update_company',
  description: 'Update an existing company in Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
      name: {
        type: 'string',
        description: 'The name of the Company',
        example: 'Intercom',
      },
      plan: {
        type: 'string',
        description: 'The name of the plan you have associated with the company',
        example: 'Enterprise',
      },
      size: {
        type: 'integer',
        description: 'The number of employees in this company',
        example: 100,
      },
      website: {
        type: 'string',
        description:
          "The URL for this company's website. Please note that the value specified here is not validated. Accepts any string",
        example: 'https://www.example.com',
      },
      industry: {
        type: 'string',
        description: 'The industry that this company operates in',
        example: 'Manufacturing',
      },
      remote_created_at: {
        type: 'integer',
        format: 'date-time',
        description: 'The time the company was created by you',
        example: 1394531169,
      },
      monthly_spend: {
        type: 'integer',
        description:
          'How much revenue the company generates for your business. Note that this will truncate floats. i.e. it only allow for whole integers, 155.98 will be truncated to 155. Note that this has an upper limit of 2**31-1 or 2147483647',
        example: 1000,
      },
      custom_attributes: {
        type: 'object',
        description:
          'A hash of key/value pairs containing any other data about the company you want Intercom to store',
        additionalProperties: true,
        example: {
          paid_subscriber: true,
          monthly_spend: 155.5,
          team_mates: 9,
        },
      },
    },
    required: ['id'],
  },
};

/**
 * Delete a company
 */
const DELETE_COMPANY_TOOL: Tool = {
  name: 'intercom_delete_company',
  description: 'Delete a single company from Intercom workspace.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
    },
    required: ['id'],
  },
};

/**
 * Find company by company_id
 */
const FIND_COMPANY_TOOL: Tool = {
  name: 'intercom_find_company',
  description: 'Find a company using your own company_id (external identifier).',
  inputSchema: {
    type: 'object',
    properties: {
      company_id: {
        type: 'string',
        description: 'The company_id you have defined for the company',
        example: '625e90fc55ab113b6d92175f',
      },
    },
    required: ['company_id'],
  },
};

/**
 * List company users
 */
const LIST_COMPANY_USERS_TOOL: Tool = {
  name: 'intercom_list_company_users',
  description: 'List all users that belong to a specific company.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
    },
    required: ['id'],
  },
};

/**
 * Attach a contact to a company
 */
const ATTACH_CONTACT_TO_COMPANY_TOOL: Tool = {
  name: 'intercom_attach_contact_to_company',
  description: 'Attach a contact to a company.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
      contact_id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
    },
    required: ['id', 'contact_id'],
  },
};

/**
 * Detach a contact from a company
 */
const DETACH_CONTACT_FROM_COMPANY_TOOL: Tool = {
  name: 'intercom_detach_contact_from_company',
  description: 'Detach a contact from a company.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
      contact_id: {
        type: 'string',
        description: 'The unique identifier for the contact which is given by Intercom',
        example: '63a07ddf05a32042dffac965',
      },
    },
    required: ['id', 'contact_id'],
  },
};

/**
 * List company segments
 */
const LIST_COMPANY_SEGMENTS_TOOL: Tool = {
  name: 'intercom_list_company_segments',
  description: 'List all segments that a specific company belongs to.',
  inputSchema: {
    type: 'object',
    properties: {
      company_id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
    },
    required: ['company_id'],
  },
};

/**
 * List company tags
 */
const LIST_COMPANY_TAGS_TOOL: Tool = {
  name: 'intercom_list_company_tags',
  description: 'List all tags attached to a specific company.',
  inputSchema: {
    type: 'object',
    properties: {
      company_id: {
        type: 'string',
        description: 'The unique identifier for the company which is given by Intercom',
        example: '531ee472cce572a6ec000006',
      },
    },
    required: ['company_id'],
  },
};

/**
 * Tag a company
 */
const TAG_COMPANY_TOOL: Tool = {
  name: 'intercom_tag_company',
  description: 'Add a tag to a specific company.',
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
 * Untag a company
 */
const UNTAG_COMPANY_TOOL: Tool = {
  name: 'intercom_untag_company',
  description: 'Remove a tag from a specific company.',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description: 'The name of the tag which will be untagged from the company',
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
        description: 'Always set to true',
        enum: [true],
        default: true,
      },
    },
    required: ['name', 'companies', 'untag'],
  },
};

export const COMPANY_TOOLS = [
  LIST_COMPANIES_TOOL,
  GET_COMPANY_TOOL,
  CREATE_COMPANY_TOOL,
  UPDATE_COMPANY_TOOL,
  DELETE_COMPANY_TOOL,
  FIND_COMPANY_TOOL,
  LIST_COMPANY_USERS_TOOL,
  ATTACH_CONTACT_TO_COMPANY_TOOL,
  DETACH_CONTACT_FROM_COMPANY_TOOL,
  LIST_COMPANY_SEGMENTS_TOOL,
  LIST_COMPANY_TAGS_TOOL,
  TAG_COMPANY_TOOL,
  UNTAG_COMPANY_TOOL,
] as const;
