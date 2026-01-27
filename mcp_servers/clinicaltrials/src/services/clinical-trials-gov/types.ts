/**
 * @fileoverview Defines the TypeScript types for the ClinicalTrials.gov API.
 * These types are based on the API's OpenAPI specification and are used
 * throughout the server for type safety and data consistency.
 * @module src/services/clinical-trials-gov/types
 */

import { z } from 'zod';

/**
 * Zod schema for a single clinical study, mirroring the ClinicalTrials.gov API structure.
 * This provides runtime validation and serves as the single source of truth for the Study type.
 */
export const StudySchema = z
  .object({
    protocolSection: z
      .object({
        identificationModule: z
          .object({
            nctId: z.string(),
            orgStudyIdInfo: z
              .object({ id: z.string().optional() })
              .passthrough()
              .optional(),
            organization: z
              .object({
                fullName: z.string().optional(),
                class: z.string().optional(),
              })
              .passthrough()
              .optional(),
            briefTitle: z.string().optional(),
            officialTitle: z.string().optional(),
            acronym: z.string().optional(),
          })
          .passthrough()
          .optional(),
        statusModule: z
          .object({
            overallStatus: z.string().optional(),
            lastKnownStatus: z.string().optional(),
            startDateStruct: z
              .object({
                date: z.string().optional(),
                type: z.string().optional(),
              })
              .passthrough()
              .optional(),
            primaryCompletionDateStruct: z
              .object({
                date: z.string().optional(),
                type: z.string().optional(),
              })
              .passthrough()
              .optional(),
            completionDateStruct: z
              .object({
                date: z.string().optional(),
                type: z.string().optional(),
              })
              .passthrough()
              .optional(),
            lastUpdatePostDateStruct: z
              .object({
                date: z.string().optional(),
                type: z.string().optional(),
              })
              .passthrough()
              .optional(),
          })
          .passthrough()
          .optional(),
        sponsorCollaboratorsModule: z
          .object({
            responsibleParty: z
              .object({ type: z.string().optional() })
              .passthrough()
              .optional(),
            leadSponsor: z
              .object({
                name: z.string().optional(),
                class: z.string().optional(),
              })
              .passthrough()
              .optional(),
            collaborators: z
              .array(
                z
                  .object({
                    name: z.string().optional(),
                    class: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
          })
          .passthrough()
          .optional(),
        descriptionModule: z
          .object({
            briefSummary: z.string().optional(),
            detailedDescription: z.string().optional(),
          })
          .passthrough()
          .optional(),
        conditionsModule: z
          .object({
            conditions: z.array(z.string()).optional(),
            keywords: z.array(z.string()).optional(),
          })
          .passthrough()
          .optional(),
        armsInterventionsModule: z
          .object({
            arms: z
              .array(
                z
                  .object({
                    name: z.string().optional(),
                    type: z.string().optional(),
                    description: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            interventions: z
              .array(
                z
                  .object({
                    type: z.string().optional(),
                    name: z.string().optional(),
                    description: z.string().optional(),
                    armNames: z.array(z.string()).optional(),
                  })
                  .passthrough(),
              )
              .optional(),
          })
          .passthrough()
          .optional(),
        designModule: z
          .object({
            studyType: z.string().optional(),
            phases: z.array(z.string()).optional(),
            designInfo: z
              .object({
                allocation: z.string().optional(),
                interventionModel: z.string().optional(),
                primaryPurpose: z.string().optional(),
                maskingInfo: z
                  .object({ masking: z.string().optional() })
                  .passthrough()
                  .optional(),
              })
              .passthrough()
              .optional(),
          })
          .passthrough()
          .optional(),
        eligibilityModule: z
          .object({
            eligibilityCriteria: z.string().optional(),
            healthyVolunteers: z.boolean().optional(),
            sex: z.string().optional(),
            minimumAge: z.string().optional(),
            stdAges: z.array(z.string()).optional(),
          })
          .passthrough()
          .optional(),
        contactsLocationsModule: z
          .object({
            locations: z
              .array(
                z
                  .object({
                    city: z.string().optional(),
                    state: z.string().optional(),
                    country: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
          })
          .passthrough()
          .optional(),
        oversightModule: z
          .object({
            oversightHasDmc: z.boolean().optional(),
            isFdaRegulatedDrug: z.boolean().optional(),
            isFdaRegulatedDevice: z.boolean().optional(),
          })
          .passthrough()
          .optional(),
        outcomesModule: z
          .object({
            primaryOutcomes: z
              .array(
                z
                  .object({
                    measure: z.string().optional(),
                    description: z.string().optional(),
                    timeFrame: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            secondaryOutcomes: z
              .array(
                z
                  .object({
                    measure: z.string().optional(),
                    description: z.string().optional(),
                    timeFrame: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            otherOutcomes: z
              .array(
                z
                  .object({
                    measure: z.string().optional(),
                    description: z.string().optional(),
                    timeFrame: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
          })
          .passthrough()
          .optional(),
        referencesModule: z
          .object({
            references: z
              .array(
                z
                  .object({
                    pmid: z.string().optional(),
                    type: z.string().optional(),
                    citation: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
          })
          .passthrough()
          .optional(),
        ipdSharingStatementModule: z
          .object({
            ipdSharing: z.string().optional(),
            description: z.string().optional(),
            url: z.string().optional(),
          })
          .passthrough()
          .optional(),
      })
      .passthrough()
      .optional(),
    derivedSection: z
      .object({
        miscInfoModule: z
          .object({
            versionHolder: z.string().optional(),
          })
          .passthrough()
          .optional(),
        conditionBrowseModule: z
          .object({
            meshes: z
              .array(
                z
                  .object({
                    id: z.string().optional(),
                    term: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            ancestors: z
              .array(
                z
                  .object({
                    id: z.string().optional(),
                    term: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            browseLeaves: z
              .array(
                z
                  .object({
                    id: z.string().optional(),
                    name: z.string().optional(),
                    asFound: z.string().optional(),
                    relevance: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            browseBranches: z
              .array(
                z
                  .object({
                    abbrev: z.string().optional(),
                    name: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
          })
          .passthrough()
          .optional(),
        interventionBrowseModule: z
          .object({
            meshes: z
              .array(
                z
                  .object({
                    id: z.string().optional(),
                    term: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            ancestors: z
              .array(
                z
                  .object({
                    id: z.string().optional(),
                    term: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            browseLeaves: z
              .array(
                z
                  .object({
                    id: z.string().optional(),
                    name: z.string().optional(),
                    relevance: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
            browseBranches: z
              .array(
                z
                  .object({
                    abbrev: z.string().optional(),
                    name: z.string().optional(),
                  })
                  .passthrough(),
              )
              .optional(),
          })
          .passthrough()
          .optional(),
      })
      .passthrough()
      .optional(),
    hasResults: z.boolean().optional(),
  })
  .passthrough();

/**
 * Represents a single clinical study, based on the ClinicalTrials.gov API structure.
 * This type is inferred from the StudySchema to ensure consistency.
 */
export type Study = z.infer<typeof StudySchema>;

/**
 * Represents a paged list of studies.
 */
export type PagedStudies = {
  studies: Study[];
  nextPageToken?: string | undefined;
  totalCount?: number | undefined;
  [key: string]: unknown;
};

/**
 * Zod schema for a paged list of studies.
 * Note: Uses explicit type annotation to prevent TypeScript inference issues with deeply nested schemas.
 */
export const PagedStudiesSchema: z.ZodType<PagedStudies> = z
  .object({
    studies: z.array(StudySchema),
    nextPageToken: z.string().optional(),
    totalCount: z.number().optional(),
  })
  .passthrough();

/**
 * Represents a node in the study data model tree.
 */
export interface FieldNode {
  name: string;
  type: string;
  description: string;
  children?: FieldNode[];
}

/**

 * Represents the possible status values for a study.
 */
export enum Status {
  ActiveNotRecruiting = 'ACTIVE_NOT_RECRUITING',
  Completed = 'COMPLETED',
  EnrollingByInvitation = 'ENROLLING_BY_INVITATION',
  NotYetRecruiting = 'NOT_YET_RECRUITING',
  Recruiting = 'RECRUITING',
  Suspended = 'SUSPENDED',
  Terminated = 'TERMINATED',
  Withdrawn = 'WITHDRAWN',
  Unknown = 'UNKNOWN',
}

/**
 * Zod schema for study metadata (lightweight version of Study).
 */
export const StudyMetadataSchema = z.object({
  nctId: z.string(),
  title: z.string().optional(),
  status: z.string().optional(),
  startDate: z.string().optional(),
  completionDate: z.string().optional(),
  lastUpdateDate: z.string().optional(),
});

/**
 * Represents study metadata without full details.
 */
export type StudyMetadata = z.infer<typeof StudyMetadataSchema>;
