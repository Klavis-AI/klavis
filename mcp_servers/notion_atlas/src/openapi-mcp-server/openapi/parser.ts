import type { OpenAPIV3, OpenAPIV3_1 } from 'openapi-types'
import type { JSONSchema7 as IJsonSchema } from 'json-schema'
import type { ChatCompletionTool } from 'openai/resources/chat/completions'
import type { Tool } from '@anthropic-ai/sdk/resources/messages/messages'

type NewToolMethod = {
  name: string
  description: string
  inputSchema: IJsonSchema & { type: 'object' }
  returnSchema?: IJsonSchema
}

type FunctionParameters = {
  type: 'object'
  properties?: Record<string, unknown>
  required?: string[]
  [key: string]: unknown
}

export class OpenAPIToMCPConverter {
  private schemaCache: Record<string, IJsonSchema> = {}
  private nameCounter: number = 0

  constructor(private openApiSpec: OpenAPIV3.Document | OpenAPIV3_1.Document) {}

  /**
   * Resolve a $ref reference to its schema in the openApiSpec.
   * Returns the raw OpenAPI SchemaObject or null if not found.
   */
  private internalResolveRef(ref: string, resolvedRefs: Set<string>): OpenAPIV3.SchemaObject | null {
    if (!ref.startsWith('#/')) {
      return null
    }
    if (resolvedRefs.has(ref)) {
      return null
    }

    const parts = ref.replace(/^#\//, '').split('/')
    let current: any = this.openApiSpec
    for (const part of parts) {
      current = current[part]
      if (!current) return null
    }
    resolvedRefs.add(ref)
    return current as OpenAPIV3.SchemaObject
  }

  /**
   * Convert an OpenAPI schema (or reference) into a JSON Schema object.
   * Uses caching and handles cycles by returning $ref nodes.
   */
  convertOpenApiSchemaToJsonSchema(
    schema: OpenAPIV3.SchemaObject | OpenAPIV3.ReferenceObject,
    resolvedRefs: Set<string>,
    resolveRefs: boolean = false,
  ): IJsonSchema {
    if ('$ref' in schema) {
      const ref = schema.$ref
      if (!resolveRefs) {
        if (ref.startsWith('#/components/schemas/')) {
          return {
            $ref: ref.replace(/^#\/components\/schemas\//, '#/$defs/'),
            ...('description' in schema ? { description: schema.description as string } : {}),
          }
        }
        console.error(`Attempting to resolve ref ${ref} not found in components collection.`)
        // deliberate fall through
      }
      // Create base schema with $ref and description if present
      const refSchema: IJsonSchema = { $ref: ref }
      if ('description' in schema && schema.description) {
        refSchema.description = schema.description as string
      }

      // If already cached, return immediately with description
      if (this.schemaCache[ref]) {
        return this.schemaCache[ref]
      }

      const resolved = this.internalResolveRef(ref, resolvedRefs)
      if (!resolved) {
        // TODO: need extensive tests for this and we definitely need to handle the case of self references
        console.error(`Failed to resolve ref ${ref}`)
        return {
          $ref: ref.replace(/^#\/components\/schemas\//, '#/$defs/'),
          description: 'description' in schema ? ((schema.description as string) ?? '') : '',
        }
      } else {
        const converted = this.convertOpenApiSchemaToJsonSchema(resolved, resolvedRefs, resolveRefs)
        this.schemaCache[ref] = converted

        return converted
      }
    }

    // Handle inline schema
    const result: IJsonSchema = {}

    if (schema.type) {
      result.type = schema.type as IJsonSchema['type']
    }

    // Convert binary format to uri-reference and enhance description
    if (schema.format === 'binary') {
      result.format = 'uri-reference'
      const binaryDesc = 'absolute paths to local files'
      result.description = schema.description ? `${schema.description} (${binaryDesc})` : binaryDesc
    } else {
      if (schema.format) {
        result.format = schema.format
      }
      if (schema.description) {
        result.description = schema.description
      }
    }

    if (schema.enum) {
      result.enum = schema.enum
    }

    if (schema.default !== undefined) {
      result.default = schema.default
    }

    // Handle object properties
    if (schema.type === 'object') {
      result.type = 'object'
      if (schema.properties) {
        result.properties = {}
        for (const [name, propSchema] of Object.entries(schema.properties)) {
          result.properties[name] = this.convertOpenApiSchemaToJsonSchema(propSchema, resolvedRefs, resolveRefs)
        }
      }
      if (schema.required) {
        result.required = schema.required
      }
      if (schema.additionalProperties === true || schema.additionalProperties === undefined) {
        result.additionalProperties = true
      } else if (schema.additionalProperties && typeof schema.additionalProperties === 'object') {
        result.additionalProperties = this.convertOpenApiSchemaToJsonSchema(schema.additionalProperties, resolvedRefs, resolveRefs)
      } else {
        result.additionalProperties = false
      }
    }

    // Handle arrays - ensure binary format conversion happens for array items too
    if (schema.type === 'array' && schema.items) {
      result.type = 'array'
      result.items = this.convertOpenApiSchemaToJsonSchema(schema.items, resolvedRefs, resolveRefs)
    }

    // oneOf, anyOf, allOf
    if (schema.oneOf) {
      result.oneOf = schema.oneOf.map((s) => this.convertOpenApiSchemaToJsonSchema(s, resolvedRefs, resolveRefs))
    }
    if (schema.anyOf) {
      result.anyOf = schema.anyOf.map((s) => this.convertOpenApiSchemaToJsonSchema(s, resolvedRefs, resolveRefs))
    }
    if (schema.allOf) {
      result.allOf = schema.allOf.map((s) => this.convertOpenApiSchemaToJsonSchema(s, resolvedRefs, resolveRefs))
    }

    return result
  }

  convertToMCPTools(): {
    tools: Record<string, { methods: NewToolMethod[] }>
    openApiLookup: Record<string, OpenAPIV3.OperationObject & { method: string; path: string }>
    zip: Record<string, { openApi: OpenAPIV3.OperationObject & { method: string; path: string }; mcp: NewToolMethod }>
  } {
    const apiName = 'API'

    const openApiLookup: Record<string, OpenAPIV3.OperationObject & { method: string; path: string }> = {}
    const tools: Record<string, { methods: NewToolMethod[] }> = {
      [apiName]: { methods: [] },
    }
    const zip: Record<string, { openApi: OpenAPIV3.OperationObject & { method: string; path: string }; mcp: NewToolMethod }> = {}
    for (const [path, pathItem] of Object.entries(this.openApiSpec.paths || {})) {
      if (!pathItem) continue

      for (const [method, operation] of Object.entries(pathItem)) {
        if (!this.isOperation(method, operation)) continue

        const mcpMethod = this.convertOperationToMCPMethod(operation, method, path)
        if (mcpMethod) {
          const uniqueName = this.ensureUniqueName(mcpMethod.name)
          mcpMethod.name = uniqueName
          tools[apiName]!.methods.push(mcpMethod)
          openApiLookup[apiName + '-' + uniqueName] = { ...operation, method, path }
          zip[apiName + '-' + uniqueName] = { openApi: { ...operation, method, path }, mcp: mcpMethod }
        }
      }
    }

    return { tools, openApiLookup, zip }
  }

  /**
   * Convert the OpenAPI spec to OpenAI's ChatCompletionTool format
   */
  convertToOpenAITools(): ChatCompletionTool[] {
    const tools: ChatCompletionTool[] = []

    for (const [path, pathItem] of Object.entries(this.openApiSpec.paths || {})) {
      if (!pathItem) continue

      for (const [method, operation] of Object.entries(pathItem)) {
        if (!this.isOperation(method, operation)) continue

        const parameters = this.convertOperationToJsonSchema(operation, method, path)
        const tool: ChatCompletionTool = {
          type: 'function',
          function: {
            name: operation.operationId!,
            description: operation.summary || operation.description || '',
            parameters: parameters as FunctionParameters,
          },
        }
        tools.push(tool)
      }
    }

    return tools
  }

  /**
   * Convert the OpenAPI spec to Anthropic's Tool format
   */
  convertToAnthropicTools(): Tool[] {
    const tools: Tool[] = []

    for (const [path, pathItem] of Object.entries(this.openApiSpec.paths || {})) {
      if (!pathItem) continue

      for (const [method, operation] of Object.entries(pathItem)) {
        if (!this.isOperation(method, operation)) continue

        const parameters = this.convertOperationToJsonSchema(operation, method, path)
        const tool: Tool = {
          name: operation.operationId!,
          description: operation.summary || operation.description || '',
          input_schema: parameters as Tool['input_schema'],
        }
        tools.push(tool)
      }
    }

    return tools
  }

  private convertComponentsToJsonSchema(): Record<string, IJsonSchema> {
    const components = this.openApiSpec.components || {}
    const schema: Record<string, IJsonSchema> = {}
    for (const [key, value] of Object.entries(components.schemas || {})) {
      schema[key] = this.convertOpenApiSchemaToJsonSchema(value, new Set())
    }
    return schema
  }
  /**
   * Helper method to convert an operation to a JSON Schema for parameters
   */
  private convertOperationToJsonSchema(
    operation: OpenAPIV3.OperationObject,
    method: string,
    path: string,
  ): IJsonSchema & { type: 'object' } {
    const schema: IJsonSchema & { type: 'object' } = {
      type: 'object',
      properties: {},
      required: [],
      $defs: this.convertComponentsToJsonSchema(),
    }

    // Handle parameters (path, query, header, cookie)
    if (operation.parameters) {
      for (const param of operation.parameters) {
        const paramObj = this.resolveParameter(param)
        if (paramObj && paramObj.schema) {
          const paramSchema = this.convertOpenApiSchemaToJsonSchema(paramObj.schema, new Set())
          // Merge parameter-level description if available
          if (paramObj.description) {
            paramSchema.description = paramObj.description
          }
          schema.properties![paramObj.name] = paramSchema
          if (paramObj.required) {
            schema.required!.push(paramObj.name)
          }
        }
      }
    }

    // Handle requestBody
    if (operation.requestBody) {
      const bodyObj = this.resolveRequestBody(operation.requestBody)
      if (bodyObj?.content) {
        if (bodyObj.content['application/json']?.schema) {
          const bodySchema = this.convertOpenApiSchemaToJsonSchema(bodyObj.content['application/json'].schema, new Set())
          if (bodySchema.type === 'object' && bodySchema.properties) {
            for (const [name, propSchema] of Object.entries(bodySchema.properties)) {
              schema.properties![name] = propSchema
            }
            if (bodySchema.required) {
              schema.required!.push(...bodySchema.required)
            }
          }
        }
      }
    }

    return schema
  }

  private isOperation(method: string, operation: any): operation is OpenAPIV3.OperationObject {
    return ['get', 'post', 'put', 'delete', 'patch'].includes(method.toLowerCase())
  }

  private isParameterObject(param: OpenAPIV3.ParameterObject | OpenAPIV3.ReferenceObject): param is OpenAPIV3.ParameterObject {
    return !('$ref' in param)
  }

  private isRequestBodyObject(body: OpenAPIV3.RequestBodyObject | OpenAPIV3.ReferenceObject): body is OpenAPIV3.RequestBodyObject {
    return !('$ref' in body)
  }

  private resolveParameter(param: OpenAPIV3.ParameterObject | OpenAPIV3.ReferenceObject): OpenAPIV3.ParameterObject | null {
    if (this.isParameterObject(param)) {
      return param
    } else {
      const resolved = this.internalResolveRef(param.$ref, new Set())
      if (resolved && (resolved as OpenAPIV3.ParameterObject).name) {
        return resolved as OpenAPIV3.ParameterObject
      }
    }
    return null
  }

  private resolveRequestBody(body: OpenAPIV3.RequestBodyObject | OpenAPIV3.ReferenceObject): OpenAPIV3.RequestBodyObject | null {
    if (this.isRequestBodyObject(body)) {
      return body
    } else {
      const resolved = this.internalResolveRef(body.$ref, new Set())
      if (resolved) {
        return resolved as OpenAPIV3.RequestBodyObject
      }
    }
    return null
  }

  private resolveResponse(response: OpenAPIV3.ResponseObject | OpenAPIV3.ReferenceObject): OpenAPIV3.ResponseObject | null {
    if ('$ref' in response) {
      const resolved = this.internalResolveRef(response.$ref, new Set())
      if (resolved) {
        return resolved as OpenAPIV3.ResponseObject
      } else {
        return null
      }
    }
    return response
  }

  private convertOperationToMCPMethod(operation: OpenAPIV3.OperationObject, method: string, path: string): NewToolMethod | null {
    if (!operation.operationId) {
      console.warn(`Operation without operationId at ${method} ${path}`)
      return null
    }

    const methodName = operation.operationId

    const inputSchema: IJsonSchema & { type: 'object' } = {
      $defs: this.convertComponentsToJsonSchema(),
      type: 'object',
      properties: {},
      required: [],
    }

    // Handle parameters (path, query, header, cookie)
    if (operation.parameters) {
      for (const param of operation.parameters) {
        const paramObj = this.resolveParameter(param)
        if (paramObj && paramObj.schema) {
          const schema = this.convertOpenApiSchemaToJsonSchema(paramObj.schema, new Set(), false)
          // Merge parameter-level description if available
          if (paramObj.description) {
            schema.description = paramObj.description
          }
          inputSchema.properties![paramObj.name] = schema
          if (paramObj.required) {
            inputSchema.required!.push(paramObj.name)
          }
        }
      }
    }

    // Handle requestBody
    if (operation.requestBody) {
      const bodyObj = this.resolveRequestBody(operation.requestBody)
      if (bodyObj?.content) {
        // Handle multipart/form-data for file uploads
        // We convert the multipart/form-data schema to a JSON schema and we require
        // that the user passes in a string for each file that points to the local file
        if (bodyObj.content['multipart/form-data']?.schema) {
          const formSchema = this.convertOpenApiSchemaToJsonSchema(bodyObj.content['multipart/form-data'].schema, new Set(), false)
          if (formSchema.type === 'object' && formSchema.properties) {
            for (const [name, propSchema] of Object.entries(formSchema.properties)) {
              inputSchema.properties![name] = propSchema
            }
            if (formSchema.required) {
              inputSchema.required!.push(...formSchema.required!)
            }
          }
        }
        // Handle application/json
        else if (bodyObj.content['application/json']?.schema) {
          const bodySchema = this.convertOpenApiSchemaToJsonSchema(bodyObj.content['application/json'].schema, new Set(), false)
          // Merge body schema into the inputSchema's properties
          if (bodySchema.type === 'object' && bodySchema.properties) {
            for (const [name, propSchema] of Object.entries(bodySchema.properties)) {
              inputSchema.properties![name] = propSchema
            }
            if (bodySchema.required) {
              inputSchema.required!.push(...bodySchema.required!)
            }
          } else {
            // If the request body is not an object, just put it under "body"
            inputSchema.properties!['body'] = bodySchema
            inputSchema.required!.push('body')
          }
        }
      }
    }

    // Build description including error responses
    let description = operation.summary || operation.description || ''
    if (operation.responses) {
      const errorResponses = Object.entries(operation.responses)
        .filter(([code]) => code.startsWith('4') || code.startsWith('5'))
        .map(([code, response]) => {
          const responseObj = this.resolveResponse(response)
          let errorDesc = responseObj?.description || ''
          return `${code}: ${errorDesc}`
        })

      if (errorResponses.length > 0) {
        description += '\nError Responses:\n' + errorResponses.join('\n')
      }
    }

    // Extract return type (response schema)
    const returnSchema = this.extractResponseType(operation.responses)

    // Generate Zod schema from input schema
    try {
      // const zodSchemaStr = jsonSchemaToZod(inputSchema, { module: "cjs" })
      // console.log(zodSchemaStr)
      // // Execute the function with the zod instance
      // const zodSchema = eval(zodSchemaStr) as z.ZodType

      return {
        name: methodName,
        description,
        inputSchema,
        ...(returnSchema ? { returnSchema } : {}),
      }
    } catch (error) {
      console.warn(`Failed to generate Zod schema for ${methodName}:`, error)
      // Fallback to a basic object schema
      return {
        name: methodName,
        description,
        inputSchema,
        ...(returnSchema ? { returnSchema } : {}),
      }
    }
  }

  private extractResponseType(responses: OpenAPIV3.ResponsesObject | undefined): IJsonSchema | null {
    // Look for a success response
    const successResponse = responses?.['200'] || responses?.['201'] || responses?.['202'] || responses?.['204']
    if (!successResponse) return null

    const responseObj = this.resolveResponse(successResponse)
    if (!responseObj || !responseObj.content) return null

    if (responseObj.content['application/json']?.schema) {
      const returnSchema = this.convertOpenApiSchemaToJsonSchema(responseObj.content['application/json'].schema, new Set(), false)
      returnSchema['$defs'] = this.convertComponentsToJsonSchema()

      // Preserve the response description if available and not already set
      if (responseObj.description && !returnSchema.description) {
        returnSchema.description = responseObj.description
      }

      return returnSchema
    }

    // If no JSON response, fallback to a generic string or known formats
    if (responseObj.content['image/png'] || responseObj.content['image/jpeg']) {
      return { type: 'string', format: 'binary', description: responseObj.description || '' }
    }

    // Fallback
    return { type: 'string', description: responseObj.description || '' }
  }

  private ensureUniqueName(name: string): string {
    if (name.length <= 64) {
      return name
    }

    const truncatedName = name.slice(0, 64 - 5) // Reserve space for suffix
    const uniqueSuffix = this.generateUniqueSuffix()
    return `${truncatedName}-${uniqueSuffix}`
  }

  private generateUniqueSuffix(): string {
    this.nameCounter += 1
    return this.nameCounter.toString().padStart(4, '0')
  }
}
