type OperationCallback<OperationResult> = () => Promise<OperationResult>;

export async function operationWithFallback<OperationResult, FallbackValue>(
    performOperation: OperationCallback<OperationResult>,
    fallback: FallbackValue
): Promise<OperationResult | FallbackValue> {
    try {
        return await performOperation();
    } catch {
        return fallback;
    }
}
