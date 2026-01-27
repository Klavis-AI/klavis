/**
 * @fileoverview Provides utility functions for parsing natural language date strings
 * into Date objects or detailed parsing results using the `chrono-node` library.
 * @module src/utils/parsing/dateParser
 */
import * as chrono from 'chrono-node';

import { JsonRpcErrorCode } from '@/types-global/errors.js';
import { ErrorHandler, type RequestContext, logger } from '@/utils/index.js';

/**
 * Parses a natural language date string into a JavaScript Date object.
 * Uses `chrono.parseDate` for lenient parsing of various date formats.
 *
 * @param text - The natural language date string to parse.
 * @param context - The request context for logging and error tracking.
 * @param refDate - Optional reference date for parsing relative dates. Defaults to current date/time.
 * @returns A promise resolving with a Date object or `null` if parsing fails.
 * @throws {McpError} If an unexpected error occurs during parsing.
 * @private
 */
export async function parseDateString(
  text: string,
  context: RequestContext,
  refDate?: Date,
): Promise<Date | null> {
  const operation = 'parseDateString';
  const logContext = { ...context, operation, inputText: text, refDate };
  logger.debug(`Attempting to parse date string: "${text}"`, logContext);

  return await ErrorHandler.tryCatch(
    () => {
      const parsedDate = chrono.parseDate(text, refDate, { forwardDate: true });
      if (parsedDate) {
        logger.debug(
          `Successfully parsed "${text}" to ${parsedDate.toISOString()}`,
          logContext,
        );
        return parsedDate;
      } else {
        logger.warning(`Failed to parse date string: "${text}"`, logContext);
        return null;
      }
    },
    {
      operation,
      context: logContext,
      input: { text, refDate },
      errorCode: JsonRpcErrorCode.ParseError,
    },
  );
}

/**
 * Parses a natural language date string and returns detailed parsing results.
 * Provides more information than just the Date object, including matched text and components.
 *
 * @param text - The natural language date string to parse.
 * @param context - The request context for logging and error tracking.
 * @param refDate - Optional reference date for parsing relative dates. Defaults to current date/time.
 * @returns A promise resolving with an array of `chrono.ParsedResult` objects. Empty if no dates found.
 * @throws {McpError} If an unexpected error occurs during parsing.
 * @private
 */
export async function parseDateStringDetailed(
  text: string,
  context: RequestContext,
  refDate?: Date,
): Promise<chrono.ParsedResult[]> {
  const operation = 'parseDateStringDetailed';
  const logContext = { ...context, operation, inputText: text, refDate };
  logger.debug(
    `Attempting detailed parse of date string: "${text}"`,
    logContext,
  );

  return await ErrorHandler.tryCatch(
    () => {
      const results = chrono.parse(text, refDate, { forwardDate: true });
      logger.debug(
        `Detailed parse of "${text}" resulted in ${results.length} result(s)`,
        logContext,
      );
      return results;
    },
    {
      operation,
      context: logContext,
      input: { text, refDate },
      errorCode: JsonRpcErrorCode.ParseError,
    },
  );
}

/**
 * An object providing date parsing functionalities.
 *
 * @example
 * ```typescript
 * import { dateParser, requestContextService } from './utils'; // Assuming utils/index.js exports these
 * const context = requestContextService.createRequestContext({ operation: 'TestDateParsing' });
 *
 * async function testParsing() {
 *   const dateObj = await dateParser.parseDate("next Friday at 3pm", context);
 *   if (dateObj) {
 *     console.log("Parsed Date:", dateObj.toISOString());
 *   }
 *
 *   const detailedResults = await dateParser.parse("Meeting on 2024-12-25 and another one tomorrow", context);
 *   detailedResults.forEach(result => {
 *     console.log("Detailed Result:", result.text, result.start.date());
 *   });
 * }
 * testParsing();
 * ```
 */
export const dateParser = {
  /**
   * Parses a natural language date string and returns detailed parsing results
   * from `chrono-node`.
   * @param text - The natural language date string to parse.
   * @param context - The request context for logging and error tracking.
   * @param refDate - Optional reference date for parsing relative dates.
   * @returns A promise resolving with an array of `chrono.ParsedResult` objects.
   */
  parse: parseDateStringDetailed,
  /**
   * Parses a natural language date string into a single JavaScript Date object.
   * @param text - The natural language date string to parse.
   * @param context - The request context for logging and error tracking.
   * @param refDate - Optional reference date for parsing relative dates.
   * @returns A promise resolving with a Date object or `null`.
   */
  parseDate: parseDateString,
};
