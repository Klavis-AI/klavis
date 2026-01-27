/**
 * @fileoverview Complete, declarative definition for the 'clinicaltrials_compare_studies' tool.
 * Performs side-by-side comparison of 2-5 clinical trials.
 *
 * @module src/mcp-server/tools/definitions/clinicaltrials-compare-studies.tool
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
import type { Study } from '@/services/clinical-trials-gov/types.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { logger, type RequestContext } from '@/utils/index.js';

/** --------------------------------------------------------- */
/** Programmatic tool name (must be unique). */
const TOOL_NAME = 'clinicaltrials_compare_studies';
/** --------------------------------------------------------- */

/** Human-readable title used by UIs. */
const TOOL_TITLE = 'Compare Clinical Studies';
/** --------------------------------------------------------- */

/**
 * LLM-facing description of the tool.
 */
const TOOL_DESCRIPTION =
  'Performs side-by-side comparison of 2-5 clinical trial studies. Compares eligibility criteria, design, interventions, outcomes, sponsors, and other key aspects.';
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
 * Defines the comparison categories available.
 */
const ComparisonCategorySchema = z.enum([
  'eligibility',
  'design',
  'interventions',
  'outcomes',
  'sponsors',
  'locations',
  'status',
  'all',
]);

const InputSchema = z
  .object({
    nctIds: z
      .array(z.string().regex(/^[Nn][Cc][Tt]\d{8}$/, 'NCT ID must be 8 digits'))
      .min(2, 'At least 2 NCT IDs are required for comparison.')
      .max(5, 'Maximum 5 NCT IDs allowed for comparison.')
      .describe('An array of 2-5 NCT IDs to compare.'),
    compareFields: z
      .union([
        ComparisonCategorySchema.describe(
          'A single comparison category to analyze.',
        ),
        z
          .array(ComparisonCategorySchema)
          .min(1)
          .describe('An array of comparison categories to analyze.'),
      ])
      .default('all')
      .describe(
        'Specify which aspects to compare: eligibility, design, interventions, outcomes, sponsors, locations, status, or all.',
      ),
  })
  .describe('Input parameters for comparing clinical trial studies.');

const StudyComparisonSchema = z
  .object({
    nctId: z.string().describe('The NCT identifier.'),
    title: z.string().optional().describe('The study title.'),
    eligibility: z
      .object({
        criteria: z.string().optional().describe('Eligibility criteria text.'),
        sex: z.string().optional().describe('Sex requirement.'),
        minimumAge: z.string().optional().describe('Minimum age.'),
        healthyVolunteers: z
          .boolean()
          .optional()
          .describe('Accepts healthy volunteers.'),
        stdAges: z
          .array(z.string())
          .optional()
          .describe('Standard age groups.'),
      })
      .optional()
      .describe('Eligibility criteria details.'),
    design: z
      .object({
        studyType: z.string().optional().describe('Type of study.'),
        phases: z.array(z.string()).optional().describe('Trial phases.'),
        allocation: z.string().optional().describe('Allocation method.'),
        interventionModel: z
          .string()
          .optional()
          .describe('Intervention model.'),
        primaryPurpose: z.string().optional().describe('Primary purpose.'),
        masking: z.string().optional().describe('Masking/blinding approach.'),
      })
      .optional()
      .describe('Study design details.'),
    interventions: z
      .array(
        z.object({
          type: z.string().optional().describe('Intervention type.'),
          name: z.string().optional().describe('Intervention name.'),
          description: z.string().optional().describe('Description.'),
        }),
      )
      .optional()
      .describe('List of interventions.'),
    outcomes: z
      .object({
        primary: z
          .array(
            z.object({
              measure: z.string().optional().describe('Outcome measure.'),
              timeFrame: z.string().optional().describe('Time frame.'),
            }),
          )
          .optional()
          .describe('Primary outcomes.'),
        secondary: z
          .array(
            z.object({
              measure: z.string().optional().describe('Outcome measure.'),
              timeFrame: z.string().optional().describe('Time frame.'),
            }),
          )
          .optional()
          .describe('Secondary outcomes.'),
      })
      .optional()
      .describe('Outcome measures.'),
    sponsors: z
      .object({
        leadSponsor: z
          .object({
            name: z.string().optional().describe('Sponsor name.'),
            class: z.string().optional().describe('Sponsor class.'),
          })
          .optional()
          .describe('Lead sponsor.'),
        collaborators: z
          .array(
            z.object({
              name: z.string().optional().describe('Collaborator name.'),
              class: z.string().optional().describe('Collaborator class.'),
            }),
          )
          .optional()
          .describe('Collaborators.'),
      })
      .optional()
      .describe('Sponsor information.'),
    locations: z
      .object({
        totalCount: z
          .number()
          .optional()
          .describe('Total number of locations.'),
        countries: z
          .array(z.string())
          .optional()
          .describe('List of countries.'),
        topCities: z
          .array(z.string())
          .optional()
          .describe('Top cities by location count.'),
      })
      .optional()
      .describe('Location summary.'),
    status: z
      .object({
        overallStatus: z.string().optional().describe('Overall status.'),
        startDate: z.string().optional().describe('Start date.'),
        completionDate: z.string().optional().describe('Completion date.'),
        lastUpdateDate: z.string().optional().describe('Last update date.'),
      })
      .optional()
      .describe('Status and timeline information.'),
  })
  .describe('Structured comparison data for a single study.');

const OutputSchema = z
  .object({
    comparisons: z
      .array(StudyComparisonSchema)
      .describe('Array of study comparisons.'),
    summary: z
      .object({
        totalStudies: z.number().describe('Number of studies compared.'),
        comparedFields: z
          .array(z.string())
          .describe('Fields that were compared.'),
        commonalities: z
          .array(z.string())
          .optional()
          .describe('Key commonalities found across studies.'),
        differences: z
          .array(z.string())
          .optional()
          .describe('Key differences found across studies.'),
      })
      .describe('Summary of the comparison.'),
    errors: z
      .array(
        z.object({
          nctId: z.string().describe('The NCT ID that failed.'),
          error: z.string().describe('Error message.'),
        }),
      )
      .optional()
      .describe('Any errors encountered during comparison.'),
  })
  .describe('Comparison results for clinical trial studies.');

type CompareStudiesInput = z.infer<typeof InputSchema>;
type StudyComparison = z.infer<typeof StudyComparisonSchema>;
type CompareStudiesOutput = z.infer<typeof OutputSchema>;

//
// Helper functions
// --------------------------

/**
 * Extracts eligibility data from a study.
 */
function extractEligibility(study: Study): StudyComparison['eligibility'] {
  const eligibility = study.protocolSection?.eligibilityModule;
  if (!eligibility) return undefined;

  return {
    criteria: eligibility.eligibilityCriteria,
    sex: eligibility.sex,
    minimumAge: eligibility.minimumAge,
    healthyVolunteers: eligibility.healthyVolunteers,
    stdAges: eligibility.stdAges,
  };
}

/**
 * Extracts design data from a study.
 */
function extractDesign(study: Study): StudyComparison['design'] {
  const design = study.protocolSection?.designModule;
  if (!design) return undefined;

  return {
    studyType: design.studyType,
    phases: design.phases,
    allocation: design.designInfo?.allocation,
    interventionModel: design.designInfo?.interventionModel,
    primaryPurpose: design.designInfo?.primaryPurpose,
    masking: design.designInfo?.maskingInfo?.masking,
  };
}

/**
 * Extracts intervention data from a study.
 */
function extractInterventions(study: Study): StudyComparison['interventions'] {
  const interventions =
    study.protocolSection?.armsInterventionsModule?.interventions;
  if (!interventions) return undefined;

  return interventions.map((i) => ({
    type: i.type,
    name: i.name,
    description: i.description,
  }));
}

/**
 * Extracts outcome measures from a study.
 */
function extractOutcomes(study: Study): StudyComparison['outcomes'] {
  const outcomes = study.protocolSection?.outcomesModule;
  if (!outcomes) return undefined;

  return {
    primary: outcomes.primaryOutcomes?.map((o) => ({
      measure: o.measure,
      timeFrame: o.timeFrame,
    })),
    secondary: outcomes.secondaryOutcomes?.map((o) => ({
      measure: o.measure,
      timeFrame: o.timeFrame,
    })),
  };
}

/**
 * Extracts sponsor information from a study.
 */
function extractSponsors(study: Study): StudyComparison['sponsors'] {
  const sponsors = study.protocolSection?.sponsorCollaboratorsModule;
  if (!sponsors) return undefined;

  return {
    leadSponsor: sponsors.leadSponsor
      ? {
          name: sponsors.leadSponsor.name,
          class: sponsors.leadSponsor.class,
        }
      : undefined,
    collaborators: sponsors.collaborators?.map((c) => ({
      name: c.name,
      class: c.class,
    })),
  };
}

/**
 * Extracts location summary from a study.
 */
function extractLocations(study: Study): StudyComparison['locations'] {
  const locations = study.protocolSection?.contactsLocationsModule?.locations;
  if (!locations || locations.length === 0) return undefined;

  const countries = [
    ...new Set(locations.map((l) => l.country).filter(Boolean)),
  ] as string[];

  const cityCount: Record<string, number> = {};
  locations.forEach((loc) => {
    if (loc.city) {
      cityCount[loc.city] = (cityCount[loc.city] ?? 0) + 1;
    }
  });

  const topCities = Object.entries(cityCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([city]) => city);

  return {
    totalCount: locations.length,
    countries,
    topCities,
  };
}

/**
 * Extracts status and timeline information from a study.
 */
function extractStatus(study: Study): StudyComparison['status'] {
  const status = study.protocolSection?.statusModule;
  if (!status) return undefined;

  return {
    overallStatus: status.overallStatus,
    startDate: status.startDateStruct?.date,
    completionDate: status.completionDateStruct?.date,
    lastUpdateDate: status.lastUpdatePostDateStruct?.date,
  };
}

/**
 * Creates a study comparison based on selected fields.
 */
function createStudyComparison(
  study: Study,
  compareFields: string[],
): StudyComparison {
  const nctId = study.protocolSection?.identificationModule?.nctId ?? 'Unknown';
  const title =
    study.protocolSection?.identificationModule?.officialTitle ??
    study.protocolSection?.identificationModule?.briefTitle;

  const comparison: StudyComparison = { nctId, title };

  const shouldInclude = (field: string) =>
    compareFields.includes('all') || compareFields.includes(field);

  if (shouldInclude('eligibility')) {
    comparison.eligibility = extractEligibility(study);
  }

  if (shouldInclude('design')) {
    comparison.design = extractDesign(study);
  }

  if (shouldInclude('interventions')) {
    comparison.interventions = extractInterventions(study);
  }

  if (shouldInclude('outcomes')) {
    comparison.outcomes = extractOutcomes(study);
  }

  if (shouldInclude('sponsors')) {
    comparison.sponsors = extractSponsors(study);
  }

  if (shouldInclude('locations')) {
    comparison.locations = extractLocations(study);
  }

  if (shouldInclude('status')) {
    comparison.status = extractStatus(study);
  }

  return comparison;
}

/**
 * Analyzes commonalities and differences across studies.
 */
function analyzeSummary(
  comparisons: StudyComparison[],
  compareFields: string[],
): CompareStudiesOutput['summary'] {
  const commonalities: string[] = [];
  const differences: string[] = [];

  // Check for common phases
  if (compareFields.includes('all') || compareFields.includes('design')) {
    const allPhases = comparisons.map((c) => c.design?.phases).filter(Boolean);
    if (allPhases.length > 0) {
      const firstPhases = allPhases[0]?.join(',');
      const allSame = allPhases.every((p) => p?.join(',') === firstPhases);
      if (allSame && firstPhases) {
        commonalities.push(`All studies are in phase: ${firstPhases}`);
      } else {
        differences.push('Studies are in different trial phases');
      }
    }
  }

  // Check for common sponsors
  if (compareFields.includes('all') || compareFields.includes('sponsors')) {
    const sponsors = comparisons
      .map((c) => c.sponsors?.leadSponsor?.name)
      .filter(Boolean);
    const uniqueSponsors = [...new Set(sponsors)];
    if (uniqueSponsors.length === 1 && sponsors.length === comparisons.length) {
      commonalities.push(`All studies sponsored by: ${uniqueSponsors[0]}`);
    } else if (uniqueSponsors.length > 1) {
      differences.push(`Different lead sponsors: ${uniqueSponsors.join(', ')}`);
    }
  }

  // Check for common status
  if (compareFields.includes('all') || compareFields.includes('status')) {
    const statuses = comparisons
      .map((c) => c.status?.overallStatus)
      .filter(Boolean);
    const uniqueStatuses = [...new Set(statuses)];
    if (uniqueStatuses.length === 1 && statuses.length === comparisons.length) {
      commonalities.push(`All studies have status: ${uniqueStatuses[0]}`);
    } else if (uniqueStatuses.length > 1) {
      differences.push(`Different statuses: ${uniqueStatuses.join(', ')}`);
    }
  }

  // Check for geographic overlap
  if (compareFields.includes('all') || compareFields.includes('locations')) {
    const allCountries = comparisons
      .map((c) => c.locations?.countries ?? [])
      .filter((countries) => countries.length > 0);

    if (allCountries.length > 1) {
      const commonCountries = allCountries.reduce((acc, countries) =>
        acc.filter((c) => countries.includes(c)),
      );

      if (commonCountries.length > 0) {
        commonalities.push(
          `Common countries: ${commonCountries.slice(0, 5).join(', ')}`,
        );
      }
    }
  }

  return {
    totalStudies: comparisons.length,
    comparedFields: compareFields,
    commonalities: commonalities.length > 0 ? commonalities : undefined,
    differences: differences.length > 0 ? differences : undefined,
  };
}

//
// Pure business logic (no try/catch; throw McpError on failure)
// -------------------------------------------------------------

/**
 * Compares 2-5 clinical studies side-by-side.
 */
async function compareStudiesLogic(
  input: CompareStudiesInput,
  appContext: RequestContext,
  _sdkContext: SdkContext,
): Promise<CompareStudiesOutput> {
  logger.debug(
    `Executing compareStudiesLogic for NCT IDs: ${input.nctIds.join(', ')}`,
    {
      ...appContext,
      toolInput: input,
    },
  );

  const provider = container.resolve<IClinicalTrialsProvider>(
    ClinicalTrialsProvider,
  );

  const compareFields = Array.isArray(input.compareFields)
    ? input.compareFields
    : [input.compareFields];

  const comparisons: StudyComparison[] = [];
  const errors: { nctId: string; error: string }[] = [];

  // Fetch all studies
  const studyPromises = input.nctIds.map(async (nctId) => {
    try {
      const study = await provider.fetchStudy(nctId, appContext);
      logger.info(`Successfully fetched study ${nctId} for comparison`, {
        ...appContext,
      });
      return { nctId, study };
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
      return null;
    }
  });

  const results = await Promise.all(studyPromises);

  // Create comparisons for successfully fetched studies
  results.forEach((result) => {
    if (result) {
      const comparison = createStudyComparison(result.study, compareFields);
      comparisons.push(comparison);
    }
  });

  // Need at least 2 studies to compare
  if (comparisons.length < 2) {
    throw new McpError(
      JsonRpcErrorCode.ValidationError,
      `Insufficient studies for comparison. Need at least 2, got ${comparisons.length}. ${errors.length > 0 ? `Errors: ${errors.map((e) => `${e.nctId}: ${e.error}`).join('; ')}` : ''}`,
      { errors, successfulFetches: comparisons.length },
    );
  }

  const summary = analyzeSummary(comparisons, compareFields);

  logger.info(`Successfully compared ${comparisons.length} studies`, {
    ...appContext,
    comparedFields: compareFields,
  });

  const result: CompareStudiesOutput = { comparisons, summary };
  if (errors.length > 0) {
    result.errors = errors;
  }

  return result;
}

/**
 * Formats the comparison with both summary analysis and full structured details.
 */
function responseFormatter(result: CompareStudiesOutput): ContentBlock[] {
  const { comparisons, summary, errors } = result;

  // Build summary section
  const summaryParts: string[] = [
    `# Comparison of ${summary.totalStudies} Clinical Trials`,
    '',
    '## Studies',
    ...comparisons.map((c) => `- **${c.nctId}**: ${c.title ?? 'No title'}`),
    '',
  ];

  if (summary.commonalities && summary.commonalities.length > 0) {
    summaryParts.push('## Commonalities');
    summaryParts.push(...summary.commonalities.map((c) => `- ${c}`));
    summaryParts.push('');
  }

  if (summary.differences && summary.differences.length > 0) {
    summaryParts.push('## Key Differences');
    summaryParts.push(...summary.differences.map((d) => `- ${d}`));
    summaryParts.push('');
  }

  if (errors && errors.length > 0) {
    summaryParts.push('## Errors');
    summaryParts.push(...errors.map((e) => `- **${e.nctId}**: ${e.error}`));
    summaryParts.push('');
  }

  summaryParts.push('---');
  summaryParts.push('');

  // Build detailed comparison sections
  const detailParts: string[] = ['## Detailed Comparison', ''];

  comparisons.forEach((comp, idx) => {
    if (idx > 0) detailParts.push('---', '');
    detailParts.push(`### ${comp.nctId}: ${comp.title ?? 'No title'}`, '');

    if (comp.status) {
      detailParts.push('**Status:**');
      detailParts.push(
        `- Overall Status: ${comp.status.overallStatus ?? 'N/A'}`,
      );
      detailParts.push(`- Start Date: ${comp.status.startDate ?? 'N/A'}`);
      detailParts.push(
        `- Completion Date: ${comp.status.completionDate ?? 'N/A'}`,
      );
      detailParts.push('');
    }

    if (comp.design) {
      detailParts.push('**Design:**');
      detailParts.push(`- Study Type: ${comp.design.studyType ?? 'N/A'}`);
      detailParts.push(`- Phases: ${comp.design.phases?.join(', ') ?? 'N/A'}`);
      detailParts.push(`- Allocation: ${comp.design.allocation ?? 'N/A'}`);
      detailParts.push(
        `- Intervention Model: ${comp.design.interventionModel ?? 'N/A'}`,
      );
      detailParts.push(
        `- Primary Purpose: ${comp.design.primaryPurpose ?? 'N/A'}`,
      );
      detailParts.push(`- Masking: ${comp.design.masking ?? 'N/A'}`);
      detailParts.push('');
    }

    if (comp.eligibility) {
      detailParts.push('**Eligibility:**');
      detailParts.push(`- Sex: ${comp.eligibility.sex ?? 'N/A'}`);
      detailParts.push(
        `- Minimum Age: ${comp.eligibility.minimumAge ?? 'N/A'}`,
      );
      detailParts.push(
        `- Healthy Volunteers: ${comp.eligibility.healthyVolunteers ?? 'N/A'}`,
      );
      if (comp.eligibility.stdAges?.length) {
        detailParts.push(
          `- Age Groups: ${comp.eligibility.stdAges.join(', ')}`,
        );
      }
      if (comp.eligibility.criteria) {
        detailParts.push(
          `- Criteria: ${comp.eligibility.criteria.substring(0, 200)}${comp.eligibility.criteria.length > 200 ? '...' : ''}`,
        );
      }
      detailParts.push('');
    }

    if (comp.interventions && comp.interventions.length > 0) {
      detailParts.push('**Interventions:**');
      comp.interventions.forEach((int) => {
        detailParts.push(`- ${int.type ?? 'Unknown'}: ${int.name ?? 'N/A'}`);
        if (int.description) {
          detailParts.push(
            `  ${int.description.substring(0, 150)}${int.description.length > 150 ? '...' : ''}`,
          );
        }
      });
      detailParts.push('');
    }

    if (comp.outcomes) {
      if (comp.outcomes.primary && comp.outcomes.primary.length > 0) {
        detailParts.push('**Primary Outcomes:**');
        comp.outcomes.primary.forEach((out) => {
          detailParts.push(`- ${out.measure ?? 'N/A'}`);
          if (out.timeFrame) {
            detailParts.push(`  Time Frame: ${out.timeFrame}`);
          }
        });
        detailParts.push('');
      }

      if (comp.outcomes.secondary && comp.outcomes.secondary.length > 0) {
        detailParts.push('**Secondary Outcomes:**');
        comp.outcomes.secondary.slice(0, 3).forEach((out) => {
          detailParts.push(`- ${out.measure ?? 'N/A'}`);
        });
        if (comp.outcomes.secondary.length > 3) {
          detailParts.push(
            `  ...and ${comp.outcomes.secondary.length - 3} more`,
          );
        }
        detailParts.push('');
      }
    }

    if (comp.sponsors) {
      detailParts.push('**Sponsors:**');
      if (comp.sponsors.leadSponsor) {
        detailParts.push(
          `- Lead: ${comp.sponsors.leadSponsor.name ?? 'N/A'} (${comp.sponsors.leadSponsor.class ?? 'N/A'})`,
        );
      }
      if (
        comp.sponsors.collaborators &&
        comp.sponsors.collaborators.length > 0
      ) {
        detailParts.push(
          `- Collaborators: ${comp.sponsors.collaborators.length}`,
        );
        comp.sponsors.collaborators.slice(0, 3).forEach((collab) => {
          detailParts.push(`  - ${collab.name ?? 'N/A'}`);
        });
        if (comp.sponsors.collaborators.length > 3) {
          detailParts.push(
            `  ...and ${comp.sponsors.collaborators.length - 3} more`,
          );
        }
      }
      detailParts.push('');
    }

    if (comp.locations) {
      detailParts.push('**Locations:**');
      detailParts.push(`- Total: ${comp.locations.totalCount ?? 0}`);
      if (comp.locations.countries?.length) {
        detailParts.push(`- Countries: ${comp.locations.countries.join(', ')}`);
      }
      if (comp.locations.topCities?.length) {
        detailParts.push(
          `- Top Cities: ${comp.locations.topCities.join(', ')}`,
        );
      }
      detailParts.push('');
    }
  });

  return [
    {
      type: 'text',
      text: [...summaryParts, ...detailParts].join('\n'),
    },
  ];
}

/**
 * The complete tool definition for comparing clinical trial studies.
 */
export const compareStudiesTool: ToolDefinition<
  typeof InputSchema,
  typeof OutputSchema
> = {
  name: TOOL_NAME,
  title: TOOL_TITLE,
  description: TOOL_DESCRIPTION,
  inputSchema: InputSchema,
  outputSchema: OutputSchema,
  annotations: TOOL_ANNOTATIONS,
  logic: withToolAuth(['tool:clinicaltrials:read'], compareStudiesLogic),
  responseFormatter,
};
