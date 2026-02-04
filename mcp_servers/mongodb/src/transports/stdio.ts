import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { LogId } from "../common/logger.js";
import type { Server } from "../server.js";
import { TransportRunnerBase, type TransportRunnerConfig } from "./base.js";

export class StdioRunner extends TransportRunnerBase {
    private server: Server | undefined;

    constructor(config: TransportRunnerConfig) {
        super(config);
    }

    async start(): Promise<void> {
        try {
            this.server = await this.setupServer();
            const transport = new StdioServerTransport();

            await this.server.connect(transport);
        } catch (error: unknown) {
            this.logger.emergency({
                id: LogId.serverStartFailure,
                context: "server",
                message: `Fatal error running server: ${error as string}`,
            });
            process.exit(1);
        }
    }

    async closeTransport(): Promise<void> {
        await this.server?.close();
    }
}
