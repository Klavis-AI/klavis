/**
 * Gradio metrics tracking module
 *
 * This module collects metrics for Gradio tool calls, tracking successful
 * and failed tool executions to provide visibility into the performance
 * of Gradio endpoints.
 */

import { createHash } from 'crypto';
import { GRADIO_PRIVATE_PREFIX } from '../../shared/constants.js';

export interface GradioToolMetrics {
	/** Number of successful tool calls */
	success: number;
	/** Number of failed tool calls (including isError results and exceptions) */
	failure: number;
	/** Number of dropped/failed progress relays */
	progressRelayFailures: number;
	/** Breakdown by tool name */
	byTool: Record<string, { success: number; failure: number }>;
	/** Progress relay failures by tool */
	progressRelayFailuresByTool: Record<string, number>;
	/** Count of schema formats seen */
	schemaFormats: {
		array: number;
		object: number;
	};
}

export class GradioMetricsCollector {
	private static instance: GradioMetricsCollector;
	private metrics: GradioToolMetrics = {
		success: 0,
		failure: 0,
		progressRelayFailures: 0,
		byTool: {},
		progressRelayFailuresByTool: {},
		schemaFormats: {
			array: 0,
			object: 0,
		},
	};
	schemaFetchErrors: Set<string> = new Set();

	private constructor() {}

	public static getInstance(): GradioMetricsCollector {
		if (!GradioMetricsCollector.instance) {
			GradioMetricsCollector.instance = new GradioMetricsCollector();
		}
		return GradioMetricsCollector.instance;
	}

	/**
	 * Records a successful Gradio tool call
	 * @param toolName The name of the tool that was called
	 */
	public recordSuccess(toolName: string): void {
		// Update overall metrics
		this.metrics.success++;

		// Initialize tool-specific metrics if needed
		if (!this.metrics.byTool[toolName]) {
			this.metrics.byTool[toolName] = { success: 0, failure: 0 };
		}

		// Update tool-specific metrics
		this.metrics.byTool[toolName].success++;
	}

	/**
	 * Records a failed Gradio tool call
	 * @param toolName The name of the tool that was called
	 */
	public recordFailure(toolName: string): void {
		// Update overall metrics
		this.metrics.failure++;

		// Initialize tool-specific metrics if needed
		if (!this.metrics.byTool[toolName]) {
			this.metrics.byTool[toolName] = { success: 0, failure: 0 };
		}

		// Update tool-specific metrics
		this.metrics.byTool[toolName].failure++;
	}

	/**
	 * Returns the current metrics
	 */
	public getMetrics(): Readonly<GradioToolMetrics> {
		return { ...this.metrics, byTool: { ...this.metrics.byTool } };
	}

	/**
	 * Resets all metrics to zero
	 */
	public reset(): void {
		this.metrics = {
			success: 0,
			failure: 0,
			progressRelayFailures: 0,
			byTool: {},
			progressRelayFailuresByTool: {},
			schemaFormats: {
				array: 0,
				object: 0,
			},
		};
	}

	/**
	 * Get a summary of the metrics suitable for logging or display
	 */
	public getSummary(): string {
		const total = this.metrics.success + this.metrics.failure;
		const successRate = total > 0 ? ((this.metrics.success / total) * 100).toFixed(1) : '0.0';
		return `Gradio Tool Calls - Total: ${total}, Success: ${this.metrics.success}, Failure: ${this.metrics.failure}, Success Rate: ${successRate}%`;
	}

	/** we only want to log schema fetch failures for a specific endpoint once */
	public schemaFetchError(toolName: string): boolean {
		if (this.schemaFetchErrors.has(toolName)) {
			return false;
		}
		this.schemaFetchErrors.add(toolName);
		return true;
	}

	/** track whether schema was array or object */
	public recordSchemaFormat(format: 'array' | 'object'): void {
		if (format === 'array') {
			this.metrics.schemaFormats.array++;
		} else if (format === 'object') {
			this.metrics.schemaFormats.object++;
		}
	}

	/** Track when progress relay fails (e.g., client disconnect during SSE) */
	public recordProgressRelayFailure(toolName: string): void {
		this.metrics.progressRelayFailures++;
		if (!this.metrics.progressRelayFailuresByTool[toolName]) {
			this.metrics.progressRelayFailuresByTool[toolName] = 0;
		}
		this.metrics.progressRelayFailuresByTool[toolName]++;
	}
}

// Export singleton instance
export const gradioMetrics = GradioMetricsCollector.getInstance();

/**
 * Get the metrics-safe name for a Gradio tool.
 * For private tools (with grp prefix), this returns an obfuscated name
 * that includes a hash for uniqueness but doesn't reveal the actual tool name.
 *
 * @param toolName The original tool name (e.g., "grp1_evalstate_private_model")
 * @returns The metrics-safe name (e.g., "grp1_[private_a1b2c3]" for private tools)
 */
export function getMetricsSafeName(toolName: string): string {
	// Check if this is a private Gradio tool
	if (toolName.startsWith(GRADIO_PRIVATE_PREFIX)) {
		// Extract the index and the actual name
		const match = toolName.match(/^grp(\d+)_(.*)$/);
		if (match && match[1] && match[2]) {
			const index = match[1];
			const privateName = match[2];
			// Create a short hash of the name for uniqueness
			const hash = createHash('sha256').update(privateName).digest('hex').substring(0, 6);
			return `grp${index}_[private_${hash}]`;
		}
	}
	// For non-private tools, return as-is
	return toolName;
}
