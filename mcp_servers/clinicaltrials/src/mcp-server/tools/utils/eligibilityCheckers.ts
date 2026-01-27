/**
 * @fileoverview Eligibility checking utilities for clinical trial matching.
 * Provides functions to check patient eligibility against study criteria
 * including sex, healthy volunteer status, and other demographic factors.
 *
 * @module src/mcp-server/tools/utils/eligibilityCheckers
 */

/**
 * Checks if a patient's sex matches a study's sex eligibility criteria.
 *
 * @param studySex - Study sex requirement ("All", "Female", "Male")
 * @param patientSex - Patient's biological sex
 * @returns Object with eligibility status and reason
 *
 * @example
 * checkSexEligibility("All", "Female")
 * // returns { eligible: true, reason: "Study accepts all sexes" }
 *
 * checkSexEligibility("Female", "Male")
 * // returns { eligible: false, reason: "Study only accepts Female" }
 */
export function checkSexEligibility(
  studySex: string | undefined,
  patientSex: string,
): { eligible: boolean; reason: string } {
  const normalizedStudySex = (studySex ?? 'All').toLowerCase();
  const normalizedPatientSex = patientSex.toLowerCase();

  if (normalizedStudySex === 'all') {
    return { eligible: true, reason: 'Study accepts all sexes' };
  }

  if (normalizedStudySex === normalizedPatientSex) {
    return {
      eligible: true,
      reason: `Study accepts ${patientSex}`,
    };
  }

  return {
    eligible: false,
    reason: `Study only accepts ${studySex}`,
  };
}

/**
 * Checks if a patient's healthy volunteer status matches a study's requirements.
 *
 * @param studyAcceptsHealthyVolunteers - Whether the study accepts healthy volunteers
 * @param isHealthyVolunteer - Whether the patient is a healthy volunteer
 * @returns Object with eligibility status and reason
 *
 * @example
 * checkHealthyVolunteerEligibility(false, true)
 * // returns { eligible: false, reason: "Study does not accept healthy volunteers" }
 *
 * checkHealthyVolunteerEligibility(true, false)
 * // returns { eligible: true, reason: "Study accepts participants with conditions" }
 */
export function checkHealthyVolunteerEligibility(
  studyAcceptsHealthyVolunteers: boolean | undefined,
  isHealthyVolunteer: boolean,
): { eligible: boolean; reason: string } {
  const acceptsHealthyVolunteers = studyAcceptsHealthyVolunteers ?? false;

  // If patient is a healthy volunteer but study doesn't accept them
  if (isHealthyVolunteer && !acceptsHealthyVolunteers) {
    return {
      eligible: false,
      reason: 'Study does not accept healthy volunteers',
    };
  }

  // If patient has conditions but study only accepts healthy volunteers
  // (This is rare but possible in some preventive studies)
  if (!isHealthyVolunteer && acceptsHealthyVolunteers) {
    return {
      eligible: true,
      reason: 'Study accepts participants with conditions',
    };
  }

  return {
    eligible: true,
    reason: 'Eligibility status matches study requirements',
  };
}
