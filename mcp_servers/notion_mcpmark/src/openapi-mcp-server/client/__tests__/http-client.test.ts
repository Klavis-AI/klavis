import { HttpClient, HttpClientError } from '../http-client'
import { OpenAPIV3 } from 'openapi-types'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import OpenAPIClientAxios from 'openapi-client-axios'

// Mock the OpenAPIClientAxios initialization
vi.mock('openapi-client-axios', () => {
  const mockApi = {
    getPet: vi.fn(),
    testOperation: vi.fn(),
    complexOperation: vi.fn(),
  }
  return {
    default: vi.fn().mockImplementation(() => ({
      init: vi.fn().mockResolvedValue(mockApi),
    })),
  }
})

describe('HttpClient', () => {
  let client: HttpClient
  let mockApi: any

  const sampleSpec: OpenAPIV3.Document = {
    openapi: '3.0.0',
    info: { title: 'Test API', version: '1.0.0' },
    paths: {
      '/pets/{petId}': {
        get: {
          operationId: 'getPet',
          parameters: [
            {
              name: 'petId',
              in: 'path',
              required: true,
              schema: { type: 'integer' },
            },
          ],
          responses: {
            '200': {
              description: 'OK',
              content: {
                'application/json': {
                  schema: { type: 'object' },
                },
              },
            },
          },
        },
      },
    },
  }

  const getPetOperation = sampleSpec.paths['/pets/{petId}']?.get as OpenAPIV3.OperationObject & { method: string; path: string }
  if (!getPetOperation) {
    throw new Error('Test setup error: getPet operation not found in sample spec')
  }

  beforeEach(async () => {
    // Create a new instance of HttpClient
    client = new HttpClient({ baseUrl: 'https://api.example.com' }, sampleSpec)
    // Await the initialization to ensure mockApi is set correctly
    mockApi = await client['api']
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('successfully executes an operation', async () => {
    const mockResponse = {
      data: { id: 1, name: 'Fluffy' },
      status: 200,
      headers: {
        'content-type': 'application/json',
      },
    }

    mockApi.getPet.mockResolvedValueOnce(mockResponse)

    const response = await client.executeOperation(getPetOperation, { petId: 1 })

    // Note GET requests should have a null Content-Type header!
    expect(mockApi.getPet).toHaveBeenCalledWith({ petId: 1 }, undefined, { headers: { 'Content-Type': null } })
    expect(response.data).toEqual(mockResponse.data)
    expect(response.status).toBe(200)
    expect(response.headers).toBeInstanceOf(Headers)
    expect(response.headers.get('content-type')).toBe('application/json')
  })

  it('throws error when operation ID is missing', async () => {
    const operationWithoutId: OpenAPIV3.OperationObject & { method: string; path: string } = {
      method: 'GET',
      path: '/unknown',
      responses: {
        '200': {
          description: 'OK',
        },
      },
    }

    await expect(client.executeOperation(operationWithoutId)).rejects.toThrow('Operation ID is required')
  })

  it('throws error when operation is not found', async () => {
    const operation: OpenAPIV3.OperationObject & { method: string; path: string } = {
      method: 'GET',
      path: '/unknown',
      operationId: 'nonexistentOperation',
      responses: {
        '200': {
          description: 'OK',
        },
      },
    }

    await expect(client.executeOperation(operation)).rejects.toThrow('Operation nonexistentOperation not found')
  })

  it('handles API errors correctly', async () => {
    const error = {
      response: {
        status: 404,
        statusText: 'Not Found',
        data: {
          code: 'RESOURCE_NOT_FOUND',
          message: 'Pet not found',
          petId: 999,
        },
        headers: {
          'content-type': 'application/json',
        },
      },
    }
    mockApi.getPet.mockRejectedValueOnce(error)

    await expect(client.executeOperation(getPetOperation, { petId: 999 })).rejects.toMatchObject({
      status: 404,
      message: '404 Not Found',
      data: {
        code: 'RESOURCE_NOT_FOUND',
        message: 'Pet not found',
        petId: 999,
      },
    })
  })

  it('handles validation errors (400) correctly', async () => {
    const error = {
      response: {
        status: 400,
        statusText: 'Bad Request',
        data: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input data',
          errors: [
            {
              field: 'age',
              message: 'Age must be a positive number',
            },
            {
              field: 'name',
              message: 'Name is required',
            },
          ],
        },
        headers: {
          'content-type': 'application/json',
        },
      },
    }
    mockApi.getPet.mockRejectedValueOnce(error)

    await expect(client.executeOperation(getPetOperation, { petId: 1 })).rejects.toMatchObject({
      status: 400,
      message: '400 Bad Request',
      data: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input data',
        errors: [
          {
            field: 'age',
            message: 'Age must be a positive number',
          },
          {
            field: 'name',
            message: 'Name is required',
          },
        ],
      },
    })
  })

  it('handles server errors (500) with HTML response', async () => {
    const error = {
      response: {
        status: 500,
        statusText: 'Internal Server Error',
        data: '<html><body><h1>500 Internal Server Error</h1></body></html>',
        headers: {
          'content-type': 'text/html',
        },
      },
    }
    mockApi.getPet.mockRejectedValueOnce(error)

    await expect(client.executeOperation(getPetOperation, { petId: 1 })).rejects.toMatchObject({
      status: 500,
      message: '500 Internal Server Error',
      data: '<html><body><h1>500 Internal Server Error</h1></body></html>',
    })
  })

  it('handles rate limit errors (429)', async () => {
    const error = {
      response: {
        status: 429,
        statusText: 'Too Many Requests',
        data: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Rate limit exceeded',
          retryAfter: 60,
        },
        headers: {
          'content-type': 'application/json',
          'retry-after': '60',
        },
      },
    }
    mockApi.getPet.mockRejectedValueOnce(error)

    await expect(client.executeOperation(getPetOperation, { petId: 1 })).rejects.toMatchObject({
      status: 429,
      message: '429 Too Many Requests',
      data: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Rate limit exceeded',
        retryAfter: 60,
      },
    })
  })

  it('should send body parameters in request body for POST operations', async () => {
    // Setup mock API with the new operation
    mockApi.testOperation = vi.fn().mockResolvedValue({
      data: {},
      status: 200,
      headers: {},
    })

    const testSpec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/test': {
          post: {
            operationId: 'testOperation',
            requestBody: {
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      foo: { type: 'string' },
                    },
                  },
                },
              },
            },
            responses: {
              '200': {
                description: 'Success response',
                content: {
                  'application/json': {
                    schema: {
                      type: 'object',
                    },
                  },
                },
              },
            },
          },
        },
      },
    }

    const postOperation = testSpec.paths['/test']?.post as OpenAPIV3.OperationObject & { method: string; path: string }
    if (!postOperation) {
      throw new Error('Test setup error: post operation not found')
    }

    const client = new HttpClient({ baseUrl: 'http://test.com' }, testSpec)

    await client.executeOperation(postOperation, { foo: 'bar' })

    expect(mockApi.testOperation).toHaveBeenCalledWith({}, { foo: 'bar' }, { headers: { 'Content-Type': 'application/json' } })
  })

  it('should handle query, path, and body parameters correctly', async () => {
    mockApi.complexOperation = vi.fn().mockResolvedValue({
      data: { success: true },
      status: 200,
      headers: {
        'content-type': 'application/json',
      },
    })

    const complexSpec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/users/{userId}/posts': {
          post: {
            operationId: 'complexOperation',
            parameters: [
              {
                name: 'userId',
                in: 'path',
                required: true,
                schema: { type: 'integer' },
              },
              {
                name: 'include',
                in: 'query',
                required: false,
                schema: { type: 'string' },
              },
            ],
            requestBody: {
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      title: { type: 'string' },
                      content: { type: 'string' },
                    },
                  },
                },
              },
            },
            responses: {
              '200': {
                description: 'Success response',
                content: {
                  'application/json': {
                    schema: {
                      type: 'object',
                      properties: {
                        success: { type: 'boolean' },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    }

    const complexOperation = complexSpec.paths['/users/{userId}/posts']?.post as OpenAPIV3.OperationObject & {
      method: string
      path: string
    }
    if (!complexOperation) {
      throw new Error('Test setup error: complex operation not found')
    }

    const client = new HttpClient({ baseUrl: 'http://test.com' }, complexSpec)

    await client.executeOperation(complexOperation, {
      // Path parameter
      userId: 123,
      // Query parameter
      include: 'comments',
      // Body parameters
      title: 'Test Post',
      content: 'Test Content',
    })

    expect(mockApi.complexOperation).toHaveBeenCalledWith(
      {
        userId: 123,
        include: 'comments',
      },
      {
        title: 'Test Post',
        content: 'Test Content',
      },
      { headers: { 'Content-Type': 'application/json' } },
    )
  })

  const mockOpenApiSpec: OpenAPIV3.Document = {
    openapi: '3.0.0',
    info: { title: 'Test API', version: '1.0.0' },
    paths: {
      '/test': {
        post: {
          operationId: 'testOperation',
          parameters: [
            {
              name: 'queryParam',
              in: 'query',
              schema: { type: 'string' },
            },
            {
              name: 'pathParam',
              in: 'path',
              schema: { type: 'string' },
            },
          ],
          requestBody: {
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    bodyParam: { type: 'string' },
                  },
                },
              },
            },
          },
          responses: {
            '200': {
              description: 'Success',
            },
            '400': {
              description: 'Bad Request',
            },
          },
        },
      },
    },
  }

  const mockConfig = {
    baseUrl: 'http://test-api.com',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should properly propagate structured error responses', async () => {
    const errorResponse = {
      response: {
        data: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input',
          details: ['Field x is required'],
        },
        status: 400,
        statusText: 'Bad Request',
        headers: {
          'content-type': 'application/json',
        },
      },
    }

    // Mock axios instance
    const mockAxiosInstance = {
      testOperation: vi.fn().mockRejectedValue(errorResponse),
    }

    // Mock the OpenAPIClientAxios initialization
    const MockOpenAPIClientAxios = vi.fn().mockImplementation(() => ({
      init: () => Promise.resolve(mockAxiosInstance),
    }))

    vi.mocked(OpenAPIClientAxios).mockImplementation(() => MockOpenAPIClientAxios())

    const client = new HttpClient(mockConfig, mockOpenApiSpec)
    const operation = mockOpenApiSpec.paths['/test']?.post
    if (!operation) {
      throw new Error('Operation not found in mock spec')
    }

    try {
      await client.executeOperation(operation as OpenAPIV3.OperationObject & { method: string; path: string }, {})
      // Should not reach here
      expect(true).toBe(false)
    } catch (error: any) {
      expect(error.status).toBe(400)
      expect(error.data).toEqual({
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
        details: ['Field x is required'],
      })
      expect(error.message).toBe('400 Bad Request')
    }
  })

  it('should handle query, path, and body parameters correctly', async () => {
    const mockAxiosInstance = {
      testOperation: vi.fn().mockResolvedValue({
        data: { success: true },
        status: 200,
        headers: { 'content-type': 'application/json' },
      }),
    }

    const MockOpenAPIClientAxios = vi.fn().mockImplementation(() => ({
      init: () => Promise.resolve(mockAxiosInstance),
    }))

    vi.mocked(OpenAPIClientAxios).mockImplementation(() => MockOpenAPIClientAxios())

    const client = new HttpClient(mockConfig, mockOpenApiSpec)
    const operation = mockOpenApiSpec.paths['/test']?.post
    if (!operation) {
      throw new Error('Operation not found in mock spec')
    }

    const response = await client.executeOperation(operation as OpenAPIV3.OperationObject & { method: string; path: string }, {
      queryParam: 'query1',
      pathParam: 'path1',
      bodyParam: 'body1',
    })

    expect(mockAxiosInstance.testOperation).toHaveBeenCalledWith(
      {
        queryParam: 'query1',
        pathParam: 'path1',
      },
      {
        bodyParam: 'body1',
      },
      { headers: { 'Content-Type': 'application/json' } },
    )

    // Additional check to ensure headers are correctly processed
    expect(response.headers.get('content-type')).toBe('application/json')
  })
})
