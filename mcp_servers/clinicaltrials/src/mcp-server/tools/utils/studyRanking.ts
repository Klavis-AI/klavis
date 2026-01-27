/**
 * @fileoverview Study ranking utilities for clinical trial matching.
 * Provides functions to calculate weights and rank studies based on
 * various criteria including phase, enrollment, and location relevance.
 *
 * @module src/mcp-server/tools/utils/studyRanking
 */

/**
 * Interface for a rankable study (must have match score, locations, and details).
 */
export interface RankableStudy {
  matchScore: number;
  locations: Array<{ distance?: number | undefined }>;
  studyDetails: {
    phase?: string[] | undefined;
    enrollmentCount?: number | undefined;
  };
}

/**
 * Calculates a numeric weight for a study phase.
 * Higher phases (more advanced trials) receive higher weights.
 *
 * @param phases - Array of phase strings (e.g., ["Phase 3", "Phase 4"])
 * @returns Numeric weight representing the highest phase (0-4)
 *
 * @example
 * getPhaseWeight(["Phase 3"]) // returns 3
 * getPhaseWeight(["Phase 1", "Phase 2"]) // returns 2 (max)
 * getPhaseWeight(["N/A"]) // returns 0
 * getPhaseWeight(undefined) // returns 0
 */
export function getPhaseWeight(phases?: string[]): number {
  if (!phases || phases.length === 0) return 0;

  const phaseMap: Record<string, number> = {
    'Phase 4': 4,
    'Phase 3': 3,
    'Phase 2': 2,
    'Phase 1': 1,
    'N/A': 0,
    'Not Applicable': 0,
  };

  // Return the maximum phase weight from the array
  return Math.max(...phases.map((p) => phaseMap[p] ?? 0));
}

/**
 * Ranks an array of studies based on multiple criteria.
 * Sorting priority: matchScore → location count → phase → enrollment count.
 *
 * @param studies - Array of studies to rank
 * @returns Sorted array with highest-ranked studies first
 *
 * @example
 * rankStudies([study1, study2, study3])
 * // returns studies sorted by relevance
 */
export function rankStudies<T extends RankableStudy>(studies: T[]): T[] {
  return [...studies].sort((a, b) => {
    // Primary: Match score (higher is better)
    if (a.matchScore !== b.matchScore) {
      return b.matchScore - a.matchScore;
    }

    // Secondary: Number of nearby locations (more is better)
    const aLocationCount = a.locations.length;
    const bLocationCount = b.locations.length;
    if (aLocationCount !== bLocationCount) {
      return bLocationCount - aLocationCount;
    }

    // Tertiary: Study phase (later phase = more established)
    const aPhase = getPhaseWeight(a.studyDetails.phase);
    const bPhase = getPhaseWeight(b.studyDetails.phase);
    if (aPhase !== bPhase) {
      return bPhase - aPhase;
    }

    // Quaternary: Enrollment count (higher = more capacity)
    const aEnrollment = a.studyDetails.enrollmentCount ?? 0;
    const bEnrollment = b.studyDetails.enrollmentCount ?? 0;
    return bEnrollment - aEnrollment;
  });
}

/**
 * Calculates a match score based on eligibility checks.
 * Each successful check adds points to the total score.
 *
 * @param checks - Array of eligibility check results
 * @returns Total match score (0-100)
 *
 * @example
 * calculateMatchScore([
 *   { eligible: true },
 *   { eligible: true },
 *   { eligible: true },
 * ])
 * // returns 75 (3 checks × 25 points each)
 */
export function calculateMatchScore(
  checks: Array<{ eligible: boolean }>,
): number {
  const pointsPerCheck = 25;
  const passedChecks = checks.filter((c) => c.eligible).length;
  return passedChecks * pointsPerCheck;
}
