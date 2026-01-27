/**
 * @fileoverview Study data extraction utilities for clinical trial tools.
 * Provides functions to extract specific information from Study objects
 * including locations, contact info, and study details.
 *
 * @module src/mcp-server/tools/utils/studyExtractors
 */

import type { Study } from '@/services/clinical-trials-gov/types.js';

/**
 * Represents a study location with optional distance calculation.
 */
export interface StudyLocation {
  facility?: string | undefined;
  city?: string | undefined;
  state?: string | undefined;
  country?: string | undefined;
  distance?: number | undefined;
}

/**
 * Represents contact information for a study.
 */
export interface StudyContact {
  name?: string | undefined;
  phone?: string | undefined;
  email?: string | undefined;
}

/**
 * Represents key study details for eligibility matching.
 */
export interface StudyDetails {
  phase?: string[] | undefined;
  status: string;
  enrollmentCount?: number | undefined;
  sponsor?: string | undefined;
}

/**
 * Patient location for filtering study sites.
 */
export interface PatientLocation {
  country: string;
  state?: string | undefined;
  city?: string | undefined;
  postalCode?: string | undefined;
}

/**
 * Extracts relevant locations from a study based on patient location.
 * Filters study locations to prioritize those matching the patient's location.
 *
 * @param study - The clinical trial study
 * @param patientLocation - Patient's location for filtering
 * @returns Array of relevant study locations
 *
 * @example
 * extractRelevantLocations(study, { country: "United States", state: "California" })
 * // returns locations in California, then other US locations
 */
export function extractRelevantLocations(
  study: Study,
  patientLocation: PatientLocation,
): StudyLocation[] {
  const locations = study.protocolSection?.contactsLocationsModule?.locations;
  if (!locations || locations.length === 0) return [];

  const relevantLocations: StudyLocation[] = [];

  for (const loc of locations) {
    // Only include if at least country matches
    if (loc.country) {
      relevantLocations.push({
        facility: (loc as { facility?: string }).facility,
        city: loc.city,
        state: loc.state,
        country: loc.country,
      });
    }
  }

  // Sort: exact city match, then state match, then country match
  relevantLocations.sort((a, b) => {
    const aCity =
      patientLocation.city &&
      a.city?.toLowerCase() === patientLocation.city.toLowerCase();
    const bCity =
      patientLocation.city &&
      b.city?.toLowerCase() === patientLocation.city.toLowerCase();

    if (aCity && !bCity) return -1;
    if (!aCity && bCity) return 1;

    const aState =
      patientLocation.state &&
      a.state?.toLowerCase() === patientLocation.state.toLowerCase();
    const bState =
      patientLocation.state &&
      b.state?.toLowerCase() === patientLocation.state.toLowerCase();

    if (aState && !bState) return -1;
    if (!aState && bState) return 1;

    return 0;
  });

  return relevantLocations;
}

/**
 * Extracts contact information from a study.
 *
 * @param study - The clinical trial study
 * @returns Contact information object or undefined
 *
 * @example
 * extractContactInfo(study)
 * // returns { name: "Dr. Smith", phone: "555-1234", email: "study@example.com" }
 */
export function extractContactInfo(study: Study): StudyContact | undefined {
  const contacts = study.protocolSection?.contactsLocationsModule
    ?.centralContacts as
    | Array<{ name?: string; phone?: string; email?: string }>
    | undefined;

  if (!contacts || contacts.length === 0) {
    return undefined;
  }

  // Use the first central contact
  const primaryContact = contacts[0];

  return {
    name: primaryContact?.name,
    phone: primaryContact?.phone,
    email: primaryContact?.email,
  };
}

/**
 * Extracts key study details for display and ranking.
 *
 * @param study - The clinical trial study
 * @returns Study details object
 *
 * @example
 * extractStudyDetails(study)
 * // returns { phase: ["Phase 3"], status: "Recruiting", enrollmentCount: 500, sponsor: "NIH" }
 */
export function extractStudyDetails(study: Study): StudyDetails {
  const statusModule = study.protocolSection?.statusModule;
  const designModule = study.protocolSection?.designModule;
  const sponsorModule = study.protocolSection?.sponsorCollaboratorsModule;
  const enrollmentInfo = designModule?.enrollmentInfo as
    | { count?: number }
    | undefined;

  return {
    phase: designModule?.phases ?? undefined,
    status: statusModule?.overallStatus ?? 'Unknown',
    enrollmentCount: enrollmentInfo?.count,
    sponsor: sponsorModule?.leadSponsor?.name,
  };
}
