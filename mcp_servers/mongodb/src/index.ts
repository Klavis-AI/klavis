#!/usr/bin/env node

import logger, { LogId } from "./common/logger.js";
import { config } from "./common/config.js";
import { StdioRunner } from "./transports/stdio.js";
import { StreamableHttpRunner } from "./transports/streamableHttp.js";

async function main() {
    const transportRunner = config.transport === "stdio" ? new StdioRunner(config) : new StreamableHttpRunner(config);

    const shutdown = () => {
        logger.info(LogId.serverCloseRequested, "server", `Server close requested`);

        transportRunner
            .close()
            .then(() => {
                logger.info(LogId.serverClosed, "server", `Server closed`);
                process.exit(0);
            })
            .catch((error: unknown) => {
                logger.error(LogId.serverCloseFailure, "server", `Error closing server: ${error as string}`);
                process.exit(1);
            });
    };

    process.on("SIGINT", shutdown);
    process.on("SIGABRT", shutdown);
    process.on("SIGTERM", shutdown);
    process.on("SIGQUIT", shutdown);

    try {
        await transportRunner.start();
    } catch (error: unknown) {
        logger.info(LogId.serverCloseRequested, "server", "Closing server");
        try {
            await transportRunner.close();
            logger.info(LogId.serverClosed, "server", "Server closed");
        } catch (error: unknown) {
            logger.error(LogId.serverCloseFailure, "server", `Error closing server: ${error as string}`);
        }
        throw error;
    }
}

main().catch((error: unknown) => {
    logger.emergency(LogId.serverStartFailure, "server", `Fatal error running server: ${error as string}`);
    process.exit(1);
});
