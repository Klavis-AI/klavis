import { describe, it, expect } from 'vitest';
import {
	parseSchemaResponse,
	convertJsonSchemaToZod,
} from '../../src/server/gradio-endpoint-connector.js';
import { stripImageContentFromResult } from '../../src/server/utils/gradio-result-processor.js';
import { z } from 'zod';
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';

describe('parseSchemaResponse', () => {
	const endpointId = 'endpoint1';
	const subdomain = 'test-subdomain';

	describe('object format schema', () => {
		it('should parse object format schema and return all tools', () => {
			const schemaOne = {
				evalstate_shuttle_jaguarinfer: {
					type: 'object',
					properties: {
						prompt: {
							type: 'string',
						},
						seed: {
							type: 'number',
							description: 'numeric value between 0 and 2147483647',
						},
						randomize_seed: {
							type: 'boolean',
						},
						width: {
							type: 'number',
							description: 'numeric value between 256 and 2048',
						},
						height: {
							type: 'number',
							description: 'numeric value between 256 and 2048',
						},
						num_inference_steps: {
							type: 'number',
							description: 'numeric value between 1 and 50',
						},
					},
					description: '',
				},
			};

			const result = parseSchemaResponse(schemaOne, endpointId, subdomain);

			expect(result).toHaveLength(1);
			expect(result[0]).toBeDefined();
			expect(result[0]?.name).toBe('evalstate_shuttle_jaguarinfer');
			expect(result[0]?.description).toBe('');
			expect(result[0]?.inputSchema).toEqual({
				type: 'object',
				properties: {
					prompt: {
						type: 'string',
					},
					seed: {
						type: 'number',
						description: 'numeric value between 0 and 2147483647',
					},
					randomize_seed: {
						type: 'boolean',
					},
					width: {
						type: 'number',
						description: 'numeric value between 256 and 2048',
					},
					height: {
						type: 'number',
						description: 'numeric value between 256 and 2048',
					},
					num_inference_steps: {
						type: 'number',
						description: 'numeric value between 1 and 50',
					},
				},
				description: '',
			});
		});

		it('should return all tools when multiple tools exist', () => {
			const schema = {
				some_other_tool: {
					type: 'object',
					properties: { test: { type: 'string' } },
				},
				evalstate_shuttle_jaguarinfer: {
					type: 'object',
					properties: { prompt: { type: 'string' } },
				},
				another_tool: {
					type: 'object',
					properties: { data: { type: 'string' } },
				},
			};

			const result = parseSchemaResponse(schema, endpointId, subdomain);

			expect(result).toHaveLength(3);
			expect(result[0]?.name).toBe('some_other_tool');
			expect(result[1]?.name).toBe('evalstate_shuttle_jaguarinfer');
			expect(result[2]?.name).toBe('another_tool');
		});

		it('should return all tools in order', () => {
			const schema = {
				first_tool: {
					type: 'object',
					properties: { test: { type: 'string' } },
				},
				last_tool: {
					type: 'object',
					properties: { data: { type: 'string' } },
				},
			};

			const result = parseSchemaResponse(schema, endpointId, subdomain);

			expect(result).toHaveLength(2);
			expect(result[0]?.name).toBe('first_tool');
			expect(result[1]?.name).toBe('last_tool');
		});
	});

	describe('array format schema', () => {
		it('should parse array format schema and return all tools', () => {
			const schemaTwo = [
				{
					name: 'OmniParser_v2_process',
					description: '',
					inputSchema: {
						type: 'object',
						properties: {
							image_input: {
								title: 'ImageData',
								type: 'string',
								format: 'a http or https url to a file',
							},
							box_threshold: {
								type: 'number',
								description: 'numeric value between 0.01 and 1.0',
								default: 0.05,
							},
							iou_threshold: {
								type: 'number',
								description: 'numeric value between 0.01 and 1.0',
								default: 0.1,
							},
							use_paddleocr: {
								type: 'boolean',
								default: true,
							},
							imgsz: {
								type: 'number',
								description: 'numeric value between 640 and 1920',
								default: 640,
							},
						},
					},
				},
			];

			const result = parseSchemaResponse(schemaTwo, endpointId, subdomain);

			expect(result).toHaveLength(1);
			expect(result[0]).toBeDefined();
			expect(result[0]?.name).toBe('OmniParser_v2_process');
			expect(result[0]?.description).toBe('');
			expect(result[0]?.inputSchema).toEqual({
				type: 'object',
				properties: {
					image_input: {
						title: 'ImageData',
						type: 'string',
						format: 'a http or https url to a file',
					},
					box_threshold: {
						type: 'number',
						description: 'numeric value between 0.01 and 1.0',
						default: 0.05,
					},
					iou_threshold: {
						type: 'number',
						description: 'numeric value between 0.01 and 1.0',
						default: 0.1,
					},
					use_paddleocr: {
						type: 'boolean',
						default: true,
					},
					imgsz: {
						type: 'number',
						description: 'numeric value between 640 and 1920',
						default: 640,
					},
				},
			});
		});

		it('should filter out invalid tools in array format', () => {
			const schema = [
				{ name: 'valid_tool', inputSchema: { type: 'object' } },
				{ name: 'missing_schema' }, // missing inputSchema
				{ inputSchema: { type: 'object' } }, // missing name
				{ name: 123, inputSchema: { type: 'object' } }, // invalid name type
				null, // null entry
				{ name: 'another_valid_tool', inputSchema: { type: 'object' } },
			];

			const result = parseSchemaResponse(schema, endpointId, subdomain);

			// Should return only valid tools
			expect(result).toHaveLength(2);
			expect(result[0]?.name).toBe('valid_tool');
			expect(result[1]?.name).toBe('another_valid_tool');
		});

		it('should return all tools in array format', () => {
			const schema = [
				{ name: 'first_tool', inputSchema: { type: 'object' } },
				{ name: 'infer_tool', inputSchema: { type: 'object' } },
				{ name: 'last_tool', inputSchema: { type: 'object' } },
			];

			const result = parseSchemaResponse(schema, endpointId, subdomain);

			expect(result).toHaveLength(3);
			expect(result[0]?.name).toBe('first_tool');
			expect(result[1]?.name).toBe('infer_tool');
			expect(result[2]?.name).toBe('last_tool');
		});

		it('should include tools with Lambda in name during parsing', () => {
			const schema = [
				{ name: 'normal_tool', inputSchema: { type: 'object' } },
				{ name: 'tool<Lambda>Function', inputSchema: { type: 'object' } },
				{ name: '<Lambda>_tool', inputSchema: { type: 'object' } },
				{ name: 'FLUX_1_Kontext_Dev_<lambda>', inputSchema: { type: 'object' } },
			];

			const result = parseSchemaResponse(schema, endpointId, subdomain);

			// parseSchemaResponse doesn't filter, it returns all valid tools
			expect(result).toHaveLength(4);
			expect(result[0]?.name).toBe('normal_tool');
			expect(result[1]?.name).toBe('tool<Lambda>Function');
			expect(result[2]?.name).toBe('<Lambda>_tool');
			expect(result[3]?.name).toBe('FLUX_1_Kontext_Dev_<lambda>');
		});
	});

	describe('error handling', () => {
		it('should throw error for invalid schema format', () => {
			expect(() => parseSchemaResponse('string', endpointId, subdomain)).toThrow(
				'Invalid schema format: expected array or object'
			);

			expect(() => parseSchemaResponse(123, endpointId, subdomain)).toThrow(
				'Invalid schema format: expected array or object'
			);

			expect(() => parseSchemaResponse(null, endpointId, subdomain)).toThrow(
				'Invalid schema format: expected array or object'
			);
		});

		it('should throw error when no tools found in object format', () => {
			expect(() => parseSchemaResponse({}, endpointId, subdomain)).toThrow('No tools found in schema');
		});

		it('should throw error when no valid tools found in array format', () => {
			const invalidSchema = [{ name: 'missing_schema' }, { inputSchema: { type: 'object' } }, null];

			expect(() => parseSchemaResponse(invalidSchema, endpointId, subdomain)).toThrow('No tools found in schema');
		});
	});
});

describe('stripImageContentFromResult', () => {
	const baseOptions = { toolName: 'test-tool', outwardFacingName: 'gr1_test' } as const;

	it('should return original result when disabled', () => {
		const result = {
			isError: false,
			content: [{ type: 'text', text: 'hello' }],
		} as CallToolResult;

		const filtered = stripImageContentFromResult(result, { ...baseOptions, enabled: false });

		expect(filtered).toBe(result);
	});

	it('should remove image-only content and add fallback text', () => {
		const result = {
			isError: false,
			content: [
				{
					type: 'image',
					mimeType: 'image/png',
					data: 'base64data',
				},
			],
		} as CallToolResult;

		const filtered = stripImageContentFromResult(result, { ...baseOptions, enabled: true });

		expect(filtered).not.toBe(result);
		expect(filtered.content).toHaveLength(1);
		expect(filtered.content?.[0]).toEqual({
			type: 'text',
			text: 'Image content omitted due to client configuration (no_image_content=true).',
		});
	});

	it('should preserve non-image content while removing images', () => {
		const result = {
			isError: false,
			content: [
				{ type: 'text', text: 'keep me' },
				{ type: 'image', mimeType: 'image/png', data: 'base64data' },
			],
		} as CallToolResult;

		const filtered = stripImageContentFromResult(result, { ...baseOptions, enabled: true });

		expect(filtered.content).toHaveLength(1);
		expect(filtered.content?.[0]).toEqual({ type: 'text', text: 'keep me' });
		// Ensure original payload remains unchanged for type safety consumers
		expect(result.content).toHaveLength(2);
	});

	it('should preserve structuredContent through spread operator', () => {
		const result = {
			isError: false,
			content: [
				{ type: 'text', text: 'hello' },
				{ type: 'image', mimeType: 'image/png', data: 'base64data' },
			],
			structuredContent: { url: 'https://example.com/result' },
		} as CallToolResult;

		const filtered = stripImageContentFromResult(result, { ...baseOptions, enabled: true });

		// Content should be filtered
		expect(filtered.content).toHaveLength(1);
		expect(filtered.content?.[0]).toEqual({ type: 'text', text: 'hello' });

		// structuredContent should be preserved via spread operator
		expect((filtered as any).structuredContent).toEqual({ url: 'https://example.com/result' });
	});
});

describe('convertJsonSchemaToZod', () => {
	it('should convert string type with file format', () => {
		const jsonSchema = {
			title: 'ImageData',
			type: 'string',
			format: 'a http or https url to a file',
		};

		const zodSchema = convertJsonSchemaToZod(jsonSchema);

		// Should be a string schema with description
		expect(zodSchema instanceof z.ZodString).toBe(true);
		expect((zodSchema as z.ZodString)._def.description).toBe('a http or https url to a file');

		// Test validation
		expect(zodSchema.parse('https://example.com/image.jpg')).toBe('https://example.com/image.jpg');
		expect(zodSchema.parse('/path/to/file.png')).toBe('/path/to/file.png');
	});

	it('should convert number type with default', () => {
		const jsonSchema = {
			type: 'number',
			description: 'numeric value between 0.01 and 1.0',
			default: 0.05,
		};

		const zodSchema = convertJsonSchemaToZod(jsonSchema);

		expect(zodSchema instanceof z.ZodDefault).toBe(true);
		expect((zodSchema as z.ZodDefault<z.ZodNumber>)._def.defaultValue()).toBe(0.05);
		expect((zodSchema as z.ZodDefault<z.ZodNumber>)._def.innerType._def.description).toBe(
			'numeric value between 0.01 and 1.0'
		);
	});

	it('should convert boolean type with default', () => {
		const jsonSchema = {
			type: 'boolean',
			default: true,
		};

		const zodSchema = convertJsonSchemaToZod(jsonSchema);

		expect(zodSchema instanceof z.ZodDefault).toBe(true);
		expect((zodSchema as z.ZodDefault<z.ZodBoolean>)._def.defaultValue()).toBe(true);
	});

	it('should skip default when skipDefault is true', () => {
		const jsonSchema = {
			type: 'number',
			default: 100,
		};

		const zodSchema = convertJsonSchemaToZod(jsonSchema, true);

		// Should not be wrapped in ZodDefault
		expect(zodSchema instanceof z.ZodNumber).toBe(true);
		expect(zodSchema instanceof z.ZodDefault).toBe(false);
	});

	it('should handle FileData objects', () => {
		const jsonSchema = {
			title: 'FileData',
			type: 'string',
			default: {
				path: '/tmp/file.jpg',
				url: 'https://example.com/file.jpg',
				size: 1024,
				orig_name: 'file.jpg',
				mime_type: 'image/jpeg',
			},
		};

		const zodSchema = convertJsonSchemaToZod(jsonSchema);

		// Should create object schema for FileData
		expect(zodSchema instanceof z.ZodDefault).toBe(true);
		const innerSchema = (zodSchema as z.ZodDefault<z.ZodObject<z.ZodRawShape>>)._def.innerType;
		expect(innerSchema instanceof z.ZodObject).toBe(true);

		// Test parsing
		const fileData = {
			path: '/some/path.png',
			url: 'https://example.com/path.png',
		};
		expect(zodSchema.parse(fileData)).toMatchObject(fileData);

		// Test default value
		expect(zodSchema.parse(undefined)).toMatchObject({
			path: '/tmp/file.jpg',
			url: 'https://example.com/file.jpg',
			size: 1024,
			orig_name: 'file.jpg',
			mime_type: 'image/jpeg',
		});
	});

	it('should extract URL from object default for non-FileData strings', () => {
		const jsonSchema = {
			type: 'string',
			default: {
				url: 'https://example.com/default.jpg',
				other: 'data',
			},
		};

		const zodSchema = convertJsonSchemaToZod(jsonSchema);

		expect(zodSchema instanceof z.ZodDefault).toBe(true);
		expect((zodSchema as z.ZodDefault<z.ZodString>)._def.defaultValue()).toBe('https://example.com/default.jpg');
	});

	it('should handle array and object types', () => {
		const arraySchema = { type: 'array' };
		const objectSchema = { type: 'object' };

		const zodArray = convertJsonSchemaToZod(arraySchema);
		const zodObject = convertJsonSchemaToZod(objectSchema);

		expect(zodArray instanceof z.ZodArray).toBe(true);
		expect(zodObject instanceof z.ZodObject).toBe(true);
	});

	it('should handle unknown types as any', () => {
		const unknownSchema = { type: 'unknown' };
		const noTypeSchema = {};

		const zodUnknown = convertJsonSchemaToZod(unknownSchema);
		const zodNoType = convertJsonSchemaToZod(noTypeSchema);

		expect(zodUnknown instanceof z.ZodAny).toBe(true);
		expect(zodNoType instanceof z.ZodAny).toBe(true);
	});
});
