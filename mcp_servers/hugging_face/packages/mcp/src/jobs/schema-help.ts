import { z } from 'zod';

/**
 * Type utilities and help generation for Zod schemas
 * Provides introspection and documentation generation for command arguments
 */

export type AnyZodType = z.ZodType<unknown, z.ZodTypeDef, unknown>;

export interface FieldDetails {
	key: string;
	description?: string;
	typeLabel: string;
	isOptional: boolean;
	isNullable: boolean;
	defaultValue?: unknown;
}

/**
 * Unwrap optional/default/nullable wrappers to find the core type definition.
 */
export function unwrapType(zodType: AnyZodType): {
	baseType: AnyZodType;
	isOptional: boolean;
	isNullable: boolean;
	defaultValue?: unknown;
} {
	let current = zodType;
	let isOptional = false;
	let isNullable = false;
	let defaultValue: unknown;

	while (true) {
		if (current instanceof z.ZodOptional) {
			isOptional = true;
			current = current._def.innerType as AnyZodType;
			continue;
		}

		if (current instanceof z.ZodDefault) {
			isOptional = true;
			defaultValue = current._def.defaultValue();
			current = current._def.innerType as AnyZodType;
			continue;
		}

		if (current instanceof z.ZodNullable) {
			isNullable = true;
			current = current._def.innerType as AnyZodType;
			continue;
		}

		if (current instanceof z.ZodEffects) {
			current = current._def.schema as AnyZodType;
			continue;
		}

		break;
	}

	return { baseType: current, isOptional, isNullable, defaultValue };
}

function isZodType(value: unknown): value is AnyZodType {
	return value instanceof z.ZodType;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Generate a human-readable type label from a Zod type definition
 */
export function labelForType(zodType: AnyZodType): string {
	if (zodType instanceof z.ZodString) {
		return 'string';
	}

	if (zodType instanceof z.ZodNumber) {
		return 'number';
	}

	if (zodType instanceof z.ZodBoolean) {
		return 'boolean';
	}

	if (zodType instanceof z.ZodEnum) {
		return `enum(${(zodType.options as readonly string[]).join(', ')})`;
	}

	if (zodType instanceof z.ZodLiteral) {
		return `literal(${JSON.stringify(zodType.value)})`;
	}

	if (zodType instanceof z.ZodArray) {
		return `array<${labelForType(zodType._def.type as AnyZodType)}>`;
	}

	if (zodType instanceof z.ZodRecord) {
		return `record<string, ${labelForType(zodType._def.valueType as AnyZodType)}>`;
	}

	if (zodType instanceof z.ZodUnion) {
		const options = zodType._def.options as readonly AnyZodType[];
		const labels = options.map((opt) => labelForType(opt));
		return labels.join(' | ');
	}

	if (zodType instanceof z.ZodObject) {
		return 'object';
	}

	// Fallback for any unexpected types
	return zodType.constructor.name.replace(/^Zod/, '').toLowerCase();
}

/**
 * Extract field details from a Zod object schema
 * Useful for custom help formatting or validation messages
 */
export function extractFieldDetails(schema: AnyZodType): FieldDetails[] {
	if (!(schema instanceof z.ZodObject)) {
		return [];
	}

	const shape = schema.shape as Record<string, unknown>;
	const keys = Object.keys(shape);
	const details: FieldDetails[] = [];

	for (const key of keys) {
		const candidate = shape[key];
		if (!isZodType(candidate)) {
			continue;
		}
		const fieldSchema: AnyZodType = candidate;
		const { baseType, isOptional, isNullable, defaultValue } = unwrapType(fieldSchema);
		details.push({
			key: String(key),
			description: fieldSchema.description ?? baseType.description,
			typeLabel: labelForType(baseType),
			isOptional,
			isNullable,
			defaultValue,
		});
	}

	return details;
}

/**
 * Format a default value for display in help text
 */
export function formatDefaultValue(value: unknown): string | undefined {
	if (value === undefined) {
		return undefined;
	}

	if (typeof value === 'string') {
		return `"${value}"`;
	}

	if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') {
		return String(value);
	}

	if (typeof value === 'symbol') {
		return value.description ? `Symbol(${value.description})` : 'Symbol()';
	}

	if (value === null) {
		return 'null';
	}

	if (Array.isArray(value)) {
		try {
			return JSON.stringify(value);
		} catch {
			return '[unserializable]';
		}
	}

	if (isPlainObject(value)) {
		try {
			return JSON.stringify(value);
		} catch {
			return '[unserializable]';
		}
	}

	return '[unsupported]';
}

/**
 * Generate command-specific help text from a Zod schema
 * Main entry point for help generation
 */
export function formatCommandHelp(commandName: string, schema: z.ZodTypeAny): string {
	if (!schema) {
		return `No help available for '${commandName}'.`;
	}

	const fields = extractFieldDetails(schema as AnyZodType);

	if (fields.length === 0) {
		return `No help available for '${commandName}'.`;
	}

	const header = `# Command help: ${commandName}\n\nArguments:\n`;
	const lines = fields.map((field) => {
		const parts: string[] = [];
		parts.push(field.isOptional ? 'optional' : 'required');
		parts.push(field.typeLabel);
		if (field.isNullable) {
			parts.push('nullable');
		}

		const defaultValue = formatDefaultValue(field.defaultValue);
		if (defaultValue !== undefined) {
			parts.push(`default: ${defaultValue}`);
		}

		const meta = parts.join(', ');
		const description = field.description ?? 'No description provided.';

		return `- \`${field.key}\` (${meta}): ${description}`;
	});

	return header + lines.join('\n');
}
