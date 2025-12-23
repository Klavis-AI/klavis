import { VercelDeployment, VercelProject, VercelDomain, VercelEnvironmentVariable } from "./types/vercel.js";

/**
 * Utility functions for the Vercel MCP Server - only keeping functions used in index.ts
 */

/**
 * Format timestamp to human-readable date
 */
export function formatTimestamp(timestamp: number): string {
  return new Date(timestamp).toISOString();
}

/**
 * Get deployment status color for display
 */
export function getDeploymentStatusColor(state: string): string {
  switch (state) {
    case "READY":
      return "";
    case "BUILDING":
      return "";
    case "ERROR":
      return "";
    case "CANCELED":
      return "";
    case "QUEUED":
    case "INITIALIZING":
      return "";
    default:
      return "";
  }
}

/**
 * Format deployment for display
 */
export function formatDeployment(deployment: VercelDeployment): string {
  const status = getDeploymentStatusColor(deployment.state);
  const created = formatTimestamp(deployment.created);
  return `${status} ${deployment.name} (${deployment.state}) - ${deployment.url} - Created: ${created}`;
}

/**
 * Format project for display
 */
export function formatProject(project: VercelProject): string {
  const created = formatTimestamp(project.createdAt);
  const framework = project.framework ? ` [${project.framework}]` : "";
  const repo = project.gitRepository ? ` (${project.gitRepository.repo})` : "";
  return ` ${project.name}${framework}${repo} - Created: ${created}`;
}

/**
 * Format domain for display
 */
export function formatDomain(domain: VercelDomain): string {
  const status = domain.verified ? "" : "";
  const name = domain.name || "Unknown";
  const verified = domain.verified !== undefined ? domain.verified : "Unknown";
  const created = domain.createdAt ? formatTimestamp(domain.createdAt) : "Unknown";
  return `${status} ${name} - Verified: ${verified} - Created: ${created}`;
}

/**
 * Format environment variable for display (masked value)
 */
export function formatEnvVar(envVar: VercelEnvironmentVariable): string {
  const key = envVar.key || "Unknown";
  const targets = Array.isArray(envVar.target) ? envVar.target.join(", ") : (envVar.target || "Unknown");
  const maskedValue = envVar.type === "plain" ? (envVar.value || "N/A") : "***ENCRYPTED***";
  const type = envVar.type || "Unknown";
  const created = envVar.createdAt ? formatTimestamp(envVar.createdAt) : "Unknown";
  return ` ${key}=${maskedValue} [${targets}] (${type}) - Created: ${created}`;
}

/**
 * Sanitize error message for display
 */
export function sanitizeErrorMessage(error: any): string {
  if (typeof error === "string") {
    return error;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  if (error?.error?.message) {
    return error.error.message;
  }
  
  return "An unknown error occurred";
}
