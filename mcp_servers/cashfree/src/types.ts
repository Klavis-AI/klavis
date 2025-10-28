import { PrimitiveSchemaDefinition } from "@modelcontextprotocol/sdk/types.js";

export interface InitializationConfiguration {
  name: string;
  trieveApiKey: string;
  trieveDatasetId: string;
}

export interface SearchResult {
  title: string;
  content: string;
  link: string;
}

export interface Endpoint {
  url?: string;
  method: string;
  path: string;
  title?: string;
  description?: string;
  request: { [key: string]: any };
  servers?: Array<{ url: string }> | { [key: string]: any };
  operation: {
    summary?: string;
    description?: string;
    tags?: string[];
    "x-mcp"?: McpConfiguration;
    operationId?: string;
    deprecated?: boolean;
    security?: any[];
    parameters?: any[];
    requestBody?: any;
    responses?: any;
    [key: string]: any;
  };
}

export interface McpConfiguration {
  enabled: boolean;
  config?: {
    elicitation?: ElicitationConfiguration;
  };
}

// Elicitation configuration for OpenAPI endpoints
export interface ElicitationConfiguration {
  enabled: boolean;
  fields: Record<string, ElicitationField>;
}

export interface ElicitationField {
  required: boolean;
  message: string;
  schema: PrimitiveSchemaDefinition;
  mapping: {
    target: string;
    transform?: 'string' | 'number' | 'boolean' | 'array';
  };
}
