/**
 * Custom error class that includes HTTP status information
 */
export class HfApiError extends Error {
	constructor(
		message: string,
		public readonly status: number,
		public readonly statusText: string,
		public readonly responseBody?: string
	) {
		super(message);
		this.name = 'HfApiError';
	}

	/**
	 * Format the error with a friendly explanation followed by the original error
	 * @param friendlyExplanation - User-friendly explanation
	 * @param context - Optional context about what was being attempted
	 * @returns Formatted error message
	 */
	formatWithExplanation(friendlyExplanation: string, context?: string): string {
		let formatted = '';

		// Add context if provided
		if (context) {
			formatted = `${context}. `;
		}

		// Add friendly explanation
		formatted += friendlyExplanation;

		// Add original error message on new line
		formatted += `\n\n${this.message}`;

		// Add response body details if available and different from message
		if (this.responseBody) {
			try {
				const parsed = JSON.parse(this.responseBody) as { error?: string; message?: string; detail?: string };
				const errorDetail = parsed.error || parsed.message || parsed.detail;
				if (errorDetail && !this.message.includes(errorDetail)) {
					formatted += `\n${errorDetail}`;
				}
			} catch {
				// If not JSON, add raw response if it's not too long and not already in message
				if (this.responseBody.length < 200 && !this.message.includes(this.responseBody)) {
					formatted += `\n${this.responseBody}`;
				}
			}
		}

		return formatted;
	}

	/**
	 * Create a new HfApiError with an improved message while preserving all other properties
	 * @param friendlyExplanation - User-friendly explanation
	 * @param context - Optional context about what was being attempted
	 * @returns New HfApiError with improved message
	 */
	withImprovedMessage(friendlyExplanation: string, context?: string): HfApiError {
		const improvedMessage = this.formatWithExplanation(friendlyExplanation, context);
		return new HfApiError(improvedMessage, this.status, this.statusText, this.responseBody);
	}
}

/**
 * Base API client for Hugging Face HTTP APIs
 *
 * @template TParams - Type for API parameters
 * @template TResponse - Type for API response
 */
export class HfApiCall<TParams = Record<string, string | undefined>, TResponse = unknown> {
	protected readonly apiUrl: string;
	protected readonly hfToken: string | undefined;
	protected readonly apiTimeout: number;
	/** nb reversed order from superclasses on basis that hfToken is more likely to be configured */
	constructor(apiUrl: string, hfToken?: string) {
		this.apiUrl = apiUrl;
		this.hfToken = hfToken;
		// Default to 12.5 seconds if HF_API_TIMEOUT is not set
		this.apiTimeout = process.env.HF_API_TIMEOUT ? parseInt(process.env.HF_API_TIMEOUT, 10) : 12500;
	}

	/**
	 * Fetches data from the API with proper error handling and authentication
	 *
	 * @template T - Response type (defaults to TResponse)
	 * @param url - The URL to fetch from
	 * @param options - Fetch options
	 * @returns The parsed JSON response
	 */
	protected async fetchFromApi<T = TResponse>(url: URL | string, options?: globalThis.RequestInit): Promise<T> {
		try {
			const headers: Record<string, string> = {
				Accept: 'application/json',
				...((options?.headers as Record<string, string>) || {}),
			};
			if (this.hfToken) {
				headers['Authorization'] = `Bearer ${this.hfToken}`;
			}

			// Add timeout using AbortController
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), this.apiTimeout);

			const response = await fetch(url.toString(), {
				...options,
				headers,
				signal: controller.signal,
			});

			clearTimeout(timeoutId);

			const responseBodyText = await response.text();

			if (!response.ok) {
				// Try to get error details from response body
				const responseBody: string | undefined = responseBodyText || undefined;

				// Log the error for debugging
				console.error(`[API Error] ${response.status} ${response.statusText}`);
				if (responseBody) {
					console.error('[API Error] Response:', responseBody);
				}

				throw new HfApiError(
					`API request failed: ${response.status.toString()} ${response.statusText}`,
					response.status,
					response.statusText,
					responseBody
				);
			}

			const contentType = response.headers.get('content-type') ?? '';
			const trimmedBody = responseBodyText.trim();
			const looksLikeJson =
				contentType.includes('application/json') || trimmedBody.startsWith('{') || trimmedBody.startsWith('[');

			if (trimmedBody.length === 0) {
				return undefined as T;
			}

			if (looksLikeJson) {
				try {
					return JSON.parse(responseBodyText) as T;
				} catch (error) {
					throw new Error(
						`API request failed: Unable to parse JSON response (${error instanceof Error ? error.message : 'unknown error'})`
					);
				}
			}

			if (trimmedBody.toUpperCase() === 'OK') {
				return undefined as T;
			}

			const truncatedBody = trimmedBody.length > 200 ? `${trimmedBody.slice(0, 200)}…` : trimmedBody;
			throw new Error(
				`API request failed: Unexpected non-JSON response${contentType ? ` (content-type: ${contentType})` : ''}: ${truncatedBody}`
			);
		} catch (error) {
			// Re-throw HfApiError as-is to preserve status information
			if (error instanceof HfApiError) {
				throw error;
			}
			// Handle timeout errors
			if (error instanceof Error && error.name === 'AbortError') {
				throw new Error(`API request timed out after ${this.apiTimeout}ms`);
			}
			// Wrap other errors
			if (error instanceof Error) {
				throw new Error(`API request failed: ${error.message}`);
			}
			throw error;
		}
	}

	/**
	 * Builds a URL with query parameters
	 *
	 * @param params - Key-value pairs of query parameters
	 * @returns A URL object with the query parameters appended
	 */
	protected buildUrl(params: TParams): URL {
		const url = new URL(this.apiUrl);

		// Iterate over params in a type-safe way
		for (const key in params) {
			const value = params[key as keyof TParams];
			if (value !== undefined) {
				url.searchParams.append(key, String(value));
			}
		}

		return url;
	}

	/**
	 * Builds a URL with the given parameters and makes an API request
	 *
	 * @template T - Response type (defaults to TResponse)
	 * @param params - The parameters to include in the URL
	 * @param options - Additional fetch options
	 * @returns The parsed JSON response
	 */
	protected async callApi<T = TResponse>(params: TParams, options?: globalThis.RequestInit): Promise<T> {
		const url = this.buildUrl(params);
		return this.fetchFromApi<T>(url, options);
	}
}
