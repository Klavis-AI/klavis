/**
 * @fileoverview Age parsing utility for clinical trial eligibility criteria.
 * Parses age strings from ClinicalTrials.gov API format (e.g., "18 Years", "6 Months", "N/A")
 * and converts them to numeric years for comparison.
 *
 * @module src/mcp-server/tools/utils/ageParser
 */

/**
 * Parses an age string into a numeric value representing years.
 * Handles various formats from the ClinicalTrials.gov API.
 *
 * @param ageString - Age string to parse (e.g., "18 Years", "6 Months", "21 Days", "N/A")
 * @returns Numeric age in years, or null if unparseable
 *
 * @example
 * parseAge("18 Years") // returns 18
 * parseAge("6 Months") // returns 0.5
 * parseAge("21 Days") // returns ~0.058
 * parseAge("N/A") // returns null
 * parseAge(undefined) // returns null
 */
export function parseAge(ageString?: string): number | null {
  if (!ageString) return null;

  // Handle explicit N/A or similar
  if (/^(N\/A|None|Unknown|-)$/i.test(ageString.trim())) {
    return null;
  }

  // Parse formats like "18 Years", "6 Months", "21 Days"
  const match = ageString.match(/(\d+\.?\d*)\s*(Year|Month|Week|Day)/i);
  if (!match || !match[1] || !match[2]) return null;

  const value = parseFloat(match[1]);
  const unit = match[2].toLowerCase();

  if (unit.startsWith('year')) return value;
  if (unit.startsWith('month')) return value / 12;
  if (unit.startsWith('week')) return value / 52;
  if (unit.startsWith('day')) return value / 365;

  return null;
}

/**
 * Checks if a patient age falls within a study's eligibility age range.
 *
 * @param minimumAge - Study minimum age string (e.g., "18 Years")
 * @param maximumAge - Study maximum age string (e.g., "65 Years", "N/A")
 * @param patientAge - Patient age in years
 * @returns Object with eligibility status and reason
 *
 * @example
 * checkAgeEligibility("18 Years", "65 Years", 45)
 * // returns { eligible: true, reason: "Age 45 within eligible range (18-65)" }
 *
 * checkAgeEligibility("21 Years", "N/A", 18)
 * // returns { eligible: false, reason: "Below minimum age (21)" }
 */
export function checkAgeEligibility(
  minimumAge: string | undefined,
  maximumAge: string | undefined,
  patientAge: number,
): { eligible: boolean; reason: string } {
  const minAge = parseAge(minimumAge);
  const maxAge = parseAge(maximumAge);

  if (minAge !== null && patientAge < minAge) {
    return { eligible: false, reason: `Below minimum age (${minAge})` };
  }

  if (maxAge !== null && patientAge > maxAge) {
    return { eligible: false, reason: `Above maximum age (${maxAge})` };
  }

  const minDisplay = minAge !== null ? minAge.toString() : 'any';
  const maxDisplay = maxAge !== null ? maxAge.toString() : 'any';

  return {
    eligible: true,
    reason: `Age ${patientAge} within eligible range (${minDisplay}-${maxDisplay})`,
  };
}
