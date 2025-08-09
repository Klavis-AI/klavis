import { Tool } from '@modelcontextprotocol/sdk/types.js';

/**
 * List all articles
 */
const LIST_ARTICLES_TOOL: Tool = {
  name: 'intercom_list_articles',
  description: 'List all articles in your Help Center with pagination support.',
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
 * Get a specific article by ID
 */
const GET_ARTICLE_TOOL: Tool = {
  name: 'intercom_get_article',
  description: 'Retrieve a specific article by its ID.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The unique identifier for the article which is given by Intercom',
        example: 123,
      },
    },
    required: ['id'],
  },
};

/**
 * Create a new article
 */
const CREATE_ARTICLE_TOOL: Tool = {
  name: 'intercom_create_article',
  description: 'Create a new article in your Help Center.',
  inputSchema: {
    type: 'object',
    properties: {
      title: {
        type: 'string',
        description:
          "The title of the article. For multilingual articles, this will be the title of the default language's content",
        example: 'Thanks for everything',
      },
      description: {
        type: 'string',
        description:
          "The description of the article. For multilingual articles, this will be the description of the default language's content",
        example: 'Description of the Article',
      },
      body: {
        type: 'string',
        description:
          "The content of the article. For multilingual articles, this will be the body of the default language's content",
        example: '<p>Body of the Article</p>',
      },
      author_id: {
        type: 'integer',
        description:
          "The id of the author of the article. For multilingual articles, this will be the id of the author of the default language's content. Must be a teammate on the help center's workspace",
        example: 1295,
      },
      state: {
        type: 'string',
        description:
          "Whether the article will be published or will be a draft. Defaults to draft. For multilingual articles, this will be the state of the default language's content",
        enum: ['published', 'draft'],
        default: 'draft',
        example: 'published',
      },
      parent_id: {
        type: 'integer',
        description:
          "The id of the article's parent collection or section. An article without this field stands alone",
        example: 18,
      },
      parent_type: {
        type: 'string',
        description: 'The type of parent, which can either be a collection or section',
        enum: ['collection', 'section'],
        example: 'collection',
      },
      translated_content: {
        type: 'object',
        description:
          'The translated content of the article. The keys are the locale codes and the values are the translated content of the article',
        additionalProperties: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: 'The title of the article in the specified language',
            },
            description: {
              type: 'string',
              description: 'The description of the article in the specified language',
            },
            body: {
              type: 'string',
              description: 'The content of the article in the specified language',
            },
            author_id: {
              type: 'integer',
              description: 'The id of the author for this language version',
            },
            state: {
              type: 'string',
              enum: ['published', 'draft'],
              description: 'The state of the article in the specified language',
            },
          },
          required: ['title', 'author_id', 'state'],
        },
        example: {
          fr: {
            title: 'Merci pour tout',
            description: "Description de l'article",
            body: "Corps de l'article",
            author_id: 991266252,
            state: 'published',
          },
        },
      },
    },
    required: ['title', 'author_id'],
  },
};

/**
 * Update an existing article
 */
const UPDATE_ARTICLE_TOOL: Tool = {
  name: 'intercom_update_article',
  description: 'Update an existing article in your Help Center.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The unique identifier for the article which is given by Intercom',
        example: 123,
      },
      title: {
        type: 'string',
        description:
          "The title of the article. For multilingual articles, this will be the title of the default language's content",
        example: 'Updated title',
      },
      description: {
        type: 'string',
        description:
          "The description of the article. For multilingual articles, this will be the description of the default language's content",
        example: 'Updated description',
      },
      body: {
        type: 'string',
        description:
          "The content of the article. For multilingual articles, this will be the body of the default language's content",
        example: '<p>Updated body content</p>',
      },
      author_id: {
        type: 'integer',
        description:
          "The id of the author of the article. For multilingual articles, this will be the id of the author of the default language's content. Must be a teammate on the help center's workspace",
        example: 1295,
      },
      state: {
        type: 'string',
        description:
          "Whether the article will be published or will be a draft. For multilingual articles, this will be the state of the default language's content",
        enum: ['published', 'draft'],
        example: 'published',
      },
      parent_id: {
        type: 'string',
        description:
          "The id of the article's parent collection or section. An article without this field stands alone",
        example: '18',
      },
      parent_type: {
        type: 'string',
        description: 'The type of parent, which can either be a collection or section',
        enum: ['collection', 'section'],
        example: 'collection',
      },
      translated_content: {
        type: 'object',
        description:
          'The translated content of the article. The keys are the locale codes and the values are the translated content of the article',
        additionalProperties: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: 'The title of the article in the specified language',
            },
            description: {
              type: 'string',
              description: 'The description of the article in the specified language',
            },
            body: {
              type: 'string',
              description: 'The content of the article in the specified language',
            },
            author_id: {
              type: 'integer',
              description: 'The id of the author for this language version',
            },
            state: {
              type: 'string',
              enum: ['published', 'draft'],
              description: 'The state of the article in the specified language',
            },
          },
        },
      },
    },
    required: ['id'],
  },
};

/**
 * Delete an article
 */
const DELETE_ARTICLE_TOOL: Tool = {
  name: 'intercom_delete_article',
  description: 'Delete a single article from your Help Center.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'integer',
        description: 'The unique identifier for the article which is given by Intercom',
        example: 123,
      },
    },
    required: ['id'],
  },
};

/**
 * Search articles
 */
const SEARCH_ARTICLES_TOOL: Tool = {
  name: 'intercom_search_articles',
  description: 'Search articles in your Help Center using query filters.',
  inputSchema: {
    type: 'object',
    properties: {
      phrase: {
        type: 'string',
        description: 'The search phrase to look for in articles',
        example: 'getting started',
      },
      state: {
        type: 'string',
        description: 'Filter articles by their publication state',
        enum: ['published', 'draft'],
        example: 'published',
      },
      author_id: {
        type: 'integer',
        description: 'Filter articles by author ID',
        example: 1295,
      },
      parent_id: {
        type: 'integer',
        description: 'Filter articles by parent collection or section ID',
        example: 18,
      },
      parent_type: {
        type: 'string',
        description: 'Filter articles by parent type',
        enum: ['collection', 'section'],
        example: 'collection',
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
    required: [],
  },
};

/**
 * List help center collections
 */
const LIST_COLLECTIONS_TOOL: Tool = {
  name: 'intercom_list_collections',
  description: 'List all Help Center collections with pagination support.',
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
 * Get a specific collection by ID
 */
const GET_COLLECTION_TOOL: Tool = {
  name: 'intercom_get_collection',
  description: 'Retrieve a specific Help Center collection by its ID.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the collection which is given by Intercom',
        example: '123',
      },
    },
    required: ['id'],
  },
};

/**
 * Create a new collection
 */
const CREATE_COLLECTION_TOOL: Tool = {
  name: 'intercom_create_collection',
  description: 'Create a new Help Center collection.',
  inputSchema: {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        description:
          "The name of the collection. For multilingual collections, this will be the name of the default language's content",
        example: 'Getting Started',
      },
      description: {
        type: 'string',
        description:
          "The description of the collection. For multilingual collections, this will be the description of the default language's content",
        example: 'Collection for getting started articles',
      },
      parent_id: {
        type: 'string',
        description:
          'The id of the parent collection. If null then it will be created as the first level collection',
        example: '6871118',
        nullable: true,
      },
      help_center_id: {
        type: 'integer',
        description:
          'The id of the help center where the collection will be created. If null then it will be created in the default help center',
        example: 123,
        nullable: true,
      },
      translated_content: {
        type: 'object',
        description:
          'The translated content of the collection. The keys are the locale codes and the values are the translated content',
        additionalProperties: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'The name of the collection in the specified language',
            },
            description: {
              type: 'string',
              description: 'The description of the collection in the specified language',
            },
          },
        },
        nullable: true,
      },
    },
    required: ['name'],
  },
};

/**
 * Update an existing collection
 */
const UPDATE_COLLECTION_TOOL: Tool = {
  name: 'intercom_update_collection',
  description: 'Update an existing Help Center collection.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the collection which is given by Intercom',
        example: '123',
      },
      name: {
        type: 'string',
        description:
          "The name of the collection. For multilingual collections, this will be the name of the default language's content",
        example: 'Updated Collection Name',
      },
      description: {
        type: 'string',
        description:
          "The description of the collection. For multilingual collections, this will be the description of the default language's content",
        example: 'Updated collection description',
      },
      parent_id: {
        type: 'string',
        description:
          'The id of the parent collection. If null then it will be updated as the first level collection',
        example: '6871118',
        nullable: true,
      },
      translated_content: {
        type: 'object',
        description:
          'The translated content of the collection. The keys are the locale codes and the values are the translated content',
        additionalProperties: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'The name of the collection in the specified language',
            },
            description: {
              type: 'string',
              description: 'The description of the collection in the specified language',
            },
          },
        },
        nullable: true,
      },
    },
    required: ['id'],
  },
};

/**
 * Delete a collection
 */
const DELETE_COLLECTION_TOOL: Tool = {
  name: 'intercom_delete_collection',
  description: 'Delete a single Help Center collection.',
  inputSchema: {
    type: 'object',
    properties: {
      id: {
        type: 'string',
        description: 'The unique identifier for the collection which is given by Intercom',
        example: '123',
      },
    },
    required: ['id'],
  },
};

export const ARTICLE_TOOLS = [
  LIST_ARTICLES_TOOL,
  GET_ARTICLE_TOOL,
  CREATE_ARTICLE_TOOL,
  UPDATE_ARTICLE_TOOL,
  DELETE_ARTICLE_TOOL,
  SEARCH_ARTICLES_TOOL,
  LIST_COLLECTIONS_TOOL,
  GET_COLLECTION_TOOL,
  CREATE_COLLECTION_TOOL,
  UPDATE_COLLECTION_TOOL,
  DELETE_COLLECTION_TOOL,
] as const;
