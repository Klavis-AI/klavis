/**
 * @fileoverview Provides a utility class for parsing YAML strings.
 * It wraps the 'js-yaml' library and includes functionality to handle
 * optional <think>...</think> blocks often found at the beginning of LLM outputs.
 * @module src/utils/parsing/yamlParser
 */
import * as yaml from 'js-yaml';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  type RequestContext,
  logger,
  requestContextService,
} from '@/utils/index.js';

/**
 * Regular expression to find a <think> block at the start of a string.
 * Captures content within <think>...</think> (Group 1) and the rest of the string (Group 2).
 * @private
 */
const thinkBlockRegex = /^<think>([\s\S]*?)<\/think>\s*([\s\S]*)$/;

/**
 * Utility class for parsing YAML strings.
 * Wraps the 'js-yaml' library for robust YAML parsing and handles
 * optional <think> blocks from LLMs.
 */
export class YamlParser {
  /**
   * Parses a YAML string, which may be prefixed with a <think> block.
   * If a <think> block is present, its content is logged, and parsing proceeds on the
   * remainder.
   *
   * @template T The expected type of the parsed YAML object. Defaults to `any`.
   * @param yamlString - The YAML string to parse.
   * @param context - Optional `RequestContext` for logging and error correlation.
   * @returns The parsed JavaScript object.
   * @throws {McpError} If the string is empty after processing or if parsing fails.
   */
  parse<T = unknown>(yamlString: string, context?: RequestContext): T {
    let stringToParse = yamlString;
    const match = yamlString.match(thinkBlockRegex);

    if (match) {
      const thinkContent = match[1]?.trim() ?? '';
      const restOfString = match[2] ?? '';

      const logContext =
        context ||
        requestContextService.createRequestContext({
          operation: 'YamlParser.thinkBlock',
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
        'YAML string is empty after removing <think> block and trimming.',
        context,
      );
    }

    try {
      return yaml.load(stringToParse) as T;
    } catch (e: unknown) {
      const error = e as Error;
      const errorLogContext =
        context ||
        requestContextService.createRequestContext({
          operation: 'YamlParser.parseError',
        });
      logger.error('Failed to parse YAML content.', {
        ...errorLogContext,
        errorDetails: error.message,
        contentAttempted: stringToParse.substring(0, 200),
      });

      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        `Failed to parse YAML: ${error.message}`,
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
 * Singleton instance of the `YamlParser`.
 * Use this instance to parse YAML strings, with support for <think> blocks.
 * @example
 * ```typescript
 * import { yamlParser, requestContextService } from './utils';
 * const context = requestContextService.createRequestContext({ operation: 'TestYamlParsing' });
 *
 * const yml = 'key: value';
 * const parsedYml = yamlParser.parse(yml, context);
 * console.log(parsedYml); // Output: { key: 'value' }
 *
 * const ymlWithThink = '<think>This is a thought.</think>key: value';
 * const parsedWithThink = yamlParser.parse(ymlWithThink, context);
 * console.log(parsedWithThink); // Output: { key: 'value' }
 * ```
 */
export const yamlParser = new YamlParser();
