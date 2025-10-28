import { OpenApiToEndpointConverter } from "@mintlify/validation";
import { z } from "zod";
import { dataSchemaArrayToZod, dataSchemaToZod } from "./zod.js";
import { readConfig } from "../config.js";
import { 
  Endpoint, 
  ElicitationConfiguration,
} from "../types.js";
import {
  ElicitRequest,
  PrimitiveSchemaDefinition,
  StringSchema,
  NumberSchema
} from "@modelcontextprotocol/sdk/types.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import crypto from "crypto";
import fs from "fs";

export type CategorizedZod = {
  url: string;
  method: string;
  paths: Record<string, z.ZodTypeAny>;
  queries: Record<string, z.ZodTypeAny>;
  headers: Record<string, z.ZodTypeAny>;
  cookies: Record<string, z.ZodTypeAny>;
  body?: { body: z.ZodTypeAny };
  metadata?: Record<string, any>;
};

type RefCache = { [key: string]: any };

type Specification = {
  paths: {
    [path: string]: {
      [method: string]: any;
    };
  };
};

export type NestedRecord =
  | string
  | {
      [key: string]: NestedRecord;
    };

export type SimpleRecord = Record<string, { [x: string]: undefined }>;

export function convertStrToTitle(str: string): string {
  const spacedString = str.replace(/[-_]/g, " ");
  const words = spacedString.split(/(?=[A-Z])|\s+/);
  return words
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

export function findNextIteration(set: Set<string>, str: string): number {
  let count = 1;
  set.forEach((val) => {
    if (val.startsWith(`${str}---`)) {
      count = Number(val.replace(`${str}---`, ""));
    }
  });
  return count + 1;
}

function resolveReferences(
  spec: Record<string, any>,
  refPath: string,
  cache: Record<string, any> = {}
): any {
  if (cache[refPath]) return cache[refPath];
  if (!refPath.startsWith("#/"))
    throw new Error(`External references not supported: ${refPath}`);
  const pathParts = refPath.substring(2).split("/");
  let current: any = spec;
  for (const part of pathParts) {
    if (!current[part]) throw new Error(`Reference not found: ${refPath}`);
    current = current[part];
  }
  if (current && current.$ref) {
    current = resolveReferences(spec, current.$ref, cache);
  }
  cache[refPath] = current;
  return current;
}

function resolveAllReferences(
  obj: any,
  spec: Specification,
  cache: RefCache
): any {
  if (obj && obj.$ref) {
    const resolved = resolveReferences(spec, obj.$ref, cache);
    return resolveAllReferences({ ...resolved }, spec, cache);
  }
  if (typeof obj !== "object" || obj === null) {
    return obj;
  }
  const result: { [key: string]: any } = Array.isArray(obj) ? [] : {};
  for (const [key, value] of Object.entries(obj)) {
    result[key] = resolveAllReferences(value, spec, cache);
  }
  return result;
}


export function getEndpointsFromOpenApi(specification: any): Endpoint[] {
  const endpoints: Endpoint[] = [];
  const paths = specification.paths;
  const refCache: RefCache = {};

  for (const path in paths) {
    const operations = paths[path];
    for (const method in operations) {
      if (method === "parameters" || method === "trace") continue;
      try {
        const resolvedPathItem = resolveAllReferences(
          operations[method],
          specification,
          refCache
        );
        if (!isMcpEnabledEndpoint(resolvedPathItem)) continue;
        const rawEndpoint = OpenApiToEndpointConverter.convert(
          {
            ...specification,
            paths: { [path]: { [method]: resolvedPathItem } },
          } as any,
          path,
          method as any
        );
        
        // Convert to our Endpoint type and ensure x-mcp configuration is preserved
        const endpoint: Endpoint = {
          ...rawEndpoint,
          operation: {
            ...resolvedPathItem,
            "x-mcp": resolvedPathItem["x-mcp"]
          }
        };
        
        endpoints.push(endpoint);
      } catch (error: any) {
        console.error(
          `Error processing endpoint ${method.toUpperCase()} ${path}:`,
          error.message
        );
      }
    }
  }
  return endpoints;
}

export function loadEnv(key: string): SimpleRecord {
  try {
    const config: any = readConfig();
    return config[key] || {};
  } catch (error) {
    if (error instanceof SyntaxError) throw error;
    return {};
  }
}

// Zod schema conversion helpers
function convertParameterSection(parameters: any, paramSection: any) {
  if (parameters) {
    Object.entries(parameters).forEach(([key, value]: any) => {
      paramSection[key] = dataSchemaArrayToZod(value.schema);
    });
  }
}

function convertParametersAndAddToRelevantParamGroups(
  parameters: any,
  paths: any,
  queries: any,
  headers: any,
  cookies: any
) {
  convertParameterSection(parameters?.path, paths);
  convertParameterSection(parameters?.query, queries);
  convertParameterSection(parameters?.header, headers);
  convertParameterSection(parameters?.cookie, cookies);
}

function convertSecurityParameterSection(
  securityParameters: ArrayLike<unknown> | { [s: string]: unknown },
  securityParamSection: { [x: string]: z.ZodString },
  envVariables: { [x: string]: { [x: string]: undefined } },
  location: string
) {
  Object.entries(securityParameters).forEach(([key]) => {
    if (envVariables[location][key] === undefined) {
      securityParamSection[key] = z.string();
    }
  });
}

function convertSecurityParametersAndAddToRelevantParamGroups(
  securityParameters: {
    query: ArrayLike<unknown> | { [s: string]: unknown };
    header: ArrayLike<unknown> | { [s: string]: unknown };
    cookie: ArrayLike<unknown> | { [s: string]: unknown };
  },
  queries: { [x: string]: z.ZodString },
  headers: { [x: string]: z.ZodString },
  cookies: { [x: string]: z.ZodString },
  envVariables: SimpleRecord
) {
  convertSecurityParameterSection(
    securityParameters.query,
    queries,
    envVariables,
    "query"
  );
  convertSecurityParameterSection(
    securityParameters.header,
    headers,
    envVariables,
    "header"
  );
  convertSecurityParameterSection(
    securityParameters.cookie,
    cookies,
    envVariables,
    "cookie"
  );
}

export function convertEndpointToCategorizedZod(
  envKey: string,
  endpoint: Endpoint
): CategorizedZod {
  const envVariables = loadEnv(envKey);

  const baseUrl =
    envVariables.base_url ||
    (Array.isArray(endpoint?.servers) ? endpoint.servers[0]?.url : undefined) ||
    "";

  const url = `${baseUrl}${endpoint.path}`;
  const method = endpoint.method;

  const paths: Record<string, any> = {};
  const queries: Record<string, any> = {};
  const headers: Record<string, any> = {};
  const cookies: Record<string, any> = {};
  let body: any | undefined = undefined;

  convertParametersAndAddToRelevantParamGroups(
    endpoint?.request?.parameters,
    paths,
    queries,
    headers,
    cookies
  );

  const securityParams = endpoint?.request?.security?.[0]?.parameters;
  if (securityParams) {
    convertSecurityParametersAndAddToRelevantParamGroups(
      securityParams,
      queries,
      headers,
      cookies,
      envVariables
    );
  }

  const jsonBodySchema = endpoint?.request?.body?.["application/json"];
  const bodySchema = jsonBodySchema?.schemaArray?.[0];

  if (bodySchema) {
    let zodBodySchema = dataSchemaToZod(bodySchema);
    
    // If endpoint has elicitation config, make fields optional
    // Client capability check will happen at runtime
    if (hasElicitationEnabled(endpoint)) {
      zodBodySchema = makeElicitationFieldsOptional(zodBodySchema, endpoint);
    }
    
    body = { body: zodBodySchema };
  }

  const metadata = generateMetadataSchema();
  // console.error("Generated metadata schema: ", JSON.stringify(metadata));
  return {
    url,
    method,
    paths,
    queries,
    body,
    headers,
    cookies,
    metadata,
  };
}

const SourceEnum = z.enum([
  "user_input",
  "generated_by_model",
  "inferred_from_context"
]);

/**
 * Recursive schema that allows nested metadata objects.
 * Each key maps either to a source string or another nested object
 * following the same structure.
 */
const RecursiveSourceSchema: z.ZodTypeAny = z.lazy(() =>
  z.record(
    z.union([SourceEnum, RecursiveSourceSchema])
  ).describe("Nested object mapping each field to its source (recursively)")
);

/**
 * Generates metadata schema that mirrors input structure.
 * Tracks sources for input fields (e.g. body, headers, query, path),
 * allowing arbitrary nesting and unknown keys.
 */
export function generateMetadataSchema() {
  const InputVariableSourceSchema = z.object({
    body: RecursiveSourceSchema.describe(
      "Mirrors the input body object, tracking sources for all nested fields"
    )
  }).describe("Tracks the source of input parameters (body, headers, query, path)");

  return { inputVariableSource: InputVariableSourceSchema};
}


export function getValFromNestedJson(key: string, jsonObj: SimpleRecord): any {
  if (!key || !jsonObj) return;
  return jsonObj[key];
}

export function isMcpEnabled(path: string): boolean {
  const product = path.split(".json")[0].split("-")[1];
  const tools = process.env.TOOLS
    ? process.env.TOOLS.toLowerCase().split(",")
    : [];
  switch (product) {
    case "PG":
      return tools.includes("pg");
    case "PO":
      return tools.includes("payouts");
    case "VRS":
      return tools.includes("secureid");
    default:
      return false;
  }
}

export function isMcpEnabledEndpoint(endpointSpec: Endpoint): boolean {
  const mcp = (endpointSpec as any)["x-mcp"];
  return mcp?.["enabled"] === true;
}

/**
 * Generate a signature by encrypting the client ID and current UNIX timestamp using RSA encryption.
 * @param {string} clientId - The client ID to be used in the signature.
 * @param {string} publicKey - The RSA public key for encryption.
 * @returns {string} - The generated signature.
 */
export function generateCfSignature(clientId: string, publicKey: string) {
  try {
    const timestamp = Math.floor(Date.now() / 1000); // Current UNIX timestamp
    const data = `${clientId}.${timestamp}`;
    const buffer = Buffer.from(data, "utf8");
    const encrypted = crypto.publicEncrypt(publicKey, buffer);
    return encrypted.toString("base64");
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Error generating signature: ${error.message}`);
    } else {
      console.error("Error generating signature: Unknown error");
    }
  }
}

/**
 * Retrieve the public key from a given file path.
 * @param {string} path - The file path to the public key.
 * @returns {string} - The public key as a string.
 * @throws {Error} - If the file cannot be read.
 */
export function getPublicKeyFromPath(path: string): string | null {
  try {
    return fs.readFileSync(path, "utf8");
  } catch (error) {
    console.error(
      `Warning: Failed to read public key from path: ${
        error instanceof Error ? error.message : "Unknown error"
      }`
    );
    return null;
  }
}

/**
 * Check if elicitation should be used for this endpoint
 * Returns true only if:
 * 1. Global elicitation is enabled via ELICITATION_ENABLED environment variable
 * 2. Endpoint has elicitation configuration
 * 3. Endpoint has elicitation enabled
 * Client support will be checked at runtime during execution
 */
export function shouldUseElicitation(endpoint: Endpoint): boolean {
  return hasElicitationEnabled(endpoint);
}

/**
 * Check if client supports elicitation by attempting to use it
 * This is a runtime check that will be done during tool execution
 */
export async function checkElicitationSupport(_server: McpServer): Promise<boolean> {
  try {
    // Try a simple elicitation request to check if client supports it
    // If it fails, the client doesn't support elicitation
    return true; // For now, assume supported - actual check happens during execution
  } catch (error) {
    return false;
  }
}

/**
 * Make fields that have elicitation configuration optional in the Zod schema
 * This allows elicitation to fill in missing required fields
 */
export function makeElicitationFieldsOptional(zodSchema: z.ZodTypeAny, endpoint: Endpoint): z.ZodTypeAny {
  // Check if elicitation is globally enabled first
  if (!hasElicitationEnabled(endpoint)) {
    return zodSchema;
  }
  
  const elicitationConfig = getElicitationConfig(endpoint);
  if (!elicitationConfig || !zodSchema) {
    return zodSchema;
  }

  // Get the list of field paths that should be made optional (those configured for elicitation)
  const elicitationFieldPaths = Object.entries(elicitationConfig.fields).map(([fieldName, fieldConfig]) => {
    // Use the target path from mapping, or fall back to field name
    const targetPath = fieldConfig.mapping?.target || fieldName;
    // For body fields, remove the 'body.' prefix if present
    return targetPath.startsWith('body.') ? targetPath.substring(5) : targetPath;
  });

  return makeFieldsOptionalAtPaths(zodSchema, elicitationFieldPaths);
}

/**
 * Recursively make fields optional at specified paths in a Zod schema
 */
function makeFieldsOptionalAtPaths(zodSchema: z.ZodTypeAny, fieldPaths: string[]): z.ZodTypeAny {
  if (!(zodSchema instanceof z.ZodObject)) {
    return zodSchema;
  }

  const shape = zodSchema.shape;
  const newShape: Record<string, z.ZodTypeAny> = {};

  // Process each field in the schema
  for (const [key, value] of Object.entries(shape)) {
    // Check if this field should be made optional (exact match)
    const shouldMakeOptional = fieldPaths.includes(key);
    
    // Check for nested paths that start with this key
    const nestedPaths = fieldPaths
      .filter(path => path.startsWith(`${key}.`))
      .map(path => path.substring(key.length + 1)); // Remove the key and dot prefix

    if (shouldMakeOptional) {
      // Make this field optional since it can be provided via elicitation
      newShape[key] = makeFieldOptional(value as z.ZodTypeAny);
    } else if (nestedPaths.length > 0 && value instanceof z.ZodObject) {
      // Recursively process nested objects for nested field paths
      newShape[key] = makeFieldsOptionalAtPaths(value, nestedPaths);
    } else if (value instanceof z.ZodObject) {
      // Process nested objects even if no specific paths match (for deeper nesting)
      newShape[key] = makeFieldsOptionalAtPaths(value, fieldPaths);
    } else {
      // Keep the field as is
      newShape[key] = value as z.ZodTypeAny;
    }
  }

  return z.object(newShape);
}

/**
 * Helper function to make a Zod field optional
 */
function makeFieldOptional(zodType: z.ZodTypeAny): z.ZodTypeAny {
  // If it's already optional, return as is
  if (zodType instanceof z.ZodOptional) {
    return zodType;
  }
  
  // Make the field optional
  return zodType.optional();
}

/**
 * Extract elicitation configuration from an endpoint's x-mcp section
 */
export function getElicitationConfig(endpoint: Endpoint): ElicitationConfiguration | null {
  // Try multiple locations for x-mcp configuration
  const mcpConfig = endpoint.operation?.["x-mcp"] || (endpoint as any)["x-mcp"];
  if (!mcpConfig || !mcpConfig.config?.elicitation) {
    return null;
  }
  return mcpConfig.config.elicitation;
}

/**
 * Check if an endpoint has elicitation enabled
 * Now checks both global environment variable and endpoint-specific configuration
 */
export function hasElicitationEnabled(endpoint: Endpoint): boolean {
  // First check if elicitation is globally enabled via environment variable
  if (process.env.ELICITATION_ENABLED?.toLowerCase() !== 'true')  {
    return false;
  }

  // Then check endpoint-specific configuration
  const config = getElicitationConfig(endpoint);
  return config !== null && config.enabled && Object.keys(config.fields || {}).length > 0;
}

/**
 * Identify missing required fields for elicitation
 */
export function getElicitationRequestFields(
  elicitationConfig: ElicitationConfiguration,
  providedArgs: Record<string, any>,
  inputVariableSource: Record<string, any>,
  elicitationRequest: any
): { missingFields: string[]; defaults: Record<string, any> } {
  const missingFields: string[] = [];
  const defaults: Record<string, any> = {};

  const getValueFromInputVariableSource = (path: string): any => {
    if (!inputVariableSource) return undefined;
    const parts = path.split('.');
    let current: any = inputVariableSource;
    for (const part of parts) {
      if (!current) return undefined;
      current = current[part];
    }
    return current;
  };

  Object.entries(elicitationConfig.fields).forEach(([fieldName, fieldConfig]) => {
    const targetPath = fieldConfig.mapping?.target || fieldName;
    
    // For body fields, get the path relative to the body
    const bodyRelativePath = targetPath.startsWith('body.') ? targetPath.substring(5) : targetPath;

    // Check if value exists in provided args at the target path
    const valueFromArgs = hasValueAtPath(providedArgs, targetPath) 
      ? getValueAtPath(providedArgs, targetPath)
      : hasValueAtPath(providedArgs, bodyRelativePath)
      ? getValueAtPath(providedArgs, bodyRelativePath)
      : providedArgs[fieldName];

    // Check input variable source using the full target path
    const valueFromInputVariableSource = getValueFromInputVariableSource(targetPath);

    // Use input variable source value as default if available
    let defaultValue = valueFromArgs ?? (valueFromInputVariableSource && valueFromInputVariableSource !== 'generated_by_model' ? valueFromInputVariableSource : undefined);

    if (valueFromInputVariableSource === 'generated_by_model') {
      // Treat generated_by_model as default but still ask if required
      defaultValue = valueFromArgs ?? undefined;
    }

    // Determine if we need to ask
    const isMissing = fieldConfig.required && (valueFromArgs === undefined || valueFromArgs === '');
    const isGeneratedByModel = valueFromInputVariableSource === 'generated_by_model';
    
    if (isMissing || isGeneratedByModel) {
      missingFields.push(fieldName);
      
      // Only add to elicitation request schema if field is actually missing
      if (!elicitationRequest.params.requestedSchema.properties[fieldName]) {
        elicitationRequest.params.requestedSchema.properties[fieldName] = fieldConfig.schema;
      }
      
      // Set default value if available
      if (defaultValue !== undefined) {
        defaults[fieldName] = defaultValue;
        elicitationRequest.params.requestedSchema.properties[fieldName].default = defaultValue;
      }
    }
  });

  return { missingFields, defaults};
};


// Helper to get value at path
function getValueAtPath(obj: any, path: string) {
  return path.split('.').reduce((acc, key) => (acc ? acc[key] : undefined), obj);
}


/**
 * Check if a value exists at a given path in an object
 */
function hasValueAtPath(obj: any, path: string): boolean {
  const parts = path.split('.');
  let current = obj;
  
  for (const part of parts) {
    if (current === null || current === undefined || !(part in current)) {
      return false;
    }
    current = current[part];
  }
  
  return current !== null && current !== undefined && current !== '';
}

/**
 * Create an elicitation request for missing fields
 */
export function createElicitationRequest(
  toolName: string,
  missingFieldNames: string[],
  elicitationConfig: ElicitationConfiguration,
  message?: string
): ElicitRequest {
  const properties: Record<string, PrimitiveSchemaDefinition> = {};
  const required: string[] = [];

  for (const fieldName of missingFieldNames) {
    const fieldConfig = elicitationConfig.fields[fieldName];
    if (fieldConfig) {
      properties[fieldName] = fieldConfig.schema;
      if (fieldConfig.required) {
        required.push(fieldName);
      }
    }
  }

  return {
    method: "elicitation/create",
    params: {
      message: message || `Please provide the required parameters for ${toolName}:`,
      requestedSchema: {
        type: "object",
        properties,
        ...(required.length > 0 && { required })
      }
    }
  };
}/**
 * Apply field mappings to elicitation response values
 */
export function applyFieldMappings(
  elicitationConfig: ElicitationConfiguration,
  elicitationResponse: Record<string, any>,
  originalArgs: Record<string, any>
): Record<string, any> {
  const mappedArgs = { ...originalArgs };
  
  Object.entries(elicitationResponse).forEach(([fieldName, value]) => {
    const fieldConfig = elicitationConfig.fields[fieldName];
    if (fieldConfig && fieldConfig.mapping) {
      const mapping = fieldConfig.mapping;
      setValueAtPath(mappedArgs, mapping.target, value, mapping.transform);
    } else {
      // Check if any field in the config matches this field name
      const matchingConfigField = Object.entries(elicitationConfig.fields).find(
        ([configFieldName]) => configFieldName === fieldName || configFieldName.split('.').pop() === fieldName
      );
      
      if (matchingConfigField) {
        const [, configField] = matchingConfigField;
        if (configField && configField.mapping) {
          setValueAtPath(mappedArgs, configField.mapping.target, value, configField.mapping.transform);
        }
      } else {
        // If no mapping exists, use the field name directly
        mappedArgs[fieldName] = value;
      }
    }
  });
  
  return mappedArgs;
}

/**
 * Set a value at a given path in an object
 */
function setValueAtPath(obj: any, path: string, value: any, transformation?: string): void {
  const parts = path.split('.');
  let current = obj;
  
  // Navigate to the parent of the target
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    if (!(part in current) || current[part] === null || current[part] === undefined) {
      current[part] = {};
    }
    current = current[part];
  }
  
  // Apply transformation if specified
  let transformedValue = value;
  if (transformation) {
    transformedValue = applyTransformation(value, transformation);
  }
  
  // Set the final value
  const finalPart = parts[parts.length - 1];
  current[finalPart] = transformedValue;
}

/**
 * Apply transformation to a value
 */
function applyTransformation(value: any, transformation: string): any {
  switch (transformation) {
    case 'number':
      return Number(value);
    case 'boolean':
      return Boolean(value);
    case 'string':
      return String(value);
    case 'array':
      return Array.isArray(value) ? value : [value];
    default:
      return value;
  }
}

/**
 * Validate elicitation response against validation schema
 */
export function validateElicitationResponse(
  elicitationConfig: ElicitationConfiguration,
  response: Record<string, any>
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  Object.entries(response).forEach(([fieldName, value]) => {
    const fieldConfig = elicitationConfig.fields[fieldName];
    if (fieldConfig && fieldConfig.schema) {
      const schema = fieldConfig.schema;
      
      // Simple validation based on schema type
      if (schema.type === 'string') {
        const stringSchema = schema as StringSchema & { pattern?: string; enum?: string[] };
        
        if (stringSchema.pattern && typeof value === 'string' && typeof stringSchema.pattern === 'string') {
          const regex = new RegExp(stringSchema.pattern);
          if (!regex.test(value)) {
            errors.push(`Field ${fieldName} does not match required pattern`);
          }
        }
        
        if (typeof value === 'string') {
          if (stringSchema.minLength && value.length < stringSchema.minLength) {
            errors.push(`Field ${fieldName} is too short (minimum ${stringSchema.minLength} characters)`);
          }
          if (stringSchema.maxLength && value.length > stringSchema.maxLength) {
            errors.push(`Field ${fieldName} is too long (maximum ${stringSchema.maxLength} characters)`);
          }
        }
        
        if (stringSchema.enum && Array.isArray(stringSchema.enum) && !stringSchema.enum.includes(value)) {
          errors.push(`Field ${fieldName} must be one of: ${stringSchema.enum.join(', ')}`);
        }
      }
      
      if (schema.type === 'number' || schema.type === 'integer') {
        const numberSchema = schema as NumberSchema;
        
        if (typeof value === 'number') {
          if (numberSchema.minimum !== undefined && value < numberSchema.minimum) {
            errors.push(`Field ${fieldName} is too small (minimum ${numberSchema.minimum})`);
          }
          if (numberSchema.maximum !== undefined && value > numberSchema.maximum) {
            errors.push(`Field ${fieldName} is too large (maximum ${numberSchema.maximum})`);
          }
        }
      }
    }
  });
  
  return {
    valid: errors.length === 0,
    errors
  };
}
