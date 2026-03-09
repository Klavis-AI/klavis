import fs from 'node:fs'
import path from 'node:path'

import { OpenAPIV3 } from 'openapi-types'
import OpenAPISchemaValidator from 'openapi-schema-validator'

import { MCPProxy, precomputeTools, type PrecomputedTools } from './openapi-mcp-server/mcp/proxy.js'

export class ValidationError extends Error {
  constructor(public errors: any[]) {
    super('OpenAPI validation failed')
    this.name = 'ValidationError'
  }
}

async function loadOpenApiSpec(specPath: string, baseUrl: string | undefined): Promise<OpenAPIV3.Document> {
  let rawSpec: string

  try {
    rawSpec = fs.readFileSync(path.resolve(process.cwd(), specPath), 'utf-8')
  } catch (error) {
    console.error('Failed to read OpenAPI specification file:', (error as Error).message)
    process.exit(1)
  }

  // Parse and validate the OpenApi Spec
  try {
    const parsed = JSON.parse(rawSpec)

    // Override baseUrl if specified.
    if (baseUrl) {
      parsed.servers[0].url = baseUrl
    }

    return parsed as OpenAPIV3.Document
  } catch (error) {
    if (error instanceof ValidationError) {
      throw error
    }
    console.error('Failed to parse OpenAPI spec:', (error as Error).message)
    process.exit(1)
  }
}

let cachedSpec: OpenAPIV3.Document | null = null
let cachedPrecomputed: PrecomputedTools | null = null

/**
 * Pre-load the OpenAPI spec and precompute tools once at startup.
 * This avoids re-parsing and re-converting on every request.
 */
export async function preloadSpec(specPath: string, baseUrl: string | undefined): Promise<void> {
  cachedSpec = await loadOpenApiSpec(specPath, baseUrl)
  cachedPrecomputed = precomputeTools(cachedSpec)
  console.log('OpenAPI spec and tools pre-computed successfully')
}

export async function initProxy(specPath: string, baseUrl: string | undefined, options: { pageIds?: string[]; pageUrls?: string[]; notionToken?: string } = {}) {
  const openApiSpec = cachedSpec ?? await loadOpenApiSpec(specPath, baseUrl)
  const proxy = new MCPProxy('Notion API', openApiSpec, options, cachedPrecomputed ?? undefined)
  return proxy
}
