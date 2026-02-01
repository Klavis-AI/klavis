import { MCPProxy } from '../proxy'
import { OpenAPIV3 } from 'openapi-types'
import { HttpClient } from '../../client/http-client'
import type { Transport } from '@modelcontextprotocol/sdk/shared/transport.js'
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest'

// Mock the dependencies
vi.mock('../../client/http-client')
vi.mock('@modelcontextprotocol/sdk/server/index.js')

describe('MCPProxy', () => {
  let proxy: MCPProxy
  let mockOpenApiSpec: OpenAPIV3.Document

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks()

    // Setup minimal OpenAPI spec for testing
    mockOpenApiSpec = {
      openapi: '3.0.0',
      servers: [{ url: 'http://localhost:3000' }],
      info: {
        title: 'Test API',
        version: '1.0.0',
      },
      paths: {
        '/test': {
          get: {
            operationId: 'getTest',
            responses: {
              '200': {
                description: 'Success',
              },
            },
          },
        },
      },
    }

    proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
  })

  describe('listTools handler', () => {
    it('should return converted tools from OpenAPI spec', async () => {
      const server = (proxy as any).server
      const listToolsHandler = server.setRequestHandler.mock.calls[0].filter((x: unknown) => typeof x === 'function')[0]
      const result = await listToolsHandler()

      expect(result).toHaveProperty('tools')
      expect(Array.isArray(result.tools)).toBe(true)
    })

    it('should truncate tool names exceeding 64 characters', async () => {
      // Setup OpenAPI spec with long tool names
      mockOpenApiSpec.paths = {
        '/test': {
          get: {
            operationId: 'a'.repeat(65),
            responses: {
              '200': {
                description: 'Success'
              }
            }
          }
        }
      }
      proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      const server = (proxy as any).server
      const listToolsHandler = server.setRequestHandler.mock.calls[0].filter((x: unknown) => typeof x === 'function')[0];
      const result = await listToolsHandler()

      expect(result.tools[0].name.length).toBeLessThanOrEqual(64)
    })
  })

  describe('callTool handler', () => {
    it('should execute operation and return formatted response', async () => {
      // Mock HttpClient response
      const mockResponse = {
        data: { message: 'success' },
        status: 200,
        headers: new Headers({
          'content-type': 'application/json',
        }),
      }
      ;(HttpClient.prototype.executeOperation as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse)

      // Set up the openApiLookup with our test operation
      ;(proxy as any).openApiLookup = {
        'API-getTest': {
          operationId: 'getTest',
          responses: { '200': { description: 'Success' } },
          method: 'get',
          path: '/test',
        },
      }

      const server = (proxy as any).server
      const handlers = server.setRequestHandler.mock.calls.flatMap((x: unknown[]) => x).filter((x: unknown) => typeof x === 'function')
      const callToolHandler = handlers[1]

      const result = await callToolHandler({
        params: {
          name: 'API-getTest',
          arguments: {},
        },
      })

      expect(result).toEqual({
        content: [
          {
            type: 'text',
            text: JSON.stringify({ message: 'success' }),
          },
        ],
      })
    })

    it('should throw error for non-existent operation', async () => {
      const server = (proxy as any).server
      const handlers = server.setRequestHandler.mock.calls.flatMap((x: unknown[]) => x).filter((x: unknown) => typeof x === 'function')
      const callToolHandler = handlers[1]

      await expect(
        callToolHandler({
          params: {
            name: 'nonExistentMethod',
            arguments: {},
          },
        }),
      ).rejects.toThrow('Method nonExistentMethod not found')
    })

    it('should handle tool names exceeding 64 characters', async () => {
      // Mock HttpClient response
      const mockResponse = {
        data: { message: 'success' },
        status: 200,
        headers: new Headers({
          'content-type': 'application/json'
        })
      };
      (HttpClient.prototype.executeOperation as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

      // Set up the openApiLookup with a long tool name
      const longToolName = 'a'.repeat(65)
      const truncatedToolName = longToolName.slice(0, 64)
      ;(proxy as any).openApiLookup = {
        [truncatedToolName]: {
          operationId: longToolName,
          responses: { '200': { description: 'Success' } },
          method: 'get',
          path: '/test'
        }
      };

      const server = (proxy as any).server;
      const handlers = server.setRequestHandler.mock.calls.flatMap((x: unknown[]) => x).filter((x: unknown) => typeof x === 'function');
      const callToolHandler = handlers[1];

      const result = await callToolHandler({
        params: {
          name: truncatedToolName,
          arguments: {}
        }
      })

      expect(result).toEqual({
        content: [
          {
            type: 'text',
            text: JSON.stringify({ message: 'success' })
          }
        ]
      })
    })
  })

  describe('getContentType', () => {
    it('should return correct content type for different headers', () => {
      const getContentType = (proxy as any).getContentType.bind(proxy)

      expect(getContentType(new Headers({ 'content-type': 'text/plain' }))).toBe('text')
      expect(getContentType(new Headers({ 'content-type': 'application/json' }))).toBe('text')
      expect(getContentType(new Headers({ 'content-type': 'image/jpeg' }))).toBe('image')
      expect(getContentType(new Headers({ 'content-type': 'application/octet-stream' }))).toBe('binary')
      expect(getContentType(new Headers())).toBe('binary')
    })
  })

  describe('parseHeadersFromEnv', () => {
    const originalEnv = process.env

    beforeEach(() => {
      process.env = { ...originalEnv }
    })

    afterEach(() => {
      process.env = originalEnv
    })

    it('should parse valid JSON headers from env', () => {
      process.env.OPENAPI_MCP_HEADERS = JSON.stringify({
        Authorization: 'Bearer token123',
        'X-Custom-Header': 'test',
      })

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {
            Authorization: 'Bearer token123',
            'X-Custom-Header': 'test',
          },
        }),
        expect.anything(),
      )
    })

    it('should return empty object when env var is not set', () => {
      delete process.env.OPENAPI_MCP_HEADERS

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {},
        }),
        expect.anything(),
      )
    })

    it('should return empty object and warn on invalid JSON', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      process.env.OPENAPI_MCP_HEADERS = 'invalid json'

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {},
        }),
        expect.anything(),
      )
      expect(consoleSpy).toHaveBeenCalledWith('Failed to parse OPENAPI_MCP_HEADERS environment variable:', expect.any(Error))
      consoleSpy.mockRestore()
    })

    it('should return empty object and warn on non-object JSON', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      process.env.OPENAPI_MCP_HEADERS = '"string"'

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {},
        }),
        expect.anything(),
      )
      expect(consoleSpy).toHaveBeenCalledWith('OPENAPI_MCP_HEADERS environment variable must be a JSON object, got:', 'string')
      consoleSpy.mockRestore()
    })

    it('should use NOTION_TOKEN when OPENAPI_MCP_HEADERS is not set', () => {
      delete process.env.OPENAPI_MCP_HEADERS
      process.env.NOTION_TOKEN = 'ntn_test_token_123'

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {
            'Authorization': 'Bearer ntn_test_token_123',
            'Notion-Version': '2025-09-03'
          },
        }),
        expect.anything(),
      )
    })

    it('should prioritize OPENAPI_MCP_HEADERS over NOTION_TOKEN when both are set', () => {
      process.env.OPENAPI_MCP_HEADERS = JSON.stringify({
        Authorization: 'Bearer custom_token',
        'Custom-Header': 'custom_value',
      })
      process.env.NOTION_TOKEN = 'ntn_test_token_123'

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {
            Authorization: 'Bearer custom_token',
            'Custom-Header': 'custom_value',
          },
        }),
        expect.anything(),
      )
    })

    it('should return empty object when neither OPENAPI_MCP_HEADERS nor NOTION_TOKEN are set', () => {
      delete process.env.OPENAPI_MCP_HEADERS
      delete process.env.NOTION_TOKEN

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {},
        }),
        expect.anything(),
      )
    })

    it('should use NOTION_TOKEN when OPENAPI_MCP_HEADERS is empty object', () => {
      process.env.OPENAPI_MCP_HEADERS = '{}'
      process.env.NOTION_TOKEN = 'ntn_test_token_123'

      const proxy = new MCPProxy('test-proxy', mockOpenApiSpec)
      expect(HttpClient).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: {
            'Authorization': 'Bearer ntn_test_token_123',
            'Notion-Version': '2025-09-03'
          },
        }),
        expect.anything(),
      )
    })
  })
  describe('connect', () => {
    it('should connect to transport', async () => {
      const mockTransport = {} as Transport
      await proxy.connect(mockTransport)

      const server = (proxy as any).server
      expect(server.connect).toHaveBeenCalledWith(mockTransport)
    })
  })

  describe('double-serialization fix (issue #176)', () => {
    it('should deserialize stringified JSON object parameters', async () => {
      // Mock HttpClient response
      const mockResponse = {
        data: { message: 'success' },
        status: 200,
        headers: new Headers({
          'content-type': 'application/json',
        }),
      }
      ;(HttpClient.prototype.executeOperation as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse)

      // Set up the openApiLookup with our test operation
      ;(proxy as any).openApiLookup = {
        'API-updatePage': {
          operationId: 'updatePage',
          responses: { '200': { description: 'Success' } },
          method: 'patch',
          path: '/pages/{page_id}',
        },
      }

      const server = (proxy as any).server
      const handlers = server.setRequestHandler.mock.calls.flatMap((x: unknown[]) => x).filter((x: unknown) => typeof x === 'function')
      const callToolHandler = handlers[1]

      // Simulate double-serialized parameters (the bug from issue #176)
      const stringifiedData = JSON.stringify({
        page_id: 'test-page-id',
        command: 'update_properties',
        properties: { Status: 'Done' },
      })

      await callToolHandler({
        params: {
          name: 'API-updatePage',
          arguments: {
            data: stringifiedData, // This would normally fail with "Expected object, received string"
          },
        },
      })

      // Verify that the parameters were deserialized before being passed to executeOperation
      expect(HttpClient.prototype.executeOperation).toHaveBeenCalledWith(
        expect.anything(),
        {
          data: {
            page_id: 'test-page-id',
            command: 'update_properties',
            properties: { Status: 'Done' },
          },
        },
      )
    })

    it('should handle nested stringified JSON parameters', async () => {
      const mockResponse = {
        data: { success: true },
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
      }
      ;(HttpClient.prototype.executeOperation as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse)

      ;(proxy as any).openApiLookup = {
        'API-createPage': {
          operationId: 'createPage',
          responses: { '200': { description: 'Success' } },
          method: 'post',
          path: '/pages',
        },
      }

      const server = (proxy as any).server
      const handlers = server.setRequestHandler.mock.calls.flatMap((x: unknown[]) => x).filter((x: unknown) => typeof x === 'function')
      const callToolHandler = handlers[1]

      // Nested stringified object
      const nestedData = JSON.stringify({
        parent: JSON.stringify({ page_id: 'parent-page-id' }),
      })

      await callToolHandler({
        params: {
          name: 'API-createPage',
          arguments: {
            data: nestedData,
          },
        },
      })

      // Verify nested objects were also deserialized
      expect(HttpClient.prototype.executeOperation).toHaveBeenCalledWith(
        expect.anything(),
        {
          data: {
            parent: { page_id: 'parent-page-id' },
          },
        },
      )
    })

    it('should preserve non-JSON string parameters', async () => {
      const mockResponse = {
        data: { success: true },
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
      }
      ;(HttpClient.prototype.executeOperation as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse)

      ;(proxy as any).openApiLookup = {
        'API-search': {
          operationId: 'search',
          responses: { '200': { description: 'Success' } },
          method: 'post',
          path: '/search',
        },
      }

      const server = (proxy as any).server
      const handlers = server.setRequestHandler.mock.calls.flatMap((x: unknown[]) => x).filter((x: unknown) => typeof x === 'function')
      const callToolHandler = handlers[1]

      await callToolHandler({
        params: {
          name: 'API-search',
          arguments: {
            query: 'hello world', // Regular string, should NOT be parsed
            filter: '{ not valid json }', // Looks like JSON but isn't valid
          },
        },
      })

      // Verify that non-JSON strings are preserved as-is
      expect(HttpClient.prototype.executeOperation).toHaveBeenCalledWith(
        expect.anything(),
        {
          query: 'hello world',
          filter: '{ not valid json }',
        },
      )
    })
  })
})
