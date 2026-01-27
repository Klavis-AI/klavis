/**
 * @fileoverview Utility for displaying startup banners in TTY environments.
 * Provides a centralized way to show user-facing messages during server initialization
 * while preventing output pollution in non-interactive environments (CI, pipes, STDIO transport).
 * @module src/utils/internal/startupBanner
 */

/**
 * Displays a startup banner message to the console only if running in a TTY environment.
 * This prevents polluting STDIO transport, piped output, or CI/CD logs.
 *
 * @param message - The banner message to display
 * @example
 * ```typescript
 * logStartupBanner('🚀 MCP Server running at: http://localhost:3010');
 * ```
 */
export function logStartupBanner(message: string): void {
  if (process.stdout.isTTY) {
    console.log(message);
  }
}
