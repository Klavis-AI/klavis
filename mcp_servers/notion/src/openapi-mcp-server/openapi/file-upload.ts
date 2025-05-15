import { OpenAPIV3 } from 'openapi-types'

/**
 * Identifies file upload parameters in an OpenAPI operation
 * @param operation The OpenAPI operation object to check
 * @returns Array of parameter names that are file uploads
 */
export function isFileUploadParameter(operation: OpenAPIV3.OperationObject): string[] {
  const fileParams: string[] = []

  if (!operation.requestBody) return fileParams

  const requestBody = operation.requestBody as OpenAPIV3.RequestBodyObject
  const content = requestBody.content || {}

  // Check multipart/form-data content type for file uploads
  const multipartContent = content['multipart/form-data']
  if (!multipartContent?.schema) return fileParams

  const schema = multipartContent.schema as OpenAPIV3.SchemaObject
  if (schema.type !== 'object' || !schema.properties) return fileParams

  // Look for properties with type: string, format: binary which indicates file uploads
  Object.entries(schema.properties).forEach(([propName, prop]) => {
    const schemaProp = prop as OpenAPIV3.SchemaObject
    if (schemaProp.type === 'string' && schemaProp.format === 'binary') {
      fileParams.push(propName)
    }

    // Check for array of files
    if (schemaProp.type === 'array' && schemaProp.items) {
      const itemSchema = schemaProp.items as OpenAPIV3.SchemaObject
      if (itemSchema.type === 'string' && itemSchema.format === 'binary') {
        fileParams.push(propName)
      }
    }
  })

  return fileParams
}
