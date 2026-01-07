#!/usr/bin/env node
import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { AsyncLocalStorage } from 'async_hooks';

// ─────────────────────────────────────────────────────────────────────────────
// Normalization Helpers - Creates Klavis-defined response schemas
// ─────────────────────────────────────────────────────────────────────────────

type MappingRule = string | ((source: Record<string, any>) => any);
type MappingRules = Record<string, MappingRule>;

/**
 * Safe dot-notation access. Returns undefined if path fails.
 */
function getPath(data: Record<string, any> | null | undefined, path: string): any {
  if (!data) return undefined;
  let current: any = data;
  for (const key of path.split('.')) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      return undefined;
    }
  }
  return current;
}

/**
 * Creates a new clean dictionary based strictly on the mapping rules.
 * Excludes fields with null/undefined values from the output.
 */
function normalize(source: Record<string, any>, mapping: MappingRules): Record<string, any> {
  const cleanData: Record<string, any> = {};
  for (const [targetKey, rule] of Object.entries(mapping)) {
    let value: any;
    if (typeof rule === 'string') {
      value = getPath(source, rule);
    } else if (typeof rule === 'function') {
      try {
        value = rule(source);
      } catch {
        value = undefined;
      }
    }
    if (value !== undefined && value !== null) {
      cleanData[targetKey] = value;
    }
  }
  return cleanData;
}

// ─────────────────────────────────────────────────────────────────────────────
// Mapping Rules - Klavis-defined field names
// ─────────────────────────────────────────────────────────────────────────────

const AUTHOR_RULES: MappingRules = {
  id: "ID",
  name: "name",
  url: "URL",
  avatarUrl: "avatar_URL",
  profileUrl: "profile_URL",
};

const CATEGORY_RULES: MappingRules = {
  id: "ID",
  name: "name",
  slug: "slug",
  postCount: "post_count",
};

const TAG_RULES: MappingRules = {
  id: "ID",
  name: "name",
  slug: "slug",
  postCount: "post_count",
};

const POST_RULES: MappingRules = {
  id: "ID",
  siteId: "site_ID",
  title: "title",
  content: "content",
  excerpt: "excerpt",
  slug: "slug",
  status: "status",
  type: "type",
  url: "URL",
  shortUrl: "short_URL",
  createdAt: "date",
  modifiedAt: "modified",
  likeCount: "like_count",
  commentCount: (x) => x.discussion?.comment_count,
  commentsOpen: (x) => x.discussion?.comments_open,
  featuredImage: "featured_image",
  format: "format",
  author: (x) => x.author ? normalize(x.author, AUTHOR_RULES) : undefined,
  categories: (x) => {
    const cats = x.categories;
    if (!cats || typeof cats !== 'object') return undefined;
    return Object.values(cats).map((c: any) => normalize(c, CATEGORY_RULES));
  },
  tags: (x) => {
    const tags = x.tags;
    if (!tags || typeof tags !== 'object') return undefined;
    return Object.values(tags).map((t: any) => normalize(t, TAG_RULES));
  },
};

const POST_LIST_RULES: MappingRules = {
  id: "ID",
  title: "title",
  content: "content",
  excerpt: "excerpt",
  slug: "slug",
  status: "status",
  type: "type",
  url: "URL",
  shortUrl: "short_URL",
  createdAt: "date",
  modifiedAt: "modified",
  likeCount: "like_count",
  commentCount: (x) => x.discussion?.comment_count,
  commentsOpen: (x) => x.discussion?.comments_open,
  featuredImage: "featured_image",
  format: "format",
  author: (x) => x.author ? normalize(x.author, AUTHOR_RULES) : undefined,
  categories: (x) => {
    const cats = x.categories;
    if (!cats || typeof cats !== 'object') return undefined;
    return Object.values(cats).map((c: any) => normalize(c, CATEGORY_RULES));
  },
  tags: (x) => {
    const tags = x.tags;
    if (!tags || typeof tags !== 'object') return undefined;
    return Object.values(tags).map((t: any) => normalize(t, TAG_RULES));
  },
};

const TOP_POST_RULES: MappingRules = {
  id: "id",
  title: "title",
  url: "href",
  views: "views",
};

const SITE_RULES: MappingRules = {
  id: "ID",
  name: "name",
  description: "description",
  url: "URL",
  slug: "slug",
  isPrivate: "is_private",
  isComingSoon: "is_coming_soon",
  language: "lang",
  postCount: "post_count",
  subscriberCount: "subscribers_count",
  iconUrl: (x) => x.icon?.img,
  logoUrl: (x) => x.logo?.url,
  isJetpack: "jetpack",
  isMultisite: "is_multisite",
  ownerId: "site_owner",
  plan: (x) => x.plan ? {
    id: x.plan.product_id,
    name: x.plan.product_name_short,
    slug: x.plan.product_slug,
  } : undefined,
};

const SITE_STATS_RULES: MappingRules = {
  visitors: "stats.visitors",
  views: "stats.views",
  visitorsToday: "stats.visitors_today",
  viewsToday: "stats.views_today",
  viewsBestDay: "stats.views_best_day",
  viewsBestDayTotal: "stats.views_best_day_total",
  postCount: "stats.posts",
  commentCount: "stats.comments",
  followers: "stats.followers",
};

const USER_SITE_RULES: MappingRules = {
  id: "ID",
  name: "name",
  description: "description",
  url: "URL",
  slug: "slug",
  isPrivate: "is_private",
  isVisible: "visible",
  iconUrl: (x) => x.icon?.img,
  plan: (x) => x.plan ? {
    name: x.plan.product_name_short,
    slug: x.plan.product_slug,
  } : undefined,
};

const getWordPressMcpServer = () => {
  const server = new Server(
    {
      name: "klavis-ai/wordpress",
      version: "0.1.0",
    },
    {
      capabilities: {
        resources: {},
        tools: {},
      },
    },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: "wordpress_create_post",
          description: "Create a new WordPress post",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
              title: { type: "string", description: "Post title in html format" },
              content: { type: "string", description: "Post content in html format" },
              status: { type: "string", description: "Post status (draft, publish, private, pending etc.)", default: "publish" }
            },
            required: ["site", "title", "content"]
          },
          annotations: { category: 'WORDPRESS_POST' },
        },
        {
          name: "wordpress_get_posts",
          description: "Get a list of WordPress posts",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
              number: { type: "number", description: "Number of posts to retrieve", default: 10 },
              page: { type: "number", description: "Page number", default: 1 }
            },
            required: ["site"]
          },
          annotations: { category: 'WORDPRESS_POST', readOnlyHint: true },
        },
        {
          name: "wordpress_update_post",
          description: "Update an existing WordPress post",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
              postId: { type: "number", description: "ID of the post to update" },
              title: { type: "string", description: "Post title in html format" },
              content: { type: "string", description: "Post content in html format" },
              status: { type: "string", description: "Post status (draft, publish, private, pending etc.)" },
            },
            required: ["site", "postId"]
          },
          annotations: { category: 'WORDPRESS_POST' },
        },
        {
          name: "wordpress_get_top_posts",
          description: "Get top WordPress posts for a site",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
            },
            required: ["site"]
          },
          annotations: { category: 'WORDPRESS_POST' }
        },
        {
          name: "wordpress_get_site_info",
          description: "Get information about a WordPress site",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
            },
            required: ["site"]
          },
          annotations: { category: 'WORDPRESS_SITE' }
        },
        {
          name: "wordpress_get_site_stats",
          description: "Get statistics for a WordPress site",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
            },
            required: ["site"]
          },
          annotations: { category: 'WORDPRESS_SITE' }
        },
        {
          name: "wordpress_get_user_sites",
          description: "Get all WordPress sites the authenticated user has access to",
          inputSchema: {
            type: "object",
            properties: {},
            required: []
          },
          annotations: { category: 'WORDPRESS_USER' }
        }
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const params = request.params.arguments || {};

    try {
      switch (request.params.name) {
        case 'wordpress_create_post': {
          if (!params.site || !params.title || !params.content) {
            throw new Error('Site, title, and content are required for creating a post');
          }

          const client = getClient();
          const response = await client.post(`/sites/${params.site}/posts/new`, {
            title: params.title,
            content: params.content,
            status: params.status || 'draft',
          });
          const data = await response.json();
          const normalizedPost = normalize(data, POST_RULES);

          return {
            content: [{ type: "text", text: JSON.stringify(normalizedPost, null, 2) }],
            isError: false,
          };
        }

        case 'wordpress_get_posts': {
          if (!params.site) {
            throw new Error('Site is required for getting posts');
          }

          const client = getClient();
          const number = params.number || 10;
          const page = params.page || 1;
          const response = await client.get(`/sites/${params.site}/posts/?number=${number}&page=${page}`);
          const data = await response.json();
          const normalizedData = {
            totalCount: data.found,
            posts: (data.posts || []).map((post: Record<string, any>) => normalize(post, POST_LIST_RULES)),
          };

          return {
            content: [{ type: "text", text: JSON.stringify(normalizedData, null, 2) }],
            isError: false,
          };
        }

        case 'wordpress_update_post': {
          if (!params.site || !params.postId) {
            throw new Error('Site and Post ID are required for updating a post');
          }

          const updateData: Record<string, any> = {};
          if (params.title) updateData.title = params.title;
          if (params.content) updateData.content = params.content;
          if (params.status) updateData.status = params.status;

          const client = getClient();
          const response = await client.post(`/sites/${params.site}/posts/${params.postId}`, updateData);
          const data = await response.json();
          const normalizedPost = normalize(data, POST_RULES);

          return {
            content: [{ type: "text", text: JSON.stringify(normalizedPost, null, 2) }],
            isError: false,
          };
        }

        case 'wordpress_get_top_posts': {
          if (!params.site) {
            throw new Error('Site is required for getting top posts');
          }

          const client = getClient();
          const response = await client.get(`/sites/${params.site}/stats/top-posts`);
          const data = await response.json();
          
          // Extract posts from the summary array and normalize them
          const topPosts: Record<string, any>[] = [];
          if (data.summary && Array.isArray(data.summary)) {
            for (const period of data.summary) {
              if (period.postviews && Array.isArray(period.postviews)) {
                for (const post of period.postviews) {
                  topPosts.push(normalize(post, TOP_POST_RULES));
                }
              }
            }
          }
          
          const normalizedData = {
            date: data.date,
            period: data.period,
            posts: topPosts,
          };

          return {
            content: [{ type: "text", text: JSON.stringify(normalizedData, null, 2) }],
            isError: false,
          };
        }

        case 'wordpress_get_site_info': {
          if (!params.site) {
            throw new Error('Site identifier is required');
          }

          const client = getClient();
          const response = await client.get(`/sites/${params.site}`);
          const data = await response.json();
          const normalizedSite = normalize(data, SITE_RULES);

          return {
            content: [{ type: "text", text: JSON.stringify(normalizedSite, null, 2) }],
            isError: false,
          };
        }

        case 'wordpress_get_site_stats': {
          if (!params.site) {
            throw new Error('Site identifier is required');
          }

          const client = getClient();
          const response = await client.get(`/sites/${params.site}/stats`);
          const data = await response.json();
          const normalizedStats = normalize(data, SITE_STATS_RULES);

          return {
            content: [{ type: "text", text: JSON.stringify(normalizedStats, null, 2) }],
            isError: false,
          };
        }

        case 'wordpress_get_user_sites': {
          const client = getClient();
          const response = await client.get('/me/sites');
          const data = await response.json();
          const normalizedData = {
            sites: (data.sites || []).map((site: Record<string, any>) => normalize(site, USER_SITE_RULES)),
          };

          return {
            content: [{ type: "text", text: JSON.stringify(normalizedData, null, 2) }],
            isError: false,
          };
        }

        default:
          throw new Error(`Unknown tool: ${request.params.name}`);
      }
    } catch (error) {
      const err = error as Error;
      throw new Error(`WordPress API error: ${err.message}`);
    }
  });

  return server;
}

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  auth_token: string;
}>();

function getClient() {
  const store = asyncLocalStorage.getStore()!;
  const auth_token = store.auth_token;

  return {
    get: async (path: string) => {
      const response = await fetch(`https://public-api.wordpress.com/rest/v1.1${path}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${auth_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error ${response.status}: ${errorText}`);
      }

      return response;
    },
    post: async (path: string, data: any) => {
      const response = await fetch(`https://public-api.wordpress.com/rest/v1.1${path}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${auth_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error ${response.status}: ${errorText}`);
      }

      return response;
    }
  };
}

function extractAccessToken(req: Request): string {
  let authData = process.env.AUTH_DATA;
  
  if (!authData && req.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data JSON:', error);
    }
  }

  if (!authData) {
    console.error('Error: WordPress access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
    return '';
  }

  const authDataJson = JSON.parse(authData);
  return authDataJson.access_token ?? '';
}

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const auth_token = extractAccessToken(req);


  const server = getWordPressMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ auth_token }, async () => {
      await transport.handleRequest(req, res, req.body);
    });
    res.on('close', () => {
      console.log('Request closed');
      transport.close();
      server.close();
    });
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: Response) => {
  console.log('Received GET MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport(`/messages`, res);

  // Set up cleanup when connection closes
  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    try {
      transports.delete(transport.sessionId);
    } finally {
    }
  });

  transports.set(transport.sessionId, transport);

  const server = getWordPressMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    const auth_token = extractAccessToken(req);

    asyncLocalStorage.run({
      auth_token
    }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

app.listen(5000, () => {
  console.log('server running on port 5000');
});
