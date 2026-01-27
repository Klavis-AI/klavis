/**
 * @fileoverview Provider interface for ClinicalTrials.gov API operations.
 * Defines the contract for fetching and querying clinical trial data.
 *
 * @module src/services/clinical-trials-gov/core/IClinicalTrialsProvider
 */

import type { RequestContext } from '@/utils/index.js';
import type { PagedStudies, Study, StudyMetadata } from '../types.js';

/**
 * Query parameters for listing clinical trials.
 */
export interface ListStudiesParams {
  /**
   * Search query to filter studies.
   */
  query?: string;

  /**
   * Filter expression for advanced querying.
   */
  filter?: string;

  /**
   * Maximum number of results to return.
   * @default 10
   */
  pageSize?: number;

  /**
   * Page token for pagination.
   */
  pageToken?: string;

  /**
   * Sort order specification.
   */
  sort?: string;

  /**
   * Specific fields to return (reduces payload size).
   * Example: ['NCTId', 'BriefTitle', 'OverallStatus']
   */
  fields?: string[];

  /**
   * Filter by country.
   */
  country?: string;

  /**
   * Filter by state/province.
   */
  state?: string;

  /**
   * Filter by city.
   */
  city?: string;
}

/**
 * Provider interface for ClinicalTrials.gov API operations.
 * Implementations handle HTTP requests, caching, and data transformation.
 */
export interface IClinicalTrialsProvider {
  /**
   * Fetches a single study by its NCT identifier.
   *
   * @param nctId - The NCT identifier (e.g., 'NCT12345678')
   * @returns The full study record
   * @throws {McpError} If the study is not found or API request fails
   */
  fetchStudy(nctId: string, context: RequestContext): Promise<Study>;

  /**
   * Lists studies matching the provided query parameters.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Paginated list of studies with metadata
   * @throws {McpError} If the API request fails
   */
  listStudies(
    params: ListStudiesParams,
    context: RequestContext,
  ): Promise<PagedStudies>;

  /**
   * Retrieves metadata for a specific study without full details.
   *
   * @param nctId - The NCT identifier
   * @returns Study metadata (title, status, dates)
   * @throws {McpError} If the study is not found or API request fails
   */
  getStudyMetadata(
    nctId: string,
    context: RequestContext,
  ): Promise<StudyMetadata>;

  /**
   * Fetches current API statistics from the /stats/size endpoint.
   * Returns total study count, current timestamp, and API version.
   *
   * @returns API statistics object with totalStudies (from API), lastUpdated (current timestamp), and version ('v2')
   * @throws {McpError} If the API request fails
   */
  getApiStats(context: RequestContext): Promise<{
    totalStudies: number;
    lastUpdated: string;
    version: string;
  }>;
}
