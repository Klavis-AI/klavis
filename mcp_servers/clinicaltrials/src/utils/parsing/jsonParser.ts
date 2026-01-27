/**
 * @fileoverview Provides a utility class for parsing potentially partial JSON strings.
 * It wraps the 'partial-json' npm library and includes functionality to handle
 * optional <think>...</think> blocks often found at the beginning of LLM outputs.
 * @module src/utils/parsing/jsonParser
 */
import {
  Allow as PartialJsonAllow,
  parse as parsePartialJson,
} from 'partial-json';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  type RequestContext,
  logger,
  requestContextService,
} from '@/utils/index.js';

/**
 * Enum mirroring `partial-json`'s `Allow` constants. These specify
 * what types of partial JSON structures are permissible during parsing.
 * They can be combined using bitwise OR (e.g., `Allow.STR | Allow.OBJ`).
 *
 * The available properties are:
 * - `STR`: Allow partial string.
 * - `NUM`: Allow partial number.
 * - `ARR`: Allow partial array.
 * - `OBJ`: Allow partial object.
 * - `NULL`: Allow partial null.
 * - `BOOL`: Allow partial boolean.
 * - `NAN`: Allow partial NaN. (Note: Standard JSON does not support NaN)
 * - `INFINITY`: Allow partial Infinity. (Note: Standard JSON does not support Infinity)
 * - `_INFINITY`: Allow partial -Infinity. (Note: Standard JSON does not support -Infinity)
 * - `INF`: Allow both partial Infinity and -Infinity.
 * - `SPECIAL`: Allow all special values (NaN, Infinity, -Infinity).
 * - `ATOM`: Allow all atomic values (strings, numbers, booleans, null, special values).
 * - `COLLECTION`: Allow all collection values (objects, arrays).
 * - `ALL`: Allow all value types to be partial (default for `partial-json`'s parse).
 * @see {@link https://github.com/promplate/partial-json-parser-js} for more details.
 */
export const Allow = PartialJsonAllow;

/**
 * Regular expression to find a <think> block at the start of a string.
 * Captures content within <think>...</think> (Group 1) and the rest of the string (Group 2).
 * @private
 */
const thinkBlockRegex = /^<think>([\s\S]*?)<\/think>\s*([\s\S]*)$/;

/**
 * Utility class for parsing potentially partial JSON strings.
 * Wraps the 'partial-json' library for robust JSON parsing, handling
 * incomplete structures and optional <think> blocks from LLMs.
 */
export class JsonParser {
  /**
   * Parses a JSON string, which may be partial or prefixed with a <think> block.
   * If a <think> block is present, its content is logged, and parsing proceeds on the
   * remainder. Uses 'partial-json' to handle incomplete JSON.
   *
   * @template T The expected type of the parsed JSON object. Defaults to `any`.
   * @param jsonString - The JSON string to parse.
   * @param allowPartial - Bitwise OR combination of `Allow` constants specifying permissible
   *   partial JSON types. Defaults to `Allow.ALL`.
   * @param context - Optional `RequestContext` for logging and error correlation.
   * @returns The parsed JavaScript value.
   * @throws {McpError} If the string is empty after processing or if `partial-json` fails.
   */
  parse<T = unknown>(
    jsonString: string,
    allowPartial: number = Allow.ALL,
    context?: RequestContext,
  ): T {
    let stringToParse = jsonString;
    const match = jsonString.match(thinkBlockRegex);

    if (match) {
      const thinkContent = match[1]?.trim() ?? '';
      const restOfString = match[2] ?? '';

      const logContext =
        context ||
        requestContextService.createRequestContext({
          operation: 'JsonParser.thinkBlock',
        });
      if (thinkContent) {
        logger.debug('LLM <think> block detected and logged.', {
          ...logContext,
          thinkContent,
        });
      } else {
        logger.debug('Empty LLM <think> block detected.', logContext);
      }
      stringToParse = restOfString;
    }

    stringToParse = stringToParse.trim();

    if (!stringToParse) {
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        'JSON string is empty after removing <think> block and trimming.',
        context,
      );
    }

    try {
      return parsePartialJson(stringToParse, allowPartial) as T;
    } catch (e: unknown) {
      const error = e as Error;
      const errorLogContext =
        context ||
        requestContextService.createRequestContext({
          operation: 'JsonParser.parseError',
        });
      logger.error('Failed to parse JSON content.', {
        ...errorLogContext,
        errorDetails: error.message,
        contentAttempted: stringToParse.substring(0, 200),
      });

      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        `Failed to parse JSON: ${error.message}`,
        {
          ...context,
          originalContentSample:
            stringToParse.substring(0, 200) +
            (stringToParse.length > 200 ? '...' : ''),
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }
}

/**
 * Singleton instance of the `JsonParser`.
 * Use this instance to parse JSON strings, with support for partial JSON and <think> blocks.
 * @example
 * ```typescript
 * import { jsonParser, Allow, requestContextService } from './utils';
 * const context = requestContextService.createRequestContext({ operation: 'TestJsonParsing' });
 *
 * const fullJson = '{"key": "value"}';
 * const parsedFull = jsonParser.parse(fullJson, Allow.ALL, context);
 * console.log(parsedFull); // Output: { key: 'value' }
 *
 * const partialObject = '<think>This is a thought.</think>{"key": "value", "arr": [1,';
 * try {
 *   const parsedPartial = jsonParser.parse(partialObject, undefined, context);
 *   console.log(parsedPartial);
 * } catch (e) {
 *   console.error("Parsing partial object failed:", e);
 * }
 * ```
 */
export const jsonParser = new JsonParser();
