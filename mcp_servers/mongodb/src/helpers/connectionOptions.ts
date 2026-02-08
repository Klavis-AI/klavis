import { MongoClientOptions } from "mongodb";
import ConnectionString from "mongodb-connection-string-url";

export function setAppNameParamIfMissing({
    connectionString,
    defaultAppName,
}: {
    connectionString: string;
    defaultAppName?: string;
}): string {
    const connectionStringUrl = new ConnectionString(connectionString);

    const searchParams = connectionStringUrl.typedSearchParams<MongoClientOptions>();

    if (!searchParams.has("appName") && defaultAppName !== undefined) {
        searchParams.set("appName", defaultAppName);
    }

    return connectionStringUrl.toString();
}
