import { logger } from '../utils/logger.js';

/**
 * API call metrics tracking for external HuggingFace API calls
 */
export interface ApiCallMetrics {
	anonymous: number;
	authenticated: number;
	unauthorized: number; // 401
	forbidden: number; // 403
}

class ApiMetricsCollector {
	private metrics: ApiCallMetrics = {
		anonymous: 0,
		authenticated: 0,
		unauthorized: 0,
		forbidden: 0,
	};

	/**
	 * Record an API call with its outcome
	 * @param hasToken - Whether the call was made with an HF token
	 * @param status - HTTP status code (200 for success, 401/403 for auth errors)
	 */
	recordCall(hasToken: boolean, status: number): void {
		logger.debug(`Recording API call: hasToken=${hasToken}, status=${status}`);
		if (status === 200) {
			if (hasToken) {
				this.metrics.authenticated++;
			} else {
				this.metrics.anonymous++;
			}
		} else if (status === 401) {
			this.metrics.unauthorized++;
		} else if (status === 403) {
			this.metrics.forbidden++;
		}
	}

	/**
	 * Get current metrics snapshot
	 */
	getMetrics(): ApiCallMetrics {
		return { ...this.metrics };
	}

	/**
	 * Reset all metrics to zero
	 */
	resetMetrics(): void {
		this.metrics = {
			anonymous: 0,
			authenticated: 0,
			unauthorized: 0,
			forbidden: 0,
		};
	}
}

// Export singleton instance
export const apiMetrics = new ApiMetricsCollector();
