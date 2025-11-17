import { Blob } from "node:buffer";
import { z, ZodTypeAny } from "zod";

type Schema =
  | {
      type?: string;
      required?: boolean;
      enum?: any;
      properties?: Record<string, Schema | Schema[]>;
      requiredProperties?: string[];
      items?: Schema | Schema[];
      format?: string;
      minimum?: number;
      maximum?: number;
      exclusiveMinimum?: boolean;
      exclusiveMaximum?: boolean;
      minLength?: any;
      maxLength?: any;
      pattern?: any;
      minItems?: number;
      maxItems?: number;
      default?: unknown;
    }
  | Record<string, unknown>;

function panic(error: unknown): never {
  throw error;
}

// WebFile polyfill implementation (based on fetch-blob)
class WebFile extends Blob {
  private _name: string;
  private _lastModified: number;
  // Add webkitRelativePath to match File interface
  public webkitRelativePath: string = "";

  constructor(
    init: (Blob | ArrayBuffer)[],
    name: string = panic(
      new TypeError("File constructor requires name argument")
    ),
    options: FilePropertyBag = {}
  ) {
    if (arguments.length < 2) {
      throw new TypeError(
        `Failed to construct 'File': 2 arguments required, but only ${arguments.length} present.`
      );
    }
    super(init, options);
    this._lastModified = 0;
    this._name = "";
    // Simulate WebIDL type casting for NaN value in lastModified option.
    const lastModified =
      options.lastModified === undefined
        ? Date.now()
        : Number(options.lastModified);
    if (!Number.isNaN(lastModified)) {
      this._lastModified = lastModified;
    }
    this._name = String(name);
  }

  get name(): string {
    return this._name;
  }

  get lastModified(): number {
    return this._lastModified;
  }

  get [Symbol.toStringTag](): string {
    return "File";
  }

  static [Symbol.hasInstance](object: unknown): boolean {
    return (
      !!object &&
      object instanceof Blob &&
      /^(File)$/.test(String((object as any)[Symbol.toStringTag]))
    );
  }
}

const File = typeof global.File === "undefined" ? WebFile : global.File;

const ANY = z.any();
const ANY_OPT = ANY.optional();
const BOOLEAN = z.boolean();
const BOOLEAN_OPT = BOOLEAN.optional();
const DATE = z.coerce.date();
const DATE_OPT = DATE.optional();
const FILE = z.instanceof(File);
const FILE_OPT = FILE.optional();
const NULL = z.null();
const NULL_OPT = NULL.optional();
const RECORD = z.record(z.any());
const RECORD_WITH_DEFAULT = RECORD.default({});
const RECORD_OPT = RECORD.optional();
const STRING = z.string();
const NUMBER = z.number();
const INTEGER = z.number().int();

export function dataSchemaArrayToZod(schemas: any) {
  const firstSchema = dataSchemaToZod(schemas[0]);
  if (!schemas[1]) {
    return firstSchema;
  }
  const secondSchema = dataSchemaToZod(schemas[1]);
  const zodSchemas: any = [firstSchema, secondSchema];
  for (const schema of schemas.slice(2)) {
    zodSchemas.push(dataSchemaToZod(schema));
  }
  return z.union(zodSchemas);
}

function getEnumSchema(enumList: any, type: string): ZodTypeAny {
  const zodSchema = z.enum(enumList.map(String));
  if (type === "string") return zodSchema;
  return zodSchema.transform(Number);
}

export function dataSchemaToZod(schema: Schema): ZodTypeAny {
  if (!("type" in schema) || Object.keys(schema).length === 0) {
    return schema.required ? ANY : ANY_OPT;
  }

  switch (schema.type) {
    case "null":
      return schema.required ? NULL : NULL_OPT;

    case "boolean":
      return schema.required ? BOOLEAN : BOOLEAN_OPT;

    case "enum<string>":
      const strEnumSchema = getEnumSchema(schema.enum, "string");
      return schema.required ? strEnumSchema : strEnumSchema.optional();

    case "enum<number>":
    case "enum<integer>":
      const numEnumSchema = getEnumSchema(schema.enum, "number");
      return schema.required ? numEnumSchema : numEnumSchema.optional();

    case "file":
      return schema.required ? FILE : FILE_OPT;

    case "any":
      return schema.required ? ANY : ANY_OPT;

    case "string":
      if ("enum" in schema && Array.isArray(schema.enum)) {
        return schema.required
          ? z.enum((schema as any).enum)
          : z.enum((schema as any).enum).optional();
      }

      if (schema.format === "binary") {
        return schema.required ? FILE : FILE_OPT;
      }

      let stringSchema = STRING;

      if (schema.minLength !== undefined) {
        stringSchema = stringSchema.min(schema.minLength);
      }
      if (schema.maxLength !== undefined) {
        stringSchema = stringSchema.max(schema.maxLength);
      }
      if (schema.pattern !== undefined) {
        stringSchema = stringSchema.regex(new RegExp(schema.pattern));
      }

      switch (schema.format) {
        case "email":
          stringSchema = stringSchema.email();
          break;
        case "uri":
        case "url":
          stringSchema = stringSchema.url();
          break;
        case "uuid":
          stringSchema = stringSchema.uuid();
          break;
        case "date-time":
          return schema.required ? DATE : DATE_OPT;
      }

      if ("default" in schema) {
        return schema.required
          ? stringSchema.default(schema.default as any)
          : stringSchema.optional().default(schema.default as any);
      }

      return schema.required ? stringSchema : stringSchema.optional();

    case "number":
    case "integer":
      if ("enum" in schema && Array.isArray(schema.enum)) {
        const numEnumSchema = getEnumSchema(schema.enum, schema.type);
        return schema.required ? numEnumSchema : numEnumSchema.optional();
      }

      let numberSchema = schema.type === "integer" ? INTEGER : NUMBER;

      if (typeof schema.minimum === "number") {
        numberSchema = numberSchema.min(schema.minimum);
      }
      if (typeof schema.maximum === "number") {
        numberSchema = numberSchema.max(schema.maximum);
      }
      if (
        schema.exclusiveMinimum !== undefined &&
        typeof schema.minimum === "number"
      ) {
        numberSchema = numberSchema.gt(schema.minimum);
      }
      if (
        schema.exclusiveMaximum !== undefined &&
        typeof schema.maximum === "number"
      ) {
        numberSchema = numberSchema.lt(schema.maximum);
      }

      return schema.required ? numberSchema : numberSchema.optional();

    case "array":
      let itemSchema;
      let arraySchema: any = z.any().array();
      if (Array.isArray(schema.items)) {
        itemSchema = dataSchemaArrayToZod(schema.items);
        if (schema.items.length > 1) {
          arraySchema = itemSchema;
        } else {
          arraySchema = itemSchema.array();
        }
      } else {
        itemSchema = dataSchemaToZod(schema.items as any);
        arraySchema = itemSchema.array();
      }
      if (schema.minItems !== undefined) {
        arraySchema = arraySchema.min(schema.minItems);
      }
      if (schema.maxItems !== undefined) {
        arraySchema = arraySchema.max(schema.maxItems);
      }
      return schema.required ? arraySchema : arraySchema.optional();
    case "object":
      const shape: Record<string, ZodTypeAny> = {};
      // Handle both 'required' and 'requiredProperties' for compatibility
      const requiredProperties = schema.requiredProperties || (schema as any).required;
      const requiredPropertiesSet = new Set(
        Array.isArray(requiredProperties) ? requiredProperties : []
      );
      
      // Special handling for the case where properties are arrays with individual required flags
      const properties = schema.properties as any;
      for (const [key, propSchema] of Object.entries(properties)) {
        let zodPropSchema: ZodTypeAny;
        let isRequired = false;
        
        if (Array.isArray(propSchema)) {
          // Handle array-wrapped schemas (from OpenAPI conversion)
          zodPropSchema = dataSchemaArrayToZod(propSchema);
          // Check if any schema in the array has required: true
          isRequired = propSchema.some((s: any) => s.required === true);
        } else {
          zodPropSchema = dataSchemaToZod(propSchema as Schema);
          isRequired = (propSchema as any).required === true;
        }
        
        // Check if property is in the required list OR has individual required flag
        const shouldBeRequired = requiredPropertiesSet.has(key) || isRequired;
        
        shape[key] = shouldBeRequired ? zodPropSchema : zodPropSchema.optional();
      }
      
      if (Object.keys(shape).length === 0) {
        return schema.required ? RECORD_WITH_DEFAULT : RECORD_OPT;
      }
      return schema.required ? z.object(shape) : z.object(shape).optional();
    default:
      return ANY;
  }
}
