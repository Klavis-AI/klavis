import { OpenAPIToMCPConverter } from '../parser.js'
import { OpenAPIV3 } from 'openapi-types'
import { describe, expect, it } from 'vitest'
import { JSONSchema7 as IJsonSchema } from 'json-schema'

interface ToolMethod {
  name: string
  description: string
  inputSchema: any
  returnSchema?: any
}

interface Tool {
  methods: ToolMethod[]
}

interface Tools {
  [key: string]: Tool
}

// Helper function to verify tool method structure without checking the exact Zod schema
function verifyToolMethod(actual: ToolMethod, expected: any, toolName: string) {
  expect(actual.name).toBe(expected.name)
  expect(actual.description).toBe(expected.description)
  expect(actual.inputSchema, `inputSchema ${actual.name} ${toolName}`).toEqual(expected.inputSchema)
  if (expected.returnSchema) {
    expect(actual.returnSchema, `returnSchema ${actual.name} ${toolName}`).toEqual(expected.returnSchema)
  }
}

// Helper function to verify tools structure
function verifyTools(actual: Tools, expected: any) {
  expect(Object.keys(actual)).toEqual(Object.keys(expected))
  for (const [key, value] of Object.entries(actual)) {
    expect(value.methods.length).toBe(expected[key].methods.length)
    value.methods.forEach((method: ToolMethod, index: number) => {
      verifyToolMethod(method, expected[key].methods[index], key)
    })
  }
}

// A helper function to derive a type from a possibly complex schema.
// If no explicit type is found, we assume 'object' for testing purposes.
function getTypeFromSchema(schema: IJsonSchema): string {
  if (schema.type) {
    return Array.isArray(schema.type) ? schema.type[0] : schema.type
  } else if (schema.$ref) {
    // If there's a $ref, we treat it as an object reference.
    return 'object'
  } else if (schema.oneOf || schema.anyOf || schema.allOf) {
    // Complex schema combos - assume object for these tests.
    return 'object'
  }
  return 'object'
}

// Updated helper function to get parameters from inputSchema
// Now handles $ref by treating it as an object reference without expecting properties.
function getParamsFromSchema(method: { inputSchema: IJsonSchema }) {
  return Object.entries(method.inputSchema.properties || {}).map(([name, prop]) => {
    if (typeof prop === 'boolean') {
      throw new Error(`Boolean schema not supported for parameter ${name}`)
    }

    // If there's a $ref, treat it as an object reference.
    const schemaType = getTypeFromSchema(prop)
    return {
      name,
      type: schemaType,
      description: prop.description,
      optional: !(method.inputSchema.required || []).includes(name),
    }
  })
}

// Updated helper function to get return type from returnSchema
// No longer requires that the schema be fully expanded. If we have a $ref, just note it as 'object'.
function getReturnType(method: { returnSchema?: IJsonSchema }) {
  if (!method.returnSchema) return null
  const schema = method.returnSchema
  return {
    type: getTypeFromSchema(schema),
    description: schema.description,
  }
}

describe('OpenAPIToMCPConverter', () => {
  describe('Simple API Conversion', () => {
    const sampleSpec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: {
        title: 'Test API',
        version: '1.0.0',
      },
      paths: {
        '/pets/{petId}': {
          get: {
            operationId: 'getPet',
            summary: 'Get a pet by ID',
            parameters: [
              {
                name: 'petId',
                in: 'path',
                required: true,
                description: 'The ID of the pet',
                schema: {
                  type: 'integer',
                },
              },
            ],
            responses: {
              '200': {
                description: 'Pet found',
                content: {
                  'application/json': {
                    schema: {
                      type: 'object',
                      properties: {
                        id: { type: 'integer' },
                        name: { type: 'string' },
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

    it('converts simple OpenAPI paths to MCP tools', () => {
      const converter = new OpenAPIToMCPConverter(sampleSpec)
      const { tools, openApiLookup } = converter.convertToMCPTools()

      expect(tools).toHaveProperty('API')
      expect(tools.API.methods).toHaveLength(1)
      expect(Object.keys(openApiLookup)).toHaveLength(1)

      const getPetMethod = tools.API.methods.find((m) => m.name === 'getPet')
      expect(getPetMethod).toBeDefined()

      const params = getParamsFromSchema(getPetMethod!)
      expect(params).toContainEqual({
        name: 'petId',
        type: 'integer',
        description: 'The ID of the pet',
        optional: false,
      })
    })

    it('truncates tool names exceeding 64 characters', () => {
      const longOperationId = 'a'.repeat(65)
      const specWithLongName: OpenAPIV3.Document = {
        openapi: '3.0.0',
        info: {
          title: 'Test API',
          version: '1.0.0'
        },
        paths: {
          '/pets/{petId}': {
            get: {
              operationId: longOperationId,
              summary: 'Get a pet by ID',
              parameters: [
                {
                  name: 'petId',
                  in: 'path',
                  required: true,
                  description: 'The ID of the pet',
                  schema: {
                    type: 'integer'
                  }
                }
              ],
              responses: {
                '200': {
                  description: 'Pet found',
                  content: {
                    'application/json': {
                      schema: {
                        type: 'object',
                        properties: {
                          id: { type: 'integer' },
                          name: { type: 'string' }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }

      const converter = new OpenAPIToMCPConverter(specWithLongName)
      const { tools } = converter.convertToMCPTools()

      const longNameMethod = tools.API.methods.find(m => m.name.startsWith('a'.repeat(59)))
      expect(longNameMethod).toBeDefined()
      expect(longNameMethod!.name.length).toBeLessThanOrEqual(64)
    })
  })

  describe('Complex API Conversion', () => {
    const complexSpec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Complex API', version: '1.0.0' },
      components: {
        schemas: {
          Error: {
            type: 'object',
            required: ['code', 'message'],
            properties: {
              code: { type: 'integer' },
              message: { type: 'string' },
            },
          },
          Pet: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer', description: 'The ID of the pet' },
              name: { type: 'string', description: 'The name of the pet' },
              category: { $ref: '#/components/schemas/Category', description: 'The category of the pet' },
              tags: {
                type: 'array',
                description: 'The tags of the pet',
                items: { $ref: '#/components/schemas/Tag' },
              },
              status: {
                type: 'string',
                description: 'The status of the pet',
                enum: ['available', 'pending', 'sold'],
              },
            },
          },
          Category: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
              subcategories: {
                type: 'array',
                items: { $ref: '#/components/schemas/Category' },
              },
            },
          },
          Tag: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
            },
          },
        },
        parameters: {
          PetId: {
            name: 'petId',
            in: 'path',
            required: true,
            description: 'ID of pet to fetch',
            schema: { type: 'integer' },
          },
          QueryLimit: {
            name: 'limit',
            in: 'query',
            description: 'Maximum number of results to return',
            schema: { type: 'integer', minimum: 1, maximum: 100, default: 20 },
          },
        },
        responses: {
          NotFound: {
            description: 'The specified resource was not found',
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/Error' },
              },
            },
          },
        },
      },
      paths: {
        '/pets': {
          get: {
            operationId: 'listPets',
            summary: 'List all pets',
            parameters: [{ $ref: '#/components/parameters/QueryLimit' }],
            responses: {
              '200': {
                description: 'A list of pets',
                content: {
                  'application/json': {
                    schema: {
                      type: 'array',
                      items: { $ref: '#/components/schemas/Pet' },
                    },
                  },
                },
              },
            },
          },
          post: {
            operationId: 'createPet',
            summary: 'Create a pet',
            requestBody: {
              required: true,
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Pet' },
                },
              },
            },
            responses: {
              '201': {
                description: 'Pet created',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/Pet' },
                  },
                },
              },
            },
          },
        },
        '/pets/{petId}': {
          get: {
            operationId: 'getPet',
            summary: 'Get a pet by ID',
            parameters: [{ $ref: '#/components/parameters/PetId' }],
            responses: {
              '200': {
                description: 'Pet found',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/Pet' },
                  },
                },
              },
              '404': {
                $ref: '#/components/responses/NotFound',
              },
            },
          },
          put: {
            operationId: 'updatePet',
            summary: 'Update a pet',
            parameters: [{ $ref: '#/components/parameters/PetId' }],
            requestBody: {
              required: true,
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Pet' },
                },
              },
            },
            responses: {
              '200': {
                description: 'Pet updated',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/Pet' },
                  },
                },
              },
              '404': {
                $ref: '#/components/responses/NotFound',
              },
            },
          },
        },
      },
    }

    it('converts operations with referenced parameters', () => {
      const converter = new OpenAPIToMCPConverter(complexSpec)
      const { tools } = converter.convertToMCPTools()

      const getPetMethod = tools.API.methods.find((m) => m.name === 'getPet')
      expect(getPetMethod).toBeDefined()
      const params = getParamsFromSchema(getPetMethod!)
      expect(params).toContainEqual({
        name: 'petId',
        type: 'integer',
        description: 'ID of pet to fetch',
        optional: false,
      })
    })

    it('converts operations with query parameters', () => {
      const converter = new OpenAPIToMCPConverter(complexSpec)
      const { tools } = converter.convertToMCPTools()

      const listPetsMethod = tools.API.methods.find((m) => m.name === 'listPets')
      expect(listPetsMethod).toBeDefined()

      const params = getParamsFromSchema(listPetsMethod!)
      expect(params).toContainEqual({
        name: 'limit',
        type: 'integer',
        description: 'Maximum number of results to return',
        optional: true,
      })
    })

    it('converts operations with array responses', () => {
      const converter = new OpenAPIToMCPConverter(complexSpec)
      const { tools } = converter.convertToMCPTools()

      const listPetsMethod = tools.API.methods.find((m) => m.name === 'listPets')
      expect(listPetsMethod).toBeDefined()

      const returnType = getReturnType(listPetsMethod!)
      // Now we only check type since description might not be carried through
      // if we are not expanding schemas.
      expect(returnType).toMatchObject({
        type: 'array',
      })
    })

    it('converts operations with request bodies using $ref', () => {
      const converter = new OpenAPIToMCPConverter(complexSpec)
      const { tools } = converter.convertToMCPTools()

      const createPetMethod = tools.API.methods.find((m) => m.name === 'createPet')
      expect(createPetMethod).toBeDefined()

      const params = getParamsFromSchema(createPetMethod!)
      // Now that we are preserving $ref, the request body won't be expanded into multiple parameters.
      // Instead, we'll have a single "body" parameter referencing Pet.
      expect(params).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'body',
            type: 'object', // Because it's a $ref
            optional: false,
          }),
        ]),
      )
    })

    it('converts operations with referenced error responses', () => {
      const converter = new OpenAPIToMCPConverter(complexSpec)
      const { tools } = converter.convertToMCPTools()

      const getPetMethod = tools.API.methods.find((m) => m.name === 'getPet')
      expect(getPetMethod).toBeDefined()

      // We just check that the description includes the error references now.
      expect(getPetMethod?.description).toContain('404: The specified resource was not found')
    })

    it('handles recursive schema references without expanding them', () => {
      const converter = new OpenAPIToMCPConverter(complexSpec)
      const { tools } = converter.convertToMCPTools()

      const createPetMethod = tools.API.methods.find((m) => m.name === 'createPet')
      expect(createPetMethod).toBeDefined()

      const params = getParamsFromSchema(createPetMethod!)
      // Since "category" would be inside Pet, and we're not expanding,
      // we won't see 'category' directly. We only have 'body' as a reference.
      // Thus, the test no longer checks for a direct 'category' param.
      expect(params.find((p) => p.name === 'body')).toBeDefined()
    })

    it('converts all operations correctly respecting $ref usage', () => {
      const converter = new OpenAPIToMCPConverter(complexSpec)
      const { tools } = converter.convertToMCPTools()

      expect(tools.API.methods).toHaveLength(4)

      const methodNames = tools.API.methods.map((m) => m.name)
      expect(methodNames).toEqual(expect.arrayContaining(['listPets', 'createPet', 'getPet', 'updatePet']))

      tools.API.methods.forEach((method) => {
        expect(method).toHaveProperty('name')
        expect(method).toHaveProperty('description')
        expect(method).toHaveProperty('inputSchema')
        expect(method).toHaveProperty('returnSchema')

        // For 'get' operations, we just check the return type is recognized correctly.
        if (method.name.startsWith('get')) {
          const returnType = getReturnType(method)
          // With $ref usage, we can't guarantee description or direct expansion.
          expect(returnType?.type).toBe('object')
        }
      })
    })
  })

  describe('Complex Schema Conversion', () => {
    // A similar approach for the nested spec
    // Just as in the previous tests, we no longer test for direct property expansion.
    // We only confirm that parameters and return types are recognized and that references are preserved.

    const nestedSpec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Nested API', version: '1.0.0' },
      components: {
        schemas: {
          Organization: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
              departments: {
                type: 'array',
                items: { $ref: '#/components/schemas/Department' },
              },
              metadata: { $ref: '#/components/schemas/Metadata' },
            },
          },
          Department: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
              employees: {
                type: 'array',
                items: { $ref: '#/components/schemas/Employee' },
              },
              subDepartments: {
                type: 'array',
                items: { $ref: '#/components/schemas/Department' },
              },
              metadata: { $ref: '#/components/schemas/Metadata' },
            },
          },
          Employee: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
              role: { $ref: '#/components/schemas/Role' },
              skills: {
                type: 'array',
                items: { $ref: '#/components/schemas/Skill' },
              },
              metadata: { $ref: '#/components/schemas/Metadata' },
            },
          },
          Role: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
              permissions: {
                type: 'array',
                items: { $ref: '#/components/schemas/Permission' },
              },
            },
          },
          Permission: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
              scope: { type: 'string' },
            },
          },
          Skill: {
            type: 'object',
            required: ['id', 'name'],
            properties: {
              id: { type: 'integer' },
              name: { type: 'string' },
              level: {
                type: 'string',
                enum: ['beginner', 'intermediate', 'expert'],
              },
            },
          },
          Metadata: {
            type: 'object',
            properties: {
              createdAt: { type: 'string', format: 'date-time' },
              updatedAt: { type: 'string', format: 'date-time' },
              tags: {
                type: 'array',
                items: { type: 'string' },
              },
              customFields: {
                type: 'object',
                additionalProperties: true,
              },
            },
          },
        },
        parameters: {
          OrgId: {
            name: 'orgId',
            in: 'path',
            required: true,
            description: 'Organization ID',
            schema: { type: 'integer' },
          },
          DeptId: {
            name: 'deptId',
            in: 'path',
            required: true,
            description: 'Department ID',
            schema: { type: 'integer' },
          },
          IncludeMetadata: {
            name: 'includeMetadata',
            in: 'query',
            description: 'Include metadata in response',
            schema: { type: 'boolean', default: false },
          },
          Depth: {
            name: 'depth',
            in: 'query',
            description: 'Depth of nested objects to return',
            schema: { type: 'integer', minimum: 1, maximum: 5, default: 1 },
          },
        },
      },
      paths: {
        '/organizations/{orgId}': {
          get: {
            operationId: 'getOrganization',
            summary: 'Get organization details',
            parameters: [
              { $ref: '#/components/parameters/OrgId' },
              { $ref: '#/components/parameters/IncludeMetadata' },
              { $ref: '#/components/parameters/Depth' },
            ],
            responses: {
              '200': {
                description: 'Organization details',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/Organization' },
                  },
                },
              },
            },
          },
        },
        '/organizations/{orgId}/departments/{deptId}': {
          get: {
            operationId: 'getDepartment',
            summary: 'Get department details',
            parameters: [
              { $ref: '#/components/parameters/OrgId' },
              { $ref: '#/components/parameters/DeptId' },
              { $ref: '#/components/parameters/IncludeMetadata' },
              { $ref: '#/components/parameters/Depth' },
            ],
            responses: {
              '200': {
                description: 'Department details',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/Department' },
                  },
                },
              },
            },
          },
          put: {
            operationId: 'updateDepartment',
            summary: 'Update department details',
            parameters: [{ $ref: '#/components/parameters/OrgId' }, { $ref: '#/components/parameters/DeptId' }],
            requestBody: {
              required: true,
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Department' },
                },
              },
            },
            responses: {
              '200': {
                description: 'Department updated',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/Department' },
                  },
                },
              },
            },
          },
        },
      },
    }

    it('handles deeply nested object references', () => {
      const converter = new OpenAPIToMCPConverter(nestedSpec)
      const { tools } = converter.convertToMCPTools()

      const getOrgMethod = tools.API.methods.find((m) => m.name === 'getOrganization')
      expect(getOrgMethod).toBeDefined()

      const params = getParamsFromSchema(getOrgMethod!)
      expect(params).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'orgId',
            type: 'integer',
            description: 'Organization ID',
            optional: false,
          }),
          expect.objectContaining({
            name: 'includeMetadata',
            type: 'boolean',
            description: 'Include metadata in response',
            optional: true,
          }),
          expect.objectContaining({
            name: 'depth',
            type: 'integer',
            description: 'Depth of nested objects to return',
            optional: true,
          }),
        ]),
      )
    })

    it('handles recursive array references without requiring expansion', () => {
      const converter = new OpenAPIToMCPConverter(nestedSpec)
      const { tools } = converter.convertToMCPTools()

      const updateDeptMethod = tools.API.methods.find((m) => m.name === 'updateDepartment')
      expect(updateDeptMethod).toBeDefined()

      const params = getParamsFromSchema(updateDeptMethod!)
      // With $ref usage, we have a body parameter referencing Department.
      // The subDepartments array is inside Department, so we won't see it expanded here.
      // Instead, we just confirm 'body' is present.
      const bodyParam = params.find((p) => p.name === 'body')
      expect(bodyParam).toBeDefined()
      expect(bodyParam?.type).toBe('object')
    })

    it('handles complex nested object hierarchies without expansion', () => {
      const converter = new OpenAPIToMCPConverter(nestedSpec)
      const { tools } = converter.convertToMCPTools()

      const getDeptMethod = tools.API.methods.find((m) => m.name === 'getDepartment')
      expect(getDeptMethod).toBeDefined()

      const params = getParamsFromSchema(getDeptMethod!)
      // Just checking top-level params:
      expect(params).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            name: 'orgId',
            type: 'integer',
            optional: false,
          }),
          expect.objectContaining({
            name: 'deptId',
            type: 'integer',
            optional: false,
          }),
          expect.objectContaining({
            name: 'includeMetadata',
            type: 'boolean',
            optional: true,
          }),
          expect.objectContaining({
            name: 'depth',
            type: 'integer',
            optional: true,
          }),
        ]),
      )
    })

    it('handles schema with mixed primitive and reference types without expansion', () => {
      const converter = new OpenAPIToMCPConverter(nestedSpec)
      const { tools } = converter.convertToMCPTools()

      const updateDeptMethod = tools.API.methods.find((m) => m.name === 'updateDepartment')
      expect(updateDeptMethod).toBeDefined()

      const params = getParamsFromSchema(updateDeptMethod!)
      // Since we are not expanding, we won't see metadata fields directly.
      // We just confirm 'body' referencing Department is there.
      expect(params.find((p) => p.name === 'body')).toBeDefined()
    })

    it('converts all operations with complex schemas correctly respecting $ref', () => {
      const converter = new OpenAPIToMCPConverter(nestedSpec)
      const { tools } = converter.convertToMCPTools()

      expect(tools.API.methods).toHaveLength(3)

      const methodNames = tools.API.methods.map((m) => m.name)
      expect(methodNames).toEqual(expect.arrayContaining(['getOrganization', 'getDepartment', 'updateDepartment']))

      tools.API.methods.forEach((method) => {
        expect(method).toHaveProperty('name')
        expect(method).toHaveProperty('description')
        expect(method).toHaveProperty('inputSchema')
        expect(method).toHaveProperty('returnSchema')

        // If it's a GET operation, check that return type is recognized.
        if (method.name.startsWith('get')) {
          const returnType = getReturnType(method)
          // Without expansion, just check type is recognized as object.
          expect(returnType).toMatchObject({
            type: 'object',
          })
        }
      })
    })
  })

  it('preserves description on $ref nodes', () => {
    const spec: OpenAPIV3.Document = {
      openapi: '3.0.0',
      info: { title: 'Test API', version: '1.0.0' },
      paths: {},
      components: {
        schemas: {
          TestSchema: {
            type: 'object',
            properties: {
              name: { type: 'string' },
            },
          },
        },
      },
    }

    const converter = new OpenAPIToMCPConverter(spec)
    const result = converter.convertOpenApiSchemaToJsonSchema(
      {
        $ref: '#/components/schemas/TestSchema',
        description: 'A schema description',
      },
      new Set(),
    )

    expect(result).toEqual({
      $ref: '#/$defs/TestSchema',
      description: 'A schema description',
    })
  })
})

// Additional complex test scenarios as a table test
describe('OpenAPIToMCPConverter - Additional Complex Tests', () => {
  interface TestCase {
    name: string
    input: OpenAPIV3.Document
    expected: {
      tools: Record<
        string,
        {
          methods: Array<{
            name: string
            description: string
            inputSchema: IJsonSchema & { type: 'object' }
            returnSchema?: IJsonSchema
          }>
        }
      >
      openApiLookup: Record<string, OpenAPIV3.OperationObject & { method: string; path: string }>
    }
  }

  const cases: TestCase[] = [
    {
      name: 'Cyclic References with Full Descriptions',
      input: {
        openapi: '3.0.0',
        info: {
          title: 'Cyclic Test API',
          version: '1.0.0',
        },
        paths: {
          '/ab': {
            get: {
              operationId: 'getAB',
              summary: 'Get an A-B object',
              responses: {
                '200': {
                  description: 'Returns an A object',
                  content: {
                    'application/json': {
                      schema: { $ref: '#/components/schemas/A' },
                    },
                  },
                },
              },
            },
            post: {
              operationId: 'createAB',
              summary: 'Create an A-B object',
              requestBody: {
                required: true,
                content: {
                  'application/json': {
                    schema: {
                      $ref: '#/components/schemas/A',
                      description: 'A schema description',
                    },
                  },
                },
              },
              responses: {
                '201': {
                  description: 'Created A object',
                  content: {
                    'application/json': {
                      schema: { $ref: '#/components/schemas/A' },
                    },
                  },
                },
              },
            },
          },
        },
        components: {
          schemas: {
            A: {
              type: 'object',
              description: 'A schema description',
              required: ['name', 'b'],
              properties: {
                name: {
                  type: 'string',
                  description: 'Name of A',
                },
                b: {
                  $ref: '#/components/schemas/B',
                  description: 'B property in A',
                },
              },
            },
            B: {
              type: 'object',
              description: 'B schema description',
              required: ['title', 'a'],
              properties: {
                title: {
                  type: 'string',
                  description: 'Title of B',
                },
                a: {
                  $ref: '#/components/schemas/A',
                  description: 'A property in B',
                },
              },
            },
          },
        },
      } as OpenAPIV3.Document,
      expected: {
        tools: {
          API: {
            methods: [
              {
                name: 'getAB',
                description: 'Get an A-B object',
                // Error responses might not be listed here since none are defined.
                // Just end the description with no Error Responses section.
                inputSchema: {
                  type: 'object',
                  properties: {},
                  required: [],
                  $defs: {
                    A: {
                      type: 'object',
                      description: 'A schema description',
                      additionalProperties: true,
                      properties: {
                        name: {
                          type: 'string',
                          description: 'Name of A',
                        },
                        b: {
                          description: 'B property in A',
                          $ref: '#/$defs/B',
                        },
                      },
                      required: ['name', 'b'],
                    },
                    B: {
                      type: 'object',
                      description: 'B schema description',
                      additionalProperties: true,
                      properties: {
                        title: {
                          type: 'string',
                          description: 'Title of B',
                        },
                        a: {
                          description: 'A property in B',
                          $ref: '#/$defs/A',
                        },
                      },
                      required: ['title', 'a'],
                    },
                  },
                },
                returnSchema: {
                  $ref: '#/$defs/A',
                  description: 'Returns an A object',
                  $defs: {
                    A: {
                      type: 'object',
                      description: 'A schema description',
                      additionalProperties: true,
                      properties: {
                        name: {
                          type: 'string',
                          description: 'Name of A',
                        },
                        b: {
                          description: 'B property in A',
                          $ref: '#/$defs/B',
                        },
                      },
                      required: ['name', 'b'],
                    },
                    B: {
                      type: 'object',
                      description: 'B schema description',
                      additionalProperties: true,
                      properties: {
                        title: {
                          type: 'string',
                          description: 'Title of B',
                        },
                        a: {
                          description: 'A property in B',
                          $ref: '#/$defs/A',
                        },
                      },
                      required: ['title', 'a'],
                    },
                  },
                },
              },
              {
                name: 'createAB',
                description: 'Create an A-B object',
                inputSchema: {
                  type: 'object',
                  properties: {
                    // The requestBody references A. We keep it as a single body field with a $ref.
                    body: {
                      $ref: '#/$defs/A',
                      description: 'A schema description',
                    },
                  },
                  required: ['body'],

                  $defs: {
                    A: {
                      type: 'object',
                      description: 'A schema description',
                      additionalProperties: true,
                      properties: {
                        name: {
                          type: 'string',
                          description: 'Name of A',
                        },
                        b: {
                          description: 'B property in A',
                          $ref: '#/$defs/B',
                        },
                      },
                      required: ['name', 'b'],
                    },
                    B: {
                      type: 'object',
                      description: 'B schema description',
                      additionalProperties: true,
                      properties: {
                        title: {
                          type: 'string',
                          description: 'Title of B',
                        },
                        a: {
                          description: 'A property in B',
                          $ref: '#/$defs/A',
                        },
                      },
                      required: ['title', 'a'],
                    },
                  },
                },
                returnSchema: {
                  $ref: '#/$defs/A',
                  description: 'Created A object',

                  $defs: {
                    A: {
                      type: 'object',
                      description: 'A schema description',
                      additionalProperties: true,
                      properties: {
                        name: {
                          type: 'string',
                          description: 'Name of A',
                        },
                        b: {
                          description: 'B property in A',
                          $ref: '#/$defs/B',
                        },
                      },
                      required: ['name', 'b'],
                    },
                    B: {
                      type: 'object',
                      description: 'B schema description',
                      additionalProperties: true,
                      properties: {
                        title: {
                          type: 'string',
                          description: 'Title of B',
                        },
                        a: {
                          description: 'A property in B',
                          $ref: '#/$defs/A',
                        },
                      },
                      required: ['title', 'a'],
                    },
                  },
                },
              },
            ],
          },
        },
        openApiLookup: {
          'API-getAB': {
            operationId: 'getAB',
            summary: 'Get an A-B object',
            responses: {
              '200': {
                description: 'Returns an A object',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/A' },
                  },
                },
              },
            },
            method: 'get',
            path: '/ab',
          },
          'API-createAB': {
            operationId: 'createAB',
            summary: 'Create an A-B object',
            requestBody: {
              required: true,
              content: {
                'application/json': {
                  schema: {
                    $ref: '#/components/schemas/A',
                    description: 'A schema description',
                  },
                },
              },
            },
            responses: {
              '201': {
                description: 'Created A object',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/A' },
                  },
                },
              },
            },
            method: 'post',
            path: '/ab',
          },
        },
      },
    },
    {
      name: 'allOf/oneOf References with Full Descriptions',
      input: {
        openapi: '3.0.0',
        info: { title: 'Composed Schema API', version: '1.0.0' },
        paths: {
          '/composed': {
            get: {
              operationId: 'getComposed',
              summary: 'Get a composed resource',
              responses: {
                '200': {
                  description: 'A composed object',
                  content: {
                    'application/json': {
                      schema: { $ref: '#/components/schemas/C' },
                    },
                  },
                },
              },
            },
          },
        },
        components: {
          schemas: {
            Base: {
              type: 'object',
              description: 'Base schema description',
              properties: {
                baseName: {
                  type: 'string',
                  description: 'Name in the base schema',
                },
              },
            },
            D: {
              type: 'object',
              description: 'D schema description',
              properties: {
                dProp: {
                  type: 'integer',
                  description: 'D property integer',
                },
              },
            },
            E: {
              type: 'object',
              description: 'E schema description',
              properties: {
                choice: {
                  description: 'One of these choices',
                  oneOf: [
                    {
                      $ref: '#/components/schemas/F',
                    },
                    {
                      $ref: '#/components/schemas/G',
                    },
                  ],
                },
              },
            },
            F: {
              type: 'object',
              description: 'F schema description',
              properties: {
                fVal: {
                  type: 'boolean',
                  description: 'Boolean in F',
                },
              },
            },
            G: {
              type: 'object',
              description: 'G schema description',
              properties: {
                gVal: {
                  type: 'string',
                  description: 'String in G',
                },
              },
            },
            C: {
              description: 'C schema description',
              allOf: [{ $ref: '#/components/schemas/Base' }, { $ref: '#/components/schemas/D' }, { $ref: '#/components/schemas/E' }],
            },
          },
        },
      } as OpenAPIV3.Document,
      expected: {
        tools: {
          API: {
            methods: [
              {
                name: 'getComposed',
                description: 'Get a composed resource',
                inputSchema: {
                  type: 'object',
                  properties: {},
                  required: [],
                  $defs: {
                    Base: {
                      type: 'object',
                      description: 'Base schema description',
                      additionalProperties: true,
                      properties: {
                        baseName: {
                          type: 'string',
                          description: 'Name in the base schema',
                        },
                      },
                    },
                    C: {
                      description: 'C schema description',
                      allOf: [{ $ref: '#/$defs/Base' }, { $ref: '#/$defs/D' }, { $ref: '#/$defs/E' }],
                    },
                    D: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'D schema description',
                      properties: {
                        dProp: {
                          type: 'integer',
                          description: 'D property integer',
                        },
                      },
                    },
                    E: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'E schema description',
                      properties: {
                        choice: {
                          description: 'One of these choices',
                          oneOf: [{ $ref: '#/$defs/F' }, { $ref: '#/$defs/G' }],
                        },
                      },
                    },
                    F: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'F schema description',
                      properties: {
                        fVal: {
                          type: 'boolean',
                          description: 'Boolean in F',
                        },
                      },
                    },
                    G: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'G schema description',
                      properties: {
                        gVal: {
                          type: 'string',
                          description: 'String in G',
                        },
                      },
                    },
                  },
                },
                returnSchema: {
                  $ref: '#/$defs/C',
                  description: 'A composed object',
                  $defs: {
                    Base: {
                      type: 'object',
                      description: 'Base schema description',
                      additionalProperties: true,
                      properties: {
                        baseName: {
                          type: 'string',
                          description: 'Name in the base schema',
                        },
                      },
                    },
                    C: {
                      description: 'C schema description',
                      allOf: [{ $ref: '#/$defs/Base' }, { $ref: '#/$defs/D' }, { $ref: '#/$defs/E' }],
                    },
                    D: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'D schema description',
                      properties: {
                        dProp: {
                          type: 'integer',
                          description: 'D property integer',
                        },
                      },
                    },
                    E: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'E schema description',
                      properties: {
                        choice: {
                          description: 'One of these choices',
                          oneOf: [{ $ref: '#/$defs/F' }, { $ref: '#/$defs/G' }],
                        },
                      },
                    },
                    F: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'F schema description',
                      properties: {
                        fVal: {
                          type: 'boolean',
                          description: 'Boolean in F',
                        },
                      },
                    },
                    G: {
                      type: 'object',
                      additionalProperties: true,
                      description: 'G schema description',
                      properties: {
                        gVal: {
                          type: 'string',
                          description: 'String in G',
                        },
                      },
                    },
                  },
                },
              },
            ],
          },
        },
        openApiLookup: {
          'API-getComposed': {
            operationId: 'getComposed',
            summary: 'Get a composed resource',
            responses: {
              '200': {
                description: 'A composed object',
                content: {
                  'application/json': {
                    schema: { $ref: '#/components/schemas/C' },
                  },
                },
              },
            },
            method: 'get',
            path: '/composed',
          },
        },
      },
    },
  ]

  it.each(cases)('$name', ({ input, expected }) => {
    const converter = new OpenAPIToMCPConverter(input)
    const { tools, openApiLookup } = converter.convertToMCPTools()

    // Use the custom verification instead of direct equality
    verifyTools(tools, expected.tools)
    expect(openApiLookup).toEqual(expected.openApiLookup)
  })
})
