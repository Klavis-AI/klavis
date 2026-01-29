import type { Tool } from '@modelcontextprotocol/sdk/types.js';
import type {
	JsonSchema,
	JsonSchemaProperty,
	SchemaComplexityResult,
	ParameterInfo,
} from '../types.js';
import { isFileDataProperty } from '../types.js';

/**
 * Analyzes a tool schema to determine if it's simple enough for the dynamic space tool
 *
 * Supported types:
 * - string, number, boolean
 * - enum (with predefined values)
 * - array of primitives
 * - shallow objects (one level deep with primitive properties)
 * - FileData (as string URLs)
 *
 * Rejected types:
 * - Deeply nested objects (2+ levels)
 * - Arrays of objects
 * - Union types
 * - Recursive schemas
 */
export function analyzeSchemaComplexity(tool: Tool): SchemaComplexityResult {
	const result: SchemaComplexityResult = {
		isSimple: true,
		parameters: [],
		toolName: tool.name,
		toolDescription: tool.description,
	};

	const inputSchema = tool.inputSchema as JsonSchema;
	if (!inputSchema || !inputSchema.properties) {
		return result;
	}

	const properties = inputSchema.properties;
	const required = inputSchema.required || [];

	for (const [paramName, prop] of Object.entries(properties)) {
		const paramInfo = analyzeProperty(paramName, prop, required.includes(paramName));

		// Check if this parameter is too complex
		if (paramInfo.complexType) {
			result.isSimple = false;
			result.reason = `Parameter "${paramName}" has complex type: ${paramInfo.complexType}`;
			return result;
		}

		result.parameters.push(paramInfo);
	}

	return result;
}

/**
 * Analyzes a single property to extract parameter information
 */
function analyzeProperty(name: string, prop: JsonSchemaProperty, isRequired: boolean): ParameterInfo {
	const paramInfo: ParameterInfo = {
		name,
		type: prop.type || 'unknown',
		description: prop.description,
		required: isRequired,
		default: prop.default,
		enum: prop.enum,
	};

	// Check for FileData types - treat as string URLs
	if (isFileDataProperty(prop)) {
		paramInfo.type = 'string (file URL)';
		paramInfo.isFileData = true;
		return paramInfo;
	}

	// Check for enum types
	if (prop.enum && Array.isArray(prop.enum) && prop.enum.length > 0) {
		paramInfo.type = `enum (${prop.enum.length} values)`;
		return paramInfo;
	}

	// Check for complex types
	if (prop.type === 'object') {
		// Check if it's a shallow object
		if (prop.properties) {
			const nestedProps = Object.values(prop.properties);
			const hasComplexNested = nestedProps.some(
				(nested) => nested.type === 'object' || nested.type === 'array'
			);

			if (hasComplexNested) {
				paramInfo.complexType = 'deeply nested object (2+ levels)';
			} else {
				paramInfo.type = 'object (shallow)';
			}
		} else {
			// Object without properties definition is too vague
			paramInfo.complexType = 'object without defined properties';
		}
		return paramInfo;
	}

	// Check for array types
	if (prop.type === 'array') {
		if (prop.items) {
			const itemType = prop.items.type;
			if (itemType === 'object') {
				paramInfo.complexType = 'array of objects';
			} else if (itemType === 'array') {
				paramInfo.complexType = 'nested arrays';
			} else {
				paramInfo.type = `array<${itemType || 'unknown'}>`;
			}
		} else {
			paramInfo.type = 'array<any>';
		}
		return paramInfo;
	}

	// Simple types are fine
	if (['string', 'number', 'integer', 'boolean'].includes(prop.type || '')) {
		return paramInfo;
	}

	// Unknown or unsupported type
	if (!prop.type) {
		paramInfo.complexType = 'unknown type';
	}

	return paramInfo;
}

/**
 * Validates parameter values against the schema
 */
export function validateParameters(
	parameters: Record<string, unknown>,
	schemaResult: SchemaComplexityResult
): { valid: boolean; errors: string[] } {
	const errors: string[] = [];

	// Check for missing required parameters
	const requiredParams = schemaResult.parameters.filter((p) => p.required);
	for (const param of requiredParams) {
		if (!(param.name in parameters) || parameters[param.name] === undefined) {
			errors.push(`Missing required parameter: "${param.name}"`);
		}
	}

	// Check types (basic validation)
	for (const [key, value] of Object.entries(parameters)) {
		const paramInfo = schemaResult.parameters.find((p) => p.name === key);

		if (!paramInfo) {
			// Unknown parameter - warning but not error (permissive inputs)
			continue;
		}

		// Type checking
		if (value !== null && value !== undefined) {
			if (!validateType(value, paramInfo)) {
				errors.push(
					`Parameter "${key}" should be type ${paramInfo.type}, got ${typeof value}`
				);
			}
		}
	}

	return {
		valid: errors.length === 0,
		errors,
	};
}

/**
 * Validates a value against a parameter type
 */
function validateType(value: unknown, paramInfo: ParameterInfo): boolean {
	// FileData as string URL
	if (paramInfo.isFileData) {
		return typeof value === 'string';
	}

	// Enum validation
	if (paramInfo.enum && Array.isArray(paramInfo.enum)) {
		return paramInfo.enum.includes(value);
	}

	// Basic type validation
	const baseType = paramInfo.type.split(' ')[0]?.split('<')[0]; // Extract base type

	switch (baseType) {
		case 'string':
			return typeof value === 'string';
		case 'number':
		case 'integer':
			return typeof value === 'number';
		case 'boolean':
			return typeof value === 'boolean';
		case 'array':
			return Array.isArray(value);
		case 'object':
			return typeof value === 'object' && value !== null && !Array.isArray(value);
		case 'enum':
			// Already checked above
			return true;
		default:
			// Unknown type, allow it (permissive)
			return true;
	}
}

/**
 * Applies default values to parameters
 */
export function applyDefaults(
	parameters: Record<string, unknown>,
	schemaResult: SchemaComplexityResult
): Record<string, unknown> {
	const result = { ...parameters };

	for (const param of schemaResult.parameters) {
		// Only apply defaults for optional parameters that are missing
		if (!param.required && !(param.name in result) && param.default !== undefined) {
			result[param.name] = param.default;
		}
	}

	return result;
}
