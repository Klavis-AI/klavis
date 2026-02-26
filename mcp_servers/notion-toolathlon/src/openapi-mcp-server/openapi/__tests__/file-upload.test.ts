import { OpenAPIV3 } from 'openapi-types'
import { describe, it, expect } from 'vitest'
import { isFileUploadParameter } from '../file-upload.js'

describe('File Upload Detection', () => {
  it('identifies file upload parameters in request bodies', () => {
    const operation: OpenAPIV3.OperationObject = {
      operationId: 'uploadFile',
      responses: {
        '200': {
          description: 'File uploaded successfully',
        },
      },
      requestBody: {
        content: {
          'multipart/form-data': {
            schema: {
              type: 'object',
              properties: {
                file: {
                  type: 'string',
                  format: 'binary',
                },
                additionalInfo: {
                  type: 'string',
                },
              },
            },
          },
        },
      },
    }

    const fileParams = isFileUploadParameter(operation)
    expect(fileParams).toEqual(['file'])
  })

  it('returns empty array for non-file upload operations', () => {
    const operation: OpenAPIV3.OperationObject = {
      operationId: 'createUser',
      responses: {
        '200': {
          description: 'User created successfully',
        },
      },
      requestBody: {
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                name: {
                  type: 'string',
                },
              },
            },
          },
        },
      },
    }

    const fileParams = isFileUploadParameter(operation)
    expect(fileParams).toEqual([])
  })

  it('identifies array-based file upload parameters', () => {
    const operation: OpenAPIV3.OperationObject = {
      operationId: 'uploadFiles',
      responses: {
        '200': {
          description: 'Files uploaded successfully',
        },
      },
      requestBody: {
        content: {
          'multipart/form-data': {
            schema: {
              type: 'object',
              properties: {
                files: {
                  type: 'array',
                  items: {
                    type: 'string',
                    format: 'binary',
                  },
                },
                description: {
                  type: 'string',
                },
              },
            },
          },
        },
      },
    }

    const fileParams = isFileUploadParameter(operation)
    expect(fileParams).toEqual(['files'])
  })
})
