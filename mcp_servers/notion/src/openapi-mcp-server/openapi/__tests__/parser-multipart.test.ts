import { OpenAPIV3 } from 'openapi-types'
import { describe, it, expect } from 'vitest'
import { OpenAPIToMCPConverter } from '../parser.js'

describe('OpenAPI Multipart Form Parser', () => {
  it('converts single file upload endpoint to tool', () => {
    const spec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/pets/{id}/photo': {
          post: {
            operationId: 'uploadPetPhoto',
            summary: 'Upload a photo for a pet',
            parameters: [
              {
                name: 'id',
                in: 'path',
                required: true,
                schema: { type: 'integer' },
              },
            ],
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: {
                    type: 'object',
                    required: ['photo'],
                    properties: {
                      photo: {
                        type: 'string',
                        format: 'binary',
                        description: 'The photo to upload',
                      },
                      caption: {
                        type: 'string',
                        description: 'Optional caption for the photo',
                      },
                    },
                  },
                },
              },
            },
            responses: {
              '201': {
                description: 'Photo uploaded successfully',
              },
            },
          },
        },
      },
    }

    const converter = new OpenAPIToMCPConverter(spec)
    const { tools } = converter.convertToMCPTools()
    expect(Object.keys(tools)).toHaveLength(1)

    const [tool] = Object.values(tools)
    expect(tool.methods).toHaveLength(1)
    const [method] = tool.methods
    expect(method.name).toBe('uploadPetPhoto')
    expect(method.description).toContain('Upload a photo for a pet')

    // Check parameters
    expect(method.inputSchema.properties).toEqual({
      id: {
        type: 'integer',
      },
      photo: {
        type: 'string',
        format: 'uri-reference',
        description: expect.stringContaining('The photo to upload (absolute paths to local files)'),
      },
      caption: {
        type: 'string',
        description: expect.stringContaining('Optional caption'),
      },
    })

    expect(method.inputSchema.required).toContain('id')
    expect(method.inputSchema.required).toContain('photo')
    expect(method.inputSchema.required).not.toContain('caption')
  })

  it('converts multiple file upload endpoint to tool', () => {
    const spec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/pets/{id}/documents': {
          post: {
            operationId: 'uploadPetDocuments',
            summary: 'Upload multiple documents for a pet',
            parameters: [
              {
                name: 'id',
                in: 'path',
                required: true,
                schema: { type: 'integer' },
              },
            ],
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: {
                    type: 'object',
                    required: ['documents'],
                    properties: {
                      documents: {
                        type: 'array',
                        items: {
                          type: 'string',
                          format: 'binary',
                        },
                        description: 'The documents to upload (max 5 files)',
                      },
                      tags: {
                        type: 'array',
                        items: {
                          type: 'string',
                        },
                        description: 'Optional tags for the documents',
                      },
                    },
                  },
                },
              },
            },
            responses: {
              '201': {
                description: 'Documents uploaded successfully',
              },
            },
          },
        },
      },
    }

    const converter = new OpenAPIToMCPConverter(spec)
    const { tools } = converter.convertToMCPTools()
    expect(Object.keys(tools)).toHaveLength(1)

    const [tool] = Object.values(tools)
    expect(tool.methods).toHaveLength(1)
    const [method] = tool.methods
    expect(method.name).toBe('uploadPetDocuments')
    expect(method.description).toContain('Upload multiple documents')

    // Check parameters
    expect(method.inputSchema.properties).toEqual({
      id: {
        type: 'integer',
      },
      documents: {
        type: 'array',
        items: {
          type: 'string',
          format: 'uri-reference',
          description: 'absolute paths to local files',
        },
        description: expect.stringContaining('max 5 files'),
      },
      tags: {
        type: 'array',
        items: {
          type: 'string',
        },
        description: expect.stringContaining('Optional tags'),
      },
    })

    expect(method.inputSchema.required).toContain('id')
    expect(method.inputSchema.required).toContain('documents')
    expect(method.inputSchema.required).not.toContain('tags')
  })

  it('handles complex multipart forms with mixed content', () => {
    const spec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/pets/{id}/profile': {
          post: {
            operationId: 'updatePetProfile',
            summary: 'Update pet profile with images and data',
            parameters: [
              {
                name: 'id',
                in: 'path',
                required: true,
                schema: { type: 'integer' },
              },
            ],
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: {
                    type: 'object',
                    required: ['avatar', 'details'],
                    properties: {
                      avatar: {
                        type: 'string',
                        format: 'binary',
                        description: 'Profile picture',
                      },
                      gallery: {
                        type: 'array',
                        items: {
                          type: 'string',
                          format: 'binary',
                        },
                        description: 'Additional pet photos',
                      },
                      details: {
                        type: 'object',
                        properties: {
                          name: { type: 'string' },
                          age: { type: 'integer' },
                          breed: { type: 'string' },
                        },
                      },
                      preferences: {
                        type: 'array',
                        items: {
                          type: 'object',
                          properties: {
                            category: { type: 'string' },
                            value: { type: 'string' },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
            responses: {
              '200': {
                description: 'Profile updated successfully',
              },
            },
          },
        },
      },
    }

    const converter = new OpenAPIToMCPConverter(spec)
    const { tools } = converter.convertToMCPTools()
    expect(Object.keys(tools)).toHaveLength(1)

    const [tool] = Object.values(tools)
    expect(tool.methods).toHaveLength(1)
    const [method] = tool.methods
    expect(method.name).toBe('updatePetProfile')
    expect(method.description).toContain('Update pet profile')

    // Check parameters
    expect(method.inputSchema.properties).toEqual({
      id: {
        type: 'integer',
      },
      avatar: {
        type: 'string',
        format: 'uri-reference',
        description: expect.stringContaining('Profile picture (absolute paths to local files)'),
      },
      gallery: {
        type: 'array',
        items: {
          type: 'string',
          format: 'uri-reference',
          description: 'absolute paths to local files',
        },
        description: expect.stringContaining('Additional pet photos'),
      },
      details: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          age: { type: 'integer' },
          breed: { type: 'string' },
        },
        additionalProperties: true,
      },
      preferences: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            category: { type: 'string' },
            value: { type: 'string' },
          },
          additionalProperties: true,
        },
      },
    })

    expect(method.inputSchema.required).toContain('id')
    expect(method.inputSchema.required).toContain('avatar')
    expect(method.inputSchema.required).toContain('details')
    expect(method.inputSchema.required).not.toContain('gallery')
    expect(method.inputSchema.required).not.toContain('preferences')
  })

  it('handles optional file uploads in multipart forms', () => {
    const spec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/pets/{id}/metadata': {
          post: {
            operationId: 'updatePetMetadata',
            summary: 'Update pet metadata with optional attachments',
            parameters: [
              {
                name: 'id',
                in: 'path',
                required: true,
                schema: { type: 'integer' },
              },
            ],
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: {
                    type: 'object',
                    required: ['metadata'],
                    properties: {
                      metadata: {
                        type: 'object',
                        required: ['name'],
                        properties: {
                          name: { type: 'string' },
                          description: { type: 'string' },
                        },
                      },
                      certificate: {
                        type: 'string',
                        format: 'binary',
                        description: 'Optional pet certificate',
                      },
                      vaccinations: {
                        type: 'array',
                        items: {
                          type: 'string',
                          format: 'binary',
                        },
                        description: 'Optional vaccination records',
                      },
                    },
                  },
                },
              },
            },
            responses: {
              '200': {
                description: 'Metadata updated successfully',
              },
            },
          },
        },
      },
    }

    const converter = new OpenAPIToMCPConverter(spec)
    const { tools } = converter.convertToMCPTools()
    const [tool] = Object.values(tools)
    const [method] = tool.methods

    expect(method.name).toBe('updatePetMetadata')
    expect(method.inputSchema.required).toContain('id')
    expect(method.inputSchema.required).toContain('metadata')
    expect(method.inputSchema.required).not.toContain('certificate')
    expect(method.inputSchema.required).not.toContain('vaccinations')

    expect(method.inputSchema.properties).toEqual({
      id: {
        type: 'integer',
      },
      metadata: {
        type: 'object',
        required: ['name'],
        properties: {
          name: { type: 'string' },
          description: { type: 'string' },
        },
        additionalProperties: true,
      },
      certificate: {
        type: 'string',
        format: 'uri-reference',
        description: expect.stringContaining('Optional pet certificate (absolute paths to local files)'),
      },
      vaccinations: {
        type: 'array',
        items: {
          type: 'string',
          format: 'uri-reference',
          description: 'absolute paths to local files',
        },
        description: expect.stringContaining('Optional vaccination records'),
      },
    })
  })

  it('handles nested objects with file arrays in multipart forms', () => {
    const spec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/pets/{id}/medical-records': {
          post: {
            operationId: 'addMedicalRecord',
            summary: 'Add medical record with attachments',
            parameters: [
              {
                name: 'id',
                in: 'path',
                required: true,
                schema: { type: 'integer' },
              },
            ],
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: {
                    type: 'object',
                    required: ['record'],
                    properties: {
                      record: {
                        type: 'object',
                        required: ['date', 'type'],
                        properties: {
                          date: { type: 'string', format: 'date' },
                          type: { type: 'string' },
                          notes: { type: 'string' },
                          attachments: {
                            type: 'array',
                            items: {
                              type: 'object',
                              required: ['file', 'type'],
                              properties: {
                                file: {
                                  type: 'string',
                                  format: 'binary',
                                },
                                type: {
                                  type: 'string',
                                  enum: ['xray', 'lab', 'prescription'],
                                },
                                description: { type: 'string' },
                              },
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
            responses: {
              '201': {
                description: 'Medical record added successfully',
              },
            },
          },
        },
      },
    }

    const converter = new OpenAPIToMCPConverter(spec)
    const { tools } = converter.convertToMCPTools()
    const [tool] = Object.values(tools)
    const [method] = tool.methods

    expect(method.name).toBe('addMedicalRecord')
    expect(method.inputSchema.required).toContain('id')
    expect(method.inputSchema.required).toContain('record')

    // Verify nested structure is preserved
    const recordSchema = method.inputSchema.properties!.record as any
    expect(recordSchema.type).toBe('object')
    expect(recordSchema.required).toContain('date')
    expect(recordSchema.required).toContain('type')

    // Verify nested file array structure
    const attachmentsSchema = recordSchema.properties.attachments
    expect(attachmentsSchema.type).toBe('array')
    expect(attachmentsSchema.items.type).toBe('object')
    expect(attachmentsSchema.items.properties.file.format).toBe('uri-reference')
    expect(attachmentsSchema.items.properties.file.description).toBe('absolute paths to local files')
    expect(attachmentsSchema.items.required).toContain('file')
    expect(attachmentsSchema.items.required).toContain('type')
  })

  it('handles oneOf/anyOf schemas with file uploads', () => {
    const spec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {
        '/pets/{id}/content': {
          post: {
            operationId: 'addPetContent',
            summary: 'Add pet content (photo or document)',
            parameters: [
              {
                name: 'id',
                in: 'path',
                required: true,
                schema: { type: 'integer' },
              },
            ],
            requestBody: {
              required: true,
              content: {
                'multipart/form-data': {
                  schema: {
                    type: 'object',
                    required: ['content'],
                    properties: {
                      content: {
                        oneOf: [
                          {
                            type: 'object',
                            required: ['photo', 'isProfile'],
                            properties: {
                              photo: {
                                type: 'string',
                                format: 'binary',
                              },
                              isProfile: {
                                type: 'boolean',
                              },
                            },
                          },
                          {
                            type: 'object',
                            required: ['document', 'category'],
                            properties: {
                              document: {
                                type: 'string',
                                format: 'binary',
                              },
                              category: {
                                type: 'string',
                                enum: ['medical', 'training', 'adoption'],
                              },
                            },
                          },
                        ],
                      },
                    },
                  },
                },
              },
            },
            responses: {
              '201': {
                description: 'Content added successfully',
              },
            },
          },
        },
      },
    }

    const converter = new OpenAPIToMCPConverter(spec)
    const { tools } = converter.convertToMCPTools()
    const [tool] = Object.values(tools)
    const [method] = tool.methods

    expect(method.name).toBe('addPetContent')
    expect(method.inputSchema.required).toContain('id')
    expect(method.inputSchema.required).toContain('content')

    // Verify oneOf structure is preserved
    const contentSchema = method.inputSchema.properties!.content as any
    expect(contentSchema.oneOf).toHaveLength(2)

    // Check photo option
    const photoOption = contentSchema.oneOf[0]
    expect(photoOption.type).toBe('object')
    expect(photoOption.properties.photo.format).toBe('uri-reference')
    expect(photoOption.properties.photo.description).toBe('absolute paths to local files')
    expect(photoOption.required).toContain('photo')
    expect(photoOption.required).toContain('isProfile')

    // Check document option
    const documentOption = contentSchema.oneOf[1]
    expect(documentOption.type).toBe('object')
    expect(documentOption.properties.document.format).toBe('uri-reference')
    expect(documentOption.properties.document.description).toBe('absolute paths to local files')
    expect(documentOption.required).toContain('document')
    expect(documentOption.required).toContain('category')
  })
})
