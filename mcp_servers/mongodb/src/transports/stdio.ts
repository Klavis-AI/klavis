import logger, { LogId } from "../common/logger.js";
import { Server } from "../server.js";
import { TransportRunnerBase } from "./base.js";
import { JSONRPCMessage, JSONRPCMessageSchema } from "@modelcontextprotocol/sdk/types.js";
import { EJSON } from "bson";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { UserConfig } from "../common/config.js";

// This is almost a copy of ReadBuffer from @modelcontextprotocol/sdk
// but it uses EJSON.parse instead of JSON.parse to handle BSON types
export class EJsonReadBuffer {
    private _buffer?: Buffer;

    append(chunk: Buffer): void {
        this._buffer = this._buffer ? Buffer.concat([this._buffer, chunk]) : chunk;
    }

    readMessage(): JSONRPCMessage | null {
        if (!this._buffer) {
            return null;
        }

        const index = this._buffer.indexOf("\n");
        if (index === -1) {
            return null;
        }

        const line = this._buffer.toString("utf8", 0, index).replace(/\r$/, "");
        this._buffer = this._buffer.subarray(index + 1);

        // This is using EJSON.parse instead of JSON.parse to handle BSON types
        return JSONRPCMessageSchema.parse(EJSON.parse(line));
    }

    clear(): void {
        this._buffer = undefined;
    }
}

// This is a hacky workaround for https://github.com/mongodb-js/mongodb-mcp-server/issues/211
// The underlying issue is that StdioServerTransport uses JSON.parse to deserialize
// messages, but that doesn't handle bson types, such as ObjectId when serialized as EJSON.
//
// This function creates a StdioServerTransport and replaces the internal readBuffer with EJsonReadBuffer
// that uses EJson.parse instead.
export function createStdioTransport(): StdioServerTransport {
    const server = new StdioServerTransport();
    server["_readBuffer"] = new EJsonReadBuffer();

    return server;
}

export class StdioRunner extends TransportRunnerBase {
    private server: Server | undefined;

    constructor(private userConfig: UserConfig) {
        super();
    }

    async start() {
        try {
            this.server = this.setupServer(this.userConfig);

            const transport = createStdioTransport();

            await this.server.connect(transport);
        } catch (error: unknown) {
            logger.emergency(LogId.serverStartFailure, "server", `Fatal error running server: ${error as string}`);
            process.exit(1);
        }
    }

    async close(): Promise<void> {
        await this.server?.close();
    }
}
