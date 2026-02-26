import { HttpClient } from '../client/http-client.js'

export interface PageAccessControlOptions {
  pageIds?: string[]
  pageUrls?: string[]
  httpClient: HttpClient
}

export class PageAccessController {
  private rootPageIds: Set<string> = new Set()
  private httpClient: HttpClient
  private pageCache = new Map<string, { parentId: string | null; isAllowed: boolean }>()

  constructor(options: PageAccessControlOptions) {
    this.httpClient = options.httpClient
    this.initializeRootPages(options)
  }

  private initializeRootPages(options: PageAccessControlOptions) {
    const allPageIds = new Set<string>()
    
    // Process command line/option page IDs
    if (options.pageIds) {
      for (const pageId of options.pageIds) {
        if (pageId.trim()) {
          allPageIds.add(this.normalizePageId(pageId.trim()))
        }
      }
    }
    
    // Process command line/option page URLs
    if (options.pageUrls) {
      for (const pageUrl of options.pageUrls) {
        if (pageUrl.trim()) {
          try {
            const pageId = this.extractPageIdFromUrl(pageUrl.trim())
            allPageIds.add(pageId)
          } catch (error) {
            console.error(`Invalid page URL: ${pageUrl}`, error)
          }
        }
      }
    }
    
    // Process environment variables as fallback
    if (allPageIds.size === 0) {
      const envPageIds = process.env.NOTION_ROOT_PAGE_ID?.split(',').map(id => id.trim()).filter(id => id.length > 0) || []
      const envPageUrls = process.env.NOTION_ROOT_PAGE_URL?.split(',').map(url => url.trim()).filter(url => url.length > 0) || []
      
      for (const pageId of envPageIds) {
        allPageIds.add(this.normalizePageId(pageId))
      }
      
      for (const pageUrl of envPageUrls) {
        try {
          const pageId = this.extractPageIdFromUrl(pageUrl)
          allPageIds.add(pageId)
        } catch (error) {
          console.error(`Invalid page URL from env: ${pageUrl}`, error)
        }
      }
    }
    
    this.rootPageIds = allPageIds
    
    if (this.rootPageIds.size > 0) {
      console.log(`Page access control enabled. Root pages: ${Array.from(this.rootPageIds).join(', ')}`)
    }
  }

  /**
   * Extract page ID from various Notion URL formats
   */
  private extractPageIdFromUrl(url: string): string {
    // Support various Notion URL formats:
    // https://www.notion.so/page-title-abc123def456
    // https://notion.so/abc123def456
    // https://www.notion.so/workspace/page-title-abc123def456
    const match = url.match(/([a-f0-9]{32}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/i)
    if (!match) {
      throw new Error(`Invalid Notion page URL format: ${url}`)
    }
    return this.normalizePageId(match[1])
  }

  /**
   * Normalize page ID to UUID format (with dashes)
   */
  private normalizePageId(pageId: string): string {
    // Remove any existing dashes and convert to lowercase
    const cleanId = pageId.replace(/-/g, '').toLowerCase()
    
    // Validate length
    if (cleanId.length !== 32) {
      throw new Error(`Invalid page ID format: ${pageId}`)
    }

    // Add UUID dashes: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    return `${cleanId.slice(0, 8)}-${cleanId.slice(8, 12)}-${cleanId.slice(12, 16)}-${cleanId.slice(16, 20)}-${cleanId.slice(20)}`
  }

  /**
   * Check if page access control is enabled
   */
  isEnabled(): boolean {
    return this.rootPageIds.size > 0
  }

  /**
   * Check if a resource ID is allowed (page, database, block, etc.)
   */
  async isPageAllowed(resourceId: string): Promise<boolean> {
    if (!this.isEnabled()) {
      return true // No access control, allow all
    }

    const normalizedResourceId = this.normalizePageId(resourceId)
    
    // Check if this is one of the root pages
    if (this.rootPageIds.has(normalizedResourceId)) {
      return true
    }

    // Check cache first
    if (this.pageCache.has(normalizedResourceId)) {
      return this.pageCache.get(normalizedResourceId)!.isAllowed
    }

    // Find the actual page ID for this resource
    const actualPageId = await this.findRootPageForResource(normalizedResourceId)
    
    if (!actualPageId) {
      // Cache as not allowed
      this.pageCache.set(normalizedResourceId, { parentId: null, isAllowed: false })
      return false
    }

    // Check if the actual page is allowed
    const isAllowed = await this.checkPageHierarchy(actualPageId)
    
    // Cache the result for the original resource ID
    this.pageCache.set(normalizedResourceId, { parentId: actualPageId, isAllowed })
    
    return isAllowed
  }

  /**
   * Traverse page hierarchy to check if page is descendant of any root page
   */
  private async checkPageHierarchy(pageId: string): Promise<boolean> {
    const visited = new Set<string>()
    let currentPageId: string | null = pageId

    while (currentPageId && !visited.has(currentPageId)) {
      visited.add(currentPageId)

      // Check if we've reached any of the root pages
      if (this.rootPageIds.has(currentPageId)) {
        // Cache all visited pages as allowed
        visited.forEach(id => {
          this.pageCache.set(id, { parentId: null, isAllowed: true })
        })
        return true
      }

      try {
        const parentId = await this.getParentPageId(currentPageId)
        this.pageCache.set(currentPageId, { parentId, isAllowed: false }) // Will update if allowed
        if (parentId) {
          currentPageId = parentId
        } else {
          break // No parent, we've reached the top
        }
      } catch (error) {
        console.error(`Failed to get parent for page ${currentPageId}:`, error)
        // Cache as not allowed
        this.pageCache.set(currentPageId, { parentId: null, isAllowed: false })
        return false
      }
    }

    // Didn't find any root page, cache all visited pages as not allowed
    visited.forEach(id => {
      if (!this.pageCache.has(id)) {
        this.pageCache.set(id, { parentId: null, isAllowed: false })
      }
    })
    return false
  }

  private async getParentPageId(pageId: string): Promise<string | null> {
    try {
      // Use the get-page operation to retrieve page details
      const operation = {
        operationId: 'retrieve-a-page',
        method: 'get',
        path: '/v1/pages/{page_id}',
        parameters: [
          {
            name: 'page_id',
            in: 'path' as const,
            required: true,
            schema: { 
              type: 'string' as const, 
              format: 'uuid' 
            }
          }
        ],
        responses: {}
      } as any

      const response = await this.httpClient.executeOperation(operation, { page_id: pageId })
      const pageData = response.data

      // Extract parent information
      if (pageData?.parent) {
        if (pageData.parent.type === 'page_id') {
          return pageData.parent.page_id
        } else if (pageData.parent.type === 'database_id') {
          // For database pages, we need to check the database parent
          return await this.getDatabaseParent(pageData.parent.database_id)
        } else if (pageData.parent.type === 'block_id') {
          // For pages that are children of blocks, we need to trace the block hierarchy
          // until we find the parent page
          return await this.resolveBlockToPage(pageData.parent.block_id)
        }
      }
      
      return null // Top-level page
    } catch (error) {
      console.error(`Error fetching page ${pageId}:`, error)
      throw error
    }
  }

  /**
   * Resolve a block ID to its parent page by tracing the block hierarchy
   */
  private async resolveBlockToPage(blockId: string): Promise<string | null> {
    try {
      const operation = {
        operationId: 'retrieve-a-block',
        method: 'get',
        path: '/v1/blocks/{block_id}',
        parameters: [
          {
            name: 'block_id',
            in: 'path' as const,
            required: true,
            schema: { 
              type: 'string' as const, 
              format: 'uuid' 
            }
          }
        ],
        responses: {}
      } as any

      const response = await this.httpClient.executeOperation(operation, { block_id: blockId })
      const blockData = response.data

      // If this block's parent is a page, we found it
      if (blockData?.parent?.type === 'page_id') {
        return blockData.parent.page_id
      }
      // If this block's parent is another block, recurse
      else if (blockData?.parent?.type === 'block_id') {
        return await this.resolveBlockToPage(blockData.parent.block_id)
      }
      // If this block's parent is a database, get the database's parent
      else if (blockData?.parent?.type === 'database_id') {
        return await this.getDatabaseParent(blockData.parent.database_id)
      }
      
      return null // No parent found
    } catch (error) {
      console.error(`Error resolving block ${blockId} to page:`, error)
      return null
    }
  }

  private async getDatabaseParent(databaseId: string): Promise<string | null> {
    try {
      const operation = {
        operationId: 'retrieve-a-database',
        method: 'get', 
        path: '/v1/databases/{database_id}',
        parameters: [
          {
            name: 'database_id',
            in: 'path' as const,
            required: true,
            schema: { 
              type: 'string' as const, 
              format: 'uuid' 
            }
          }
        ],
        responses: {}
      } as any

      const response = await this.httpClient.executeOperation(operation, { database_id: databaseId })
      const dbData = response.data

      if (dbData?.parent?.type === 'page_id') {
        return dbData.parent.page_id
      } else if (dbData?.parent?.type === 'block_id') {
        // Database is inside a block, resolve the block to its parent page
        return await this.resolveBlockToPage(dbData.parent.block_id)
      }
      
      return null
    } catch (error) {
      console.error(`Error fetching database ${databaseId}:`, error)
      return null
    }
  }

  /**
   * Find the root page for any type of resource (page, database, block, etc.)
   */
  private async findRootPageForResource(resourceId: string): Promise<string | null> {
    try {
      // First, try treating it as a page ID
      try {
        const operation = {
          operationId: 'retrieve-a-page',
          method: 'get',
          path: '/v1/pages/{page_id}',
          parameters: [
            {
              name: 'page_id',
              in: 'path' as const,
              required: true,
              schema: { 
                type: 'string' as const, 
                format: 'uuid' 
              }
            }
          ],
          responses: {}
        } as any

        await this.httpClient.executeOperation(operation, { page_id: resourceId })
        // If successful, it's a page ID
        return resourceId
      } catch (error: any) {
        // If it fails, try other resource types
      }

      // Try treating it as a database ID
      try {
        const parentPageId = await this.getDatabaseParent(resourceId)
        if (parentPageId) {
          return parentPageId
        }
      } catch (error: any) {
        // If it fails, try block ID
      }

      // Try treating it as a block ID
      try {
        const parentPageId = await this.resolveBlockToPage(resourceId)
        if (parentPageId) {
          return parentPageId
        }
      } catch (error: any) {
        // All attempts failed
      }

      return null
    } catch (error) {
      console.error(`Error finding root page for resource ${resourceId}:`, error)
      return null
    }
  }

  /**
   * Extract page ID from various API endpoints
   */
  extractPageIdFromRequest(path: string, params: Record<string, any>): string | null {
    // Direct page operations
    if (path.includes('/pages/') && params.page_id) {
      return params.page_id
    }

    // Block operations (blocks belong to pages)
    if (path.includes('/blocks/') && params.block_id) {
      // For block operations, the block_id might be a page_id
      return params.block_id
    }

    // Database query operations
    if (path.includes('/databases/') && path.includes('/query') && params.database_id) {
      // We'll need to check if this database is allowed
      return params.database_id
    }

    // Page creation - check parent
    if (path.includes('/pages') && params.parent) {
      if (params.parent.page_id) {
        return params.parent.page_id
      } else if (params.parent.database_id) {
        return params.parent.database_id
      }
    }

    return null
  }

  /**
   * Clear the cache (useful for testing or manual refresh)
   */
  clearCache(): void {
    this.pageCache.clear()
  }
}