import { IntercomClient } from '../../client/intercomClient.js';
import { validateArticleId, validateRequiredFields } from '../../utils/validation.js';

export class ArticleHandler {
  constructor(private intercomClient: IntercomClient) {}

  async listArticles(data: { startingAfter?: string; perPage?: number }): Promise<any> {
    const params = new URLSearchParams();

    if (data.startingAfter) {
      params.append('starting_after', data.startingAfter);
    }

    if (data.perPage) {
      params.append('per_page', data.perPage.toString());
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/articles?${queryString}` : '/articles';

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getArticle(articleId: number): Promise<any> {
    if (!validateArticleId(articleId.toString())) {
      throw new Error('Invalid article ID provided');
    }

    return this.intercomClient.makeRequest(`/articles/${articleId}`, {
      method: 'GET',
    });
  }

  async createArticle(data: {
    title: string;
    description?: string;
    body?: string;
    authorId: number;
    state?: 'published' | 'draft';
    parentId?: number;
    parentType?: 'collection' | 'section';
    translatedContent?: Record<
      string,
      {
        title?: string;
        description?: string;
        body?: string;
        authorId?: number;
        state?: 'published' | 'draft';
      }
    >;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['title', 'authorId']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload: any = {
      title: data.title,
      author_id: data.authorId,
    };

    if (data.description !== undefined) payload.description = data.description;
    if (data.body !== undefined) payload.body = data.body;
    if (data.state !== undefined) payload.state = data.state;
    if (data.parentId !== undefined) payload.parent_id = data.parentId;
    if (data.parentType !== undefined) payload.parent_type = data.parentType;

    if (data.translatedContent !== undefined) {
      payload.translated_content = {};
      for (const [locale, content] of Object.entries(data.translatedContent)) {
        payload.translated_content[locale] = {};
        if (content.title !== undefined) payload.translated_content[locale].title = content.title;
        if (content.description !== undefined)
          payload.translated_content[locale].description = content.description;
        if (content.body !== undefined) payload.translated_content[locale].body = content.body;
        if (content.authorId !== undefined)
          payload.translated_content[locale].author_id = content.authorId;
        if (content.state !== undefined) payload.translated_content[locale].state = content.state;
      }
    }

    return this.intercomClient.makeRequest('/articles', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateArticle(
    articleId: number,
    data: {
      title?: string;
      description?: string;
      body?: string;
      authorId?: number;
      state?: 'published' | 'draft';
      parentId?: string;
      parentType?: 'collection' | 'section';
      translatedContent?: Record<
        string,
        {
          title?: string;
          description?: string;
          body?: string;
          authorId?: number;
          state?: 'published' | 'draft';
        }
      >;
    },
  ): Promise<any> {
    if (!validateArticleId(articleId.toString())) {
      throw new Error('Invalid article ID provided');
    }

    const payload: any = {};

    if (data.title !== undefined) payload.title = data.title;
    if (data.description !== undefined) payload.description = data.description;
    if (data.body !== undefined) payload.body = data.body;
    if (data.authorId !== undefined) payload.author_id = data.authorId;
    if (data.state !== undefined) payload.state = data.state;
    if (data.parentId !== undefined) payload.parent_id = data.parentId;
    if (data.parentType !== undefined) payload.parent_type = data.parentType;

    if (data.translatedContent !== undefined) {
      payload.translated_content = {};
      for (const [locale, content] of Object.entries(data.translatedContent)) {
        payload.translated_content[locale] = {};
        if (content.title !== undefined) payload.translated_content[locale].title = content.title;
        if (content.description !== undefined)
          payload.translated_content[locale].description = content.description;
        if (content.body !== undefined) payload.translated_content[locale].body = content.body;
        if (content.authorId !== undefined)
          payload.translated_content[locale].author_id = content.authorId;
        if (content.state !== undefined) payload.translated_content[locale].state = content.state;
      }
    }

    return this.intercomClient.makeRequest(`/articles/${articleId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteArticle(articleId: number): Promise<any> {
    if (!validateArticleId(articleId.toString())) {
      throw new Error('Invalid article ID provided');
    }

    return this.intercomClient.makeRequest(`/articles/${articleId}`, {
      method: 'DELETE',
    });
  }

  async searchArticles(data: {
    phrase?: string;
    state?: 'published' | 'draft';
    authorId?: number;
    parentId?: number;
    parentType?: 'collection' | 'section';
    startingAfter?: string;
    perPage?: number;
  }): Promise<any> {
    const params = new URLSearchParams();

    if (data.phrase) params.append('phrase', data.phrase);
    if (data.state) params.append('state', data.state);
    if (data.authorId) params.append('author_id', data.authorId.toString());
    if (data.parentId) params.append('parent_id', data.parentId.toString());
    if (data.parentType) params.append('parent_type', data.parentType);
    if (data.startingAfter) params.append('starting_after', data.startingAfter);
    if (data.perPage) params.append('per_page', data.perPage.toString());

    const queryString = params.toString();
    const endpoint = queryString ? `/articles/search?${queryString}` : '/articles/search';

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async listCollections(data: { startingAfter?: string; perPage?: number }): Promise<any> {
    const params = new URLSearchParams();

    if (data.startingAfter) {
      params.append('starting_after', data.startingAfter);
    }

    if (data.perPage) {
      params.append('per_page', data.perPage.toString());
    }

    const queryString = params.toString();
    const endpoint = queryString
      ? `/help_center/collections?${queryString}`
      : '/help_center/collections';

    return this.intercomClient.makeRequest(endpoint, {
      method: 'GET',
    });
  }

  async getCollection(collectionId: string): Promise<any> {
    if (!collectionId || typeof collectionId !== 'string') {
      throw new Error('Invalid collection ID provided');
    }

    return this.intercomClient.makeRequest(`/help_center/collections/${collectionId}`, {
      method: 'GET',
    });
  }

  async createCollection(data: {
    name: string;
    description?: string;
    parentId?: string;
    helpCenterId?: number;
    translatedContent?: Record<
      string,
      {
        name?: string;
        description?: string;
      }
    >;
  }): Promise<any> {
    const validation = validateRequiredFields(data, ['name']);
    if (!validation.isValid) {
      throw new Error(`Missing required fields: ${validation.missingFields.join(', ')}`);
    }

    const payload: any = {
      name: data.name,
    };

    if (data.description !== undefined) payload.description = data.description;
    if (data.parentId !== undefined) payload.parent_id = data.parentId;
    if (data.helpCenterId !== undefined) payload.help_center_id = data.helpCenterId;

    if (data.translatedContent !== undefined) {
      payload.translated_content = {};
      for (const [locale, content] of Object.entries(data.translatedContent)) {
        payload.translated_content[locale] = {};
        if (content.name !== undefined) payload.translated_content[locale].name = content.name;
        if (content.description !== undefined)
          payload.translated_content[locale].description = content.description;
      }
    }

    return this.intercomClient.makeRequest('/help_center/collections', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateCollection(
    collectionId: string,
    data: {
      name?: string;
      description?: string;
      parentId?: string;
      translatedContent?: Record<
        string,
        {
          name?: string;
          description?: string;
        }
      >;
    },
  ): Promise<any> {
    if (!collectionId || typeof collectionId !== 'string') {
      throw new Error('Invalid collection ID provided');
    }

    const payload: any = {};

    if (data.name !== undefined) payload.name = data.name;
    if (data.description !== undefined) payload.description = data.description;
    if (data.parentId !== undefined) payload.parent_id = data.parentId;

    if (data.translatedContent !== undefined) {
      payload.translated_content = {};
      for (const [locale, content] of Object.entries(data.translatedContent)) {
        payload.translated_content[locale] = {};
        if (content.name !== undefined) payload.translated_content[locale].name = content.name;
        if (content.description !== undefined)
          payload.translated_content[locale].description = content.description;
      }
    }

    return this.intercomClient.makeRequest(`/help_center/collections/${collectionId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async deleteCollection(collectionId: string): Promise<any> {
    if (!collectionId || typeof collectionId !== 'string') {
      throw new Error('Invalid collection ID provided');
    }

    return this.intercomClient.makeRequest(`/help_center/collections/${collectionId}`, {
      method: 'DELETE',
    });
  }
}
