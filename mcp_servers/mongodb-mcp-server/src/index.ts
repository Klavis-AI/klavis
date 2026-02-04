#!/usr/bin/env node
/* eslint-disable no-console */

function enableFipsIfRequested(): void {
    let fipsError: Error | undefined;
    const tlsFIPSMode = process.argv.includes("--tlsFIPSMode");

    if (tlsFIPSMode) {
        try {
            // eslint-disable-next-line
            require("crypto").setFips(1);
        } catch (err: unknown) {
            fipsError ??= err as Error;
        }
    }

    if (tlsFIPSMode) {
        if (!fipsError && !crypto.getFips()) {
            fipsError = new Error("FIPS mode not enabled despite requested due to unknown error.");
        }
    }

    if (fipsError) {
        if (process.config.variables.node_shared_openssl) {
            console.error(
                "Could not enable FIPS mode. Please ensure that your system OpenSSL installation supports FIPS."
            );
        } else {
            console.error("Could not enable FIPS mode. This installation does not appear to support FIPS.");
        }
        console.error("Error details:");
        console.error(fipsError);
        process.exit(1);
    }
}

enableFipsIfRequested();

import crypto from "crypto";
import { ConsoleLogger, LogId } from "./common/logger.js";
import { parseUserConfig } from "./common/config/parseUserConfig.js";
import { type UserConfig } from "./common/config/userConfig.js";
import { packageInfo } from "./common/packageInfo.js";
import { StdioRunner } from "./transports/stdio.js";
import { StreamableHttpRunner } from "./transports/streamableHttp.js";
import { systemCA } from "@mongodb-js/devtools-proxy-support";
import { Keychain } from "./common/keychain.js";
import { DryRunModeRunner } from "./transports/dryModeRunner.js";

async function main(): Promise<void> {
    systemCA().catch(() => undefined); // load system CA asynchronously as in mongosh

    const {
        error,
        warnings,
        parsed: config,
    } = parseUserConfig({
        args: process.argv.slice(2),
    });

    if (!config || (error && error.length)) {
        console.error(`${error}
- Refer to https://www.mongodb.com/docs/mcp-server/get-started/ for setting up the MCP Server.`);
        process.exit(1);
    }

    if (warnings && warnings.length) {
        console.warn(`${warnings.join("\n")}
- Refer to https://www.mongodb.com/docs/mcp-server/get-started/ for setting up the MCP Server.`);
    }

    if (config.help) {
        handleHelpRequest();
    }

    if (config.version) {
        handleVersionRequest();
    }

    if (config.dryRun) {
        await handleDryRunRequest(config);
    }

    const transportRunner =
        config.transport === "stdio"
            ? new StdioRunner({
                  userConfig: config,
              })
            : new StreamableHttpRunner({
                  userConfig: config,
              });
    const shutdown = (): void => {
        transportRunner.logger.info({
            id: LogId.serverCloseRequested,
            context: "server",
            message: `Server close requested`,
        });

        transportRunner
            .close()
            .then(() => {
                transportRunner.logger.info({
                    id: LogId.serverClosed,
                    context: "server",
                    message: `Server closed`,
                });
                process.exit(0);
            })
            .catch((error: unknown) => {
                transportRunner.logger.error({
                    id: LogId.serverCloseFailure,
                    context: "server",
                    message: `Error closing server: ${error as string}`,
                });
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
        transportRunner.logger.info({
            id: LogId.serverCloseRequested,
            context: "server",
            message: `Closing server due to error: ${error as string}`,
            noRedaction: true,
        });

        try {
            await transportRunner.close();
            transportRunner.logger.info({
                id: LogId.serverClosed,
                context: "server",
                message: "Server closed",
            });
        } catch (error: unknown) {
            transportRunner.logger.error({
                id: LogId.serverCloseFailure,
                context: "server",
                message: `Error closing server: ${error as string}`,
            });
        }
        throw error;
    }
}

main().catch((error: unknown) => {
    // At this point, we may be in a very broken state, so we can't rely on the logger
    // being functional. Instead, create a brand new ConsoleLogger and log the error
    // to the console.
    const logger = new ConsoleLogger(Keychain.root);
    logger.emergency({
        id: LogId.serverStartFailure,
        context: "server",
        message: `Fatal error running server: ${error as string}`,
    });
    process.exit(1);
});

function handleHelpRequest(): never {
    console.log("For usage information refer to the README.md:");
    console.log("https://github.com/mongodb-js/mongodb-mcp-server?tab=readme-ov-file#quick-start");
    process.exit(0);
}

function handleVersionRequest(): never {
    console.log(packageInfo.version);
    process.exit(0);
}

export async function handleDryRunRequest(config: UserConfig): Promise<never> {
    try {
        const runner = new DryRunModeRunner({
            userConfig: config,
            logger: {
                log(message): void {
                    console.log(message);
                },
                error(message): void {
                    console.error(message);
                },
            },
        });
        await runner.start();
        await runner.close();
        process.exit(0);
    } catch (error) {
        console.error(`Fatal error running server in dry run mode: ${error as string}`);
        process.exit(1);
    }
}
