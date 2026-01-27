/**
 * @fileoverview Barrel file for tool utilities.
 * Re-exports all utility functions and types for easy import.
 *
 * @module src/mcp-server/tools/utils
 */

// Age parsing utilities
export { parseAge, checkAgeEligibility } from './ageParser.js';

// Eligibility checking utilities
export {
  checkSexEligibility,
  checkHealthyVolunteerEligibility,
} from './eligibilityCheckers.js';

// Study extraction utilities
export {
  extractRelevantLocations,
  extractContactInfo,
  extractStudyDetails,
  type StudyLocation,
  type StudyContact,
  type StudyDetails,
  type PatientLocation,
} from './studyExtractors.js';

// Study ranking utilities
export {
  getPhaseWeight,
  rankStudies,
  calculateMatchScore,
  type RankableStudy,
} from './studyRanking.js';

// Tool definition and handler utilities
export type {
  ToolDefinition,
  ToolAnnotations,
  SdkContext,
} from './toolDefinition.js';

export { createMcpToolHandler } from './toolHandlerFactory.js';
