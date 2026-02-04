import type { Client } from "@mongodb-js/atlas-local";
import { LogId, type LoggerBase } from "./logger.js";

export type AtlasLocalClientFactoryFn = ({
    logger,
    loader,
}: {
    logger: LoggerBase;
    loader?: LibraryLoader;
}) => Promise<Client | undefined>;

export interface LibraryLoader {
    loadAtlasLocalClient: (logger: LoggerBase) => Promise<typeof Client | undefined>;
}

class DefaultLibraryLoader implements LibraryLoader {
    public static readonly instance = new DefaultLibraryLoader();

    private isAtlasLocalSupported: boolean = true;

    private constructor() {}

    public async loadAtlasLocalClient(logger: LoggerBase): Promise<typeof Client | undefined> {
        // If we've tried and failed to load the Atlas Local client before, don't try again
        if (!this.isAtlasLocalSupported) {
            return undefined;
        }

        try {
            // Try to dynamically import the Atlas Local client library - this will fail
            // on unsupported platforms (e.g., Windows on ARM)
            const { Client: AtlasLocalClient } = await import("@mongodb-js/atlas-local");
            return AtlasLocalClient;
        } catch {
            this.isAtlasLocalSupported = false;

            logger.warning({
                id: LogId.atlasLocalUnsupportedPlatform,
                message:
                    "Atlas Local is not supported on this platform. Atlas Local tools are disabled. All other tools continue to work normally.",
                context: "Atlas Local Initialization",
            });

            return undefined;
        }
    }
}

export const defaultCreateAtlasLocalClient: AtlasLocalClientFactoryFn = async ({ logger, loader }) => {
    const libraryLoader = loader ?? DefaultLibraryLoader.instance;
    const client = await libraryLoader.loadAtlasLocalClient(logger);

    try {
        // Connect to Atlas Local client
        // This will fail if docker is not running
        return client?.connect();
    } catch {
        logger.warning({
            id: LogId.atlasLocalDockerNotRunning,
            message:
                "Cannot connect to Docker. Atlas Local tools are disabled. All other tools continue to work normally.",
            context: "Atlas Local Initialization",
        });

        return undefined;
    }
};
