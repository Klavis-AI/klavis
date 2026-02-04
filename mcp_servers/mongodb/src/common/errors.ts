export enum ErrorCodes {
    NotConnectedToMongoDB = 1_000_000,
    MisconfiguredConnectionString = 1_000_001,
    ForbiddenCollscan = 1_000_002,
    ForbiddenWriteOperation = 1_000_003,
    AtlasSearchNotSupported = 1_000_004,
    NoEmbeddingsProviderConfigured = 1_000_005,
    AtlasVectorSearchIndexNotFound = 1_000_006,
    AtlasVectorSearchInvalidQuery = 1_000_007,
    Unexpected = 1_000_008,
}

export class MongoDBError<ErrorCode extends ErrorCodes = ErrorCodes> extends Error {
    constructor(
        public code: ErrorCode,
        message: string
    ) {
        super(message);
    }
}
