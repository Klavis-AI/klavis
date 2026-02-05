import express from "express";
import http from "http";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { TransportRunnerBase } from "./base.js";
import { UserConfig, extractConnectionStringFromAuthData } from "../common/config.js";
import logger, { LogId } from "../common/logger.js";
import { randomUUID } from "crypto";
import { SessionStore } from "../common/sessionStore.js";
import { EJSON } from "bson";

const JSON_RPC_ERROR_CODE_PROCESSING_REQUEST_FAILED = -32000;
const JSON_RPC_ERROR_CODE_SESSION_ID_REQUIRED = -32001;
const JSON_RPC_ERROR_CODE_SESSION_ID_INVALID = -32002;
const JSON_RPC_ERROR_CODE_SESSION_NOT_FOUND = -32003;
const JSON_RPC_ERROR_CODE_INVALID_REQUEST = -32004;

function withErrorHandling(
    fn: (req: express.Request, res: express.Response, next: express.NextFunction) => Promise<void>
) {
    return (req: express.Request, res: express.Response, next: express.NextFunction) => {
        fn(req, res, next).catch((error) => {
            logger.error(
                LogId.streamableHttpTransportRequestFailure,
                "streamableHttpTransport",
                `Error handling request: ${error instanceof Error ? error.message : String(error)}`
            );
            res.status(400).json({
                jsonrpc: "2.0",
                error: {
                    code: JSON_RPC_ERROR_CODE_PROCESSING_REQUEST_FAILED,
                    message: `failed to handle request`,
                    data: error instanceof Error ? error.message : String(error),
                },
            });
        });
    };
}

// Custom middleware to parse JSON using EJSON instead of regular JSON.parse
// This is needed to properly handle BSON types like ObjectId, Date, etc.
function ejsonParser(req: express.Request, res: express.Response, next: express.NextFunction) {
    if (req.is("application/json")) {
        let data = "";
        req.setEncoding("utf8");
        req.on("data", (chunk) => {
            data += chunk;
        });
        req.on("end", () => {
            try {
                req.body = data ? EJSON.parse(data) : {};
                next();
            } catch (error) {
                res.status(400).json({
                    jsonrpc: "2.0",
                    error: {
                        code: JSON_RPC_ERROR_CODE_PROCESSING_REQUEST_FAILED,
                        message: "Invalid JSON",
                        data: error instanceof Error ? error.message : String(error),
                    },
                });
            }
        });
    } else {
        next();
    }
}

export class StreamableHttpRunner extends TransportRunnerBase {
    private httpServer: http.Server | undefined;
    private sessionStore: SessionStore;

    constructor(private userConfig: UserConfig) {
        super();
        this.sessionStore = new SessionStore(this.userConfig.idleTimeoutMs, this.userConfig.notificationTimeoutMs);
    }

    async start() {
        const app = express();
        app.enable("trust proxy"); // needed for reverse proxy support
        app.use(ejsonParser); // Use EJSON parser instead of express.json() to handle BSON types

        const handleSessionRequest = async (req: express.Request, res: express.Response) => {
            const sessionId = req.headers["mcp-session-id"];
            if (!sessionId) {
                res.status(400).json({
                    jsonrpc: "2.0",
                    error: {
                        code: JSON_RPC_ERROR_CODE_SESSION_ID_REQUIRED,
                        message: `session id is required`,
                    },
                });
                return;
            }
            if (typeof sessionId !== "string") {
                res.status(400).json({
                    jsonrpc: "2.0",
                    error: {
                        code: JSON_RPC_ERROR_CODE_SESSION_ID_INVALID,
                        message: `session id is invalid`,
                    },
                });
                return;
            }
            const transport = this.sessionStore.getSession(sessionId);
            if (!transport) {
                res.status(404).json({
                    jsonrpc: "2.0",
                    error: {
                        code: JSON_RPC_ERROR_CODE_SESSION_NOT_FOUND,
                        message: `session not found`,
                    },
                });
                return;
            }
            await transport.handleRequest(req, res, req.body);
        };

        app.post(
            "/mcp",
            withErrorHandling(async (req: express.Request, res: express.Response) => {
                const sessionId = req.headers["mcp-session-id"];
                if (sessionId) {
                    await handleSessionRequest(req, res);
                    return;
                }

                if (!isInitializeRequest(req.body)) {
                    res.status(400).json({
                        jsonrpc: "2.0",
                        error: {
                            code: JSON_RPC_ERROR_CODE_INVALID_REQUEST,
                            message: `invalid request`,
                        },
                    });
                    return;
                }

                // Extract connection string from x-auth-data header if not already set
                let sessionConfig = this.userConfig;
                if (!sessionConfig.connectionString) {
                    const connectionStringFromAuthData = extractConnectionStringFromAuthData(
                        req.headers as Record<string, string | string[] | undefined>
                    );
                    if (connectionStringFromAuthData) {
                        sessionConfig = {
                            ...this.userConfig,
                            connectionString: connectionStringFromAuthData,
                        };
                    }
                }

                const server = this.setupServer(sessionConfig);
                const transport = new StreamableHTTPServerTransport({
                    sessionIdGenerator: () => randomUUID().toString(),
                    onsessioninitialized: (sessionId) => {
                        this.sessionStore.setSession(sessionId, transport, server.mcpServer);
                    },
                    onsessionclosed: async (sessionId) => {
                        try {
                            await this.sessionStore.closeSession(sessionId, false);
                        } catch (error) {
                            logger.error(
                                LogId.streamableHttpTransportSessionCloseFailure,
                                "streamableHttpTransport",
                                `Error closing session: ${error instanceof Error ? error.message : String(error)}`
                            );
                        }
                    },
                });

                transport.onclose = () => {
                    server.close().catch((error) => {
                        logger.error(
                            LogId.streamableHttpTransportCloseFailure,
                            "streamableHttpTransport",
                            `Error closing server: ${error instanceof Error ? error.message : String(error)}`
                        );
                    });
                };

                await server.connect(transport);

                await transport.handleRequest(req, res, req.body);
            })
        );

        app.get("/mcp", withErrorHandling(handleSessionRequest));
        app.delete("/mcp", withErrorHandling(handleSessionRequest));

        this.httpServer = await new Promise<http.Server>((resolve, reject) => {
            const result = app.listen(this.userConfig.httpPort, this.userConfig.httpHost, (err?: Error) => {
                if (err) {
                    reject(err);
                    return;
                }
                resolve(result);
            });
        });

        logger.info(
            LogId.streamableHttpTransportStarted,
            "streamableHttpTransport",
            `Server started on http://${this.userConfig.httpHost}:${this.userConfig.httpPort}`
        );
    }

    async close(): Promise<void> {
        await Promise.all([
            this.sessionStore.closeAllSessions(),
            new Promise<void>((resolve, reject) => {
                this.httpServer?.close((err) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    resolve();
                });
            }),
        ]);
    }
}
