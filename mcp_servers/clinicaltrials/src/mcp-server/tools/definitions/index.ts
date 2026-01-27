/**
 * @fileoverview Barrel file for all tool definitions.
 * This file re-exports all tool definitions for easy import and registration.
 * It also exports an array of all definitions for automated registration.
 * @module src/mcp-server/tools/definitions
 */

import { analyzeTrendsTool } from './clinicaltrials-analyze-trends.tool.js';
import { compareStudiesTool } from './clinicaltrials-compare-studies.tool.js';
import { findEligibleStudiesTool } from './clinicaltrials-find-eligible-studies.tool.js';
import { getStudyTool } from './clinicaltrials-get-study.tool.js';
import { searchStudiesTool } from './clinicaltrials-search-studies.tool.js';

/**
 * An array containing all tool definitions for easy iteration.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const allToolDefinitions: any[] = [
  analyzeTrendsTool,
  compareStudiesTool,
  findEligibleStudiesTool,
  getStudyTool,
  searchStudiesTool,
];
