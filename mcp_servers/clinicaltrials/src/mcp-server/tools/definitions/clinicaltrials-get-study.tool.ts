/**
 * @fileoverview Complete, declarative definition for the 'clinicaltrials_get_study' tool.
 * Fetches one or more clinical studies from ClinicalTrials.gov by their NCT IDs.
 *
 * @module src/mcp-server/tools/definitions/clinicaltrials-get-study.tool
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
import {
  StudySchema,
  type Study,
} from '@/services/clinical-trials-gov/types.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { logger, type RequestContext } from '@/utils/index.js';

/** --------------------------------------------------------- */
/** Programmatic tool name (must be unique). */
const TOOL_NAME = 'clinicaltrials_get_study';
/** --------------------------------------------------------- */

/** Human-readable title used by UIs. */
const TOOL_TITLE = 'Get Clinical Study';
/** --------------------------------------------------------- */

/**
 * LLM-facing description of the tool.
 */
const TOOL_DESCRIPTION =
  'Fetches one or more clinical trial studies from ClinicalTrials.gov by their NCT ID(s). Returns full study data or concise summaries.';
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

/**
 * Zod schema for a summarized study, containing only essential fields for a concise overview.
 */
const StudySummarySchema = z
  .object({
    nctId: z.string().optional().describe('The NCT identifier of the study.'),
    title: z.string().optional().describe('The official title of the study.'),
    briefSummary: z
      .string()
      .optional()
      .describe('A brief summary of the study purpose.'),
    overallStatus: z
      .string()
      .optional()
      .describe('The current recruitment status of the study.'),
    conditions: z
      .array(z.string())
      .optional()
      .describe('List of medical conditions being studied.'),
    interventions: z
      .array(
        z.object({
          name: z.string().optional().describe('Name of the intervention.'),
          type: z.string().optional().describe('Type of intervention.'),
        }),
      )
      .optional()
      .describe('List of interventions being tested.'),
    leadSponsor: z
      .string()
      .optional()
      .describe('The lead sponsor organization.'),
  })
  .passthrough()
  .describe('Concise summary of a clinical trial study.');

const InputSchema = z
  .object({
    nctIds: z
      .union([
        z
          .string()
          .regex(/^[Nn][Cc][Tt]\d{8}$/, 'NCT ID must be 8 digits')
          .describe('A single NCT ID (e.g., "NCT12345678").'),
        z
          .array(
            z.string().regex(/^[Nn][Cc][Tt]\d{8}$/, 'NCT ID must be 8 digits'),
          )
          .min(1, 'At least one NCT ID is required.')
          .max(5, 'Maximum 5 NCT IDs allowed per request.')
          .describe('An array of up to 5 NCT IDs.'),
      ])
      .describe(
        'A single NCT ID (e.g., "NCT12345678") or an array of up to 5 NCT IDs to fetch.',
      ),
    summaryOnly: z
      .boolean()
      .default(false)
      .describe(
        'If true, returns concise summaries. If false (default), returns full study data.',
      ),
  })
  .describe('Input parameters for fetching clinical trial studies.');

const OutputSchema = z
  .object({
    studies: z
      .array(z.union([StudySchema, StudySummarySchema]))
      .describe('Array of full study data or summaries.'),
    errors: z
      .array(
        z.object({
          nctId: z.string().describe('The NCT ID that failed.'),
          error: z.string().describe('Error message for this NCT ID.'),
        }),
      )
      .optional()
      .describe('List of errors encountered for specific NCT IDs.'),
  })
  .describe('Response containing study data and any errors.');

type GetStudyInput = z.infer<typeof InputSchema>;
type StudySummary = z.infer<typeof StudySummarySchema>;
type GetStudyOutput = z.infer<typeof OutputSchema>;

//
// Pure business logic (no try/catch; throw McpError on failure)
// -------------------------------------------------------------

/**
 * Extracts a concise summary from a full study object.
 */
function createStudySummary(study: Study): StudySummary {
  return {
    nctId: study.protocolSection?.identificationModule?.nctId,
    title: study.protocolSection?.identificationModule?.officialTitle,
    briefSummary: study.protocolSection?.descriptionModule?.briefSummary,
    overallStatus: study.protocolSection?.statusModule?.overallStatus,
    conditions: study.protocolSection?.conditionsModule?.conditions,
    interventions:
      study.protocolSection?.armsInterventionsModule?.interventions?.map(
        (i) => ({
          name: i.name,
          type: i.type,
        }),
      ),
    leadSponsor:
      study.protocolSection?.sponsorCollaboratorsModule?.leadSponsor?.name,
  };
}

/**
 * Fetches one or more clinical studies from ClinicalTrials.gov by their NCT IDs.
 */
async function getStudyLogic(
  input: GetStudyInput,
  appContext: RequestContext,
  _sdkContext: SdkContext,
): Promise<GetStudyOutput> {
  const nctIds = Array.isArray(input.nctIds) ? input.nctIds : [input.nctIds];

  logger.debug(`Executing getStudyLogic for NCT IDs: ${nctIds.join(', ')}`, {
    ...appContext,
    toolInput: input,
  });

  const provider = container.resolve<IClinicalTrialsProvider>(
    ClinicalTrialsProvider,
  );

  const studies: (Study | StudySummary)[] = [];
  const errors: { nctId: string; error: string }[] = [];

  const studyPromises = nctIds.map(async (nctId) => {
    try {
      const study = await provider.fetchStudy(nctId, appContext);

      logger.info(`Successfully fetched study ${nctId}`, { ...appContext });

      if (input.summaryOnly) {
        logger.debug(`Creating summary for study ${nctId}`, { ...appContext });
        studies.push(createStudySummary(study));
      } else {
        studies.push(study);
      }
    } catch (error) {
      const errorMessage =
        error instanceof McpError
          ? error.message
          : 'An unexpected error occurred';
      logger.warning(`Failed to fetch study ${nctId}: ${errorMessage}`, {
        ...appContext,
        nctId,
        error,
      });
      errors.push({ nctId, error: errorMessage });
    }
  });

  await Promise.all(studyPromises);

  // If all studies failed, throw an error
  if (studies.length === 0 && errors.length > 0) {
    throw new McpError(
      JsonRpcErrorCode.ServiceUnavailable,
      `Failed to fetch any studies. Errors: ${errors.map((e) => `${e.nctId}: ${e.error}`).join('; ')}`,
      { errors },
    );
  }

  const result: GetStudyOutput = { studies };
  if (errors.length > 0) {
    result.errors = errors;
  }

  return result;
}

/**
 * Formats the full tool output as a JSON string for the LLM.
 * The LLM requires the complete data, not just a human-readable summary.
 */
function responseFormatter(result: GetStudyOutput): ContentBlock[] {
  return [
    {
      type: 'text',
      text: JSON.stringify(result, null, 2),
    },
  ];
}

/**
 * The complete tool definition for fetching clinical trial studies.
 */
export const getStudyTool: ToolDefinition<
  typeof InputSchema,
  typeof OutputSchema
> = {
  name: TOOL_NAME,
  title: TOOL_TITLE,
  description: TOOL_DESCRIPTION,
  inputSchema: InputSchema,
  outputSchema: OutputSchema,
  annotations: TOOL_ANNOTATIONS,
  logic: withToolAuth(['tool:clinicaltrials:read'], getStudyLogic),
  responseFormatter,
};
