import { ApiError } from "./openapi.js";

export class ApiClientError extends Error {
    private constructor(
        message: string,
        public readonly response: Response,
        public readonly apiError?: ApiError
    ) {
        super(message);
        this.name = "ApiClientError";
    }

    static async fromResponse(
        response: Response,
        message: string = `error calling Atlas API`
    ): Promise<ApiClientError> {
        const err = await this.extractError(response);

        return this.fromError(response, err, message);
    }

    static fromError(
        response: Response,
        error?: ApiError | string | Error,
        message: string = `error calling Atlas API`
    ): ApiClientError {
        const errorMessage = this.buildErrorMessage(error);

        const apiError = typeof error === "object" && !(error instanceof Error) ? error : undefined;

        return new ApiClientError(
            `[${response.status} ${response.statusText}] ${message}: ${errorMessage}`,
            response,
            apiError
        );
    }

    private static async extractError(response: Response): Promise<ApiError | string | undefined> {
        try {
            return (await response.json()) as ApiError;
        } catch {
            try {
                return await response.text();
            } catch {
                return undefined;
            }
        }
    }

    private static buildErrorMessage(error?: string | ApiError | Error): string {
        let errorMessage: string = "unknown error";

        if (error instanceof Error) {
            return error.message;
        }

        //eslint-disable-next-line @typescript-eslint/switch-exhaustiveness-check
        switch (typeof error) {
            case "object":
                errorMessage = error.reason || "unknown error";
                if (error.detail && error.detail.length > 0) {
                    errorMessage = `${errorMessage}; ${error.detail}`;
                }
                break;
            case "string":
                errorMessage = error;
                break;
        }

        return errorMessage.trim();
    }
}
