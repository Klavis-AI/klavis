import { InMemoryTransport } from "./inMemoryTransport.js";
import { TransportRunnerBase, type TransportRunnerConfig } from "./base.js";
import { type Server } from "../server.js";

export type DryRunModeTestHelpers = {
    logger: {
        log(this: void, message: string): void;
        error(this: void, message: string): void;
    };
};

type DryRunModeRunnerConfig = TransportRunnerConfig & DryRunModeTestHelpers;

export class DryRunModeRunner extends TransportRunnerBase {
    private server: Server | undefined;
    private consoleLogger: DryRunModeTestHelpers["logger"];

    constructor({ logger, ...transportRunnerConfig }: DryRunModeRunnerConfig) {
        super(transportRunnerConfig);
        this.consoleLogger = logger;
    }

    override async start(): Promise<void> {
        this.server = await this.setupServer();
        const transport = new InMemoryTransport();

        await this.server.connect(transport);
        this.dumpConfig();
        this.dumpTools();
    }

    override async closeTransport(): Promise<void> {
        await this.server?.close();
    }

    private dumpConfig(): void {
        this.consoleLogger.log("Configuration:");
        this.consoleLogger.log(JSON.stringify(this.userConfig, null, 2));
    }

    private dumpTools(): void {
        const tools =
            this.server?.tools
                .filter((tool) => tool.isEnabled())
                .map((tool) => ({
                    name: tool.name,
                    category: tool.category,
                })) ?? [];
        this.consoleLogger.log("Enabled tools:");
        this.consoleLogger.log(JSON.stringify(tools, null, 2));
    }
}
