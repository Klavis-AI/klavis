/**
 * @fileoverview Complete, declarative definition for the 'clinicaltrials_search_studies' tool.
 * Searches for clinical trials using queries and filters with pagination support.
 *
 * @module src/mcp-server/tools/definitions/clinicaltrials-search-studies.tool
 */

import type { ContentBlock } from '@modelcontextprotocol/sdk/types.js';
import { container } from 'tsyringe';
import { z } from 'zod';

import { ClinicalTrialsProvider } from '@/container/tokens.js';
import type {
  SdkContext,
  ToolAnnotations,
  ToolDefinition,
} from '@/mcp-server/tools/utils/toolDefinition.js';
import { withToolAuth } from '@/mcp-server/transports/auth/lib/withAuth.js';
import type { IClinicalTrialsProvider } from '@/services/clinical-trials-gov/core/IClinicalTrialsProvider.js';
import { PagedStudiesSchema } from '@/services/clinical-trials-gov/types.js';
import { logger, type RequestContext } from '@/utils/index.js';

/** --------------------------------------------------------- */
/** Programmatic tool name (must be unique). */
const TOOL_NAME = 'clinicaltrials_search_studies';
/** --------------------------------------------------------- */

/** Human-readable title used by UIs. */
const TOOL_TITLE = 'Search Clinical Trials';
/** --------------------------------------------------------- */

/**
 * LLM-facing description of the tool.
 */
const TOOL_DESCRIPTION =
  'Searches for clinical trial studies from ClinicalTrials.gov using queries and filters. Supports pagination, sorting, and advanced filtering.';
/** --------------------------------------------------------- */

/** UI/behavior hints for clients. */
const TOOL_ANNOTATIONS: ToolAnnotations = {
  readOnlyHint: true,
  idempotentHint: true,
  openWorldHint: true, // Accesses external ClinicalTrials.gov API
};
/** --------------------------------------------------------- */

//
// Schemas (input and output)
// --------------------------

const InputSchema = z
  .object({
    query: z
      .string()
      .optional()
      .describe(
        'General search query for conditions, interventions, sponsors, or other terms.',
      ),
    filter: z
      .string()
      .optional()
      .describe(
        'Advanced filter expression using the ClinicalTrials.gov filter syntax.',
      ),
    pageSize: z
      .number()
      .int()
      .min(1)
      .max(200)
      .default(10)
      .describe(
        'Number of studies to return per page (1-200). Defaults to 10.',
      ),
    pageToken: z
      .string()
      .optional()
      .describe('Token for retrieving the next page of results.'),
    sort: z
      .string()
      .optional()
      .describe(
        'Sort order specification (e.g., "LastUpdateDate:desc", "EnrollmentCount").',
      ),
    fields: z
      .array(z.string())
      .optional()
      .describe(
        'Specific fields to return (reduces payload size). Example: ["NCTId", "BriefTitle", "OverallStatus"].',
      ),
    country: z
      .string()
      .optional()
      .describe('Filter studies by country (e.g., "United States", "Canada").'),
    state: z
      .string()
      .optional()
      .describe(
        'Filter studies by state or province (e.g., "California", "Ontario").',
      ),
    city: z
      .string()
      .optional()
      .describe('Filter studies by city (e.g., "New York", "Toronto").'),
  })
  .describe('Input parameters for searching clinical trial studies.');

const OutputSchema = z.object({
  pagedStudies: PagedStudiesSchema,
});

type SearchStudiesInput = z.infer<typeof InputSchema>;
type SearchStudiesOutput = z.infer<typeof OutputSchema>;

//
// Pure business logic (no try/catch; throw McpError on failure)
// -------------------------------------------------------------

/**
 * Searches for clinical studies using a combination of queries and filters.
 * Supports pagination, sorting, and advanced filtering.
 */
async function searchStudiesLogic(
  input: SearchStudiesInput,
  appContext: RequestContext,
  _sdkContext: SdkContext,
): Promise<SearchStudiesOutput> {
  logger.debug('Executing searchStudiesLogic', {
    ...appContext,
    toolInput: input,
  });

  const provider = container.resolve<IClinicalTrialsProvider>(
    ClinicalTrialsProvider,
  );

  const pagedStudies = await provider.listStudies(
    {
      ...(input.query && { query: input.query }),
      ...(input.filter && { filter: input.filter }),
      pageSize: input.pageSize,
      ...(input.pageToken && { pageToken: input.pageToken }),
      ...(input.sort && { sort: input.sort }),
      ...(input.fields && { fields: input.fields }),
      ...(input.country && { country: input.country }),
      ...(input.state && { state: input.state }),
      ...(input.city && { city: input.city }),
    },
    appContext,
  );

  logger.info(
    `Successfully searched studies: ${pagedStudies.studies?.length ?? 0} results`,
    {
      ...appContext,
      totalCount: pagedStudies.totalCount,
    },
  );

  return { pagedStudies };
}

/**
 * Formats a concise human-readable summary.
 */
function responseFormatter(result: SearchStudiesOutput): ContentBlock[] {
  const { pagedStudies } = result;
  const studyCount = pagedStudies.studies?.length ?? 0;
  const totalCount = pagedStudies.totalCount;
  const hasMore = !!pagedStudies.nextPageToken;

  const summary = [
    `Found ${studyCount} ${studyCount === 1 ? 'study' : 'studies'}`,
    totalCount ? `of ${totalCount} total` : null,
    hasMore ? '(more pages available)' : null,
  ]
    .filter(Boolean)
    .join(' ');

  const studyList = (pagedStudies.studies ?? [])
    .slice(0, 5)
    .map((s) => {
      const nctId = s.protocolSection?.identificationModule?.nctId ?? 'Unknown';
      const title =
        s.protocolSection?.identificationModule?.briefTitle ?? 'No title';
      const status =
        s.protocolSection?.statusModule?.overallStatus ?? 'Unknown status';
      return `• ${nctId}: ${title}\n  Status: ${status}`;
    })
    .join('\n');

  const moreStudies = studyCount > 5 ? `\n...and ${studyCount - 5} more` : '';

  const pagination = hasMore
    ? `\n\nNext page token: ${pagedStudies.nextPageToken}`
    : '';

  return [
    {
      type: 'text',
      text: `${summary}\n\n${studyList}${moreStudies}${pagination}`,
    },
  ];
}

/**
 * The complete tool definition for searching clinical trial studies.
 */
export const searchStudiesTool: ToolDefinition<
  typeof InputSchema,
  typeof OutputSchema
> = {
  name: TOOL_NAME,
  title: TOOL_TITLE,
  description: TOOL_DESCRIPTION,
  inputSchema: InputSchema,
  outputSchema: OutputSchema,
  annotations: TOOL_ANNOTATIONS,
  logic: withToolAuth(['tool:clinicaltrials:read'], searchStudiesLogic),
  responseFormatter,
};
