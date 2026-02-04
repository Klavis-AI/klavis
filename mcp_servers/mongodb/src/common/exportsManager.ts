import z from "zod";
import path from "path";
import fs from "fs/promises";
import EventEmitter from "events";
import { createWriteStream } from "fs";
import type { AggregationCursor, FindCursor } from "mongodb";
import type { EJSONOptions } from "bson";
import { EJSON, ObjectId } from "bson";
import { Transform } from "stream";
import { pipeline } from "stream/promises";
import type { MongoLogId } from "mongodb-log-writer";

import type { UserConfig } from "./config/userConfig.js";
import type { LoggerBase } from "./logger.js";
import { LogId } from "./logger.js";

export const jsonExportFormat = z.enum(["relaxed", "canonical"]);
export type JSONExportFormat = z.infer<typeof jsonExportFormat>;

interface CommonExportData {
    exportName: string;
    exportTitle: string;
    exportURI: string;
    exportPath: string;
}

interface ReadyExport extends CommonExportData {
    exportStatus: "ready";
    exportCreatedAt: number;
    docsTransformed: number;
}

interface InProgressExport extends CommonExportData {
    exportStatus: "in-progress";
}

type StoredExport = ReadyExport | InProgressExport;

/**
 * Ideally just exportName and exportURI should be made publicly available but
 * we also make exportPath available because the export tool, also returns the
 * exportPath in its response when the MCP server is running connected to stdio
 * transport. The reasoning behind this is that a few clients, Cursor in
 * particular, as of the date of this writing (7 August 2025) cannot refer to
 * resource URIs which means they have no means to access the exported resource.
 * As of this writing, majority of the usage of our MCP server is behind STDIO
 * transport so we can assume that for most of the usages, if not all, the MCP
 * server will be running on the same machine as of the MCP client and thus we
 * can provide the local path to export so that these clients which do not still
 * support parsing resource URIs, can still work with the exported data. We
 * expect for clients to catch up and implement referencing resource URIs at
 * which point it would be safe to remove the `exportPath` from the publicly
 * exposed properties of an export.
 *
 * The editors that we would like to watch out for are Cursor and Windsurf as
 * they don't yet support working with Resource URIs.
 *
 * Ref Cursor: https://forum.cursor.com/t/cursor-mcp-resource-feature-support/50987
 * JIRA: https://jira.mongodb.org/browse/MCP-104 */
export type AvailableExport = Pick<StoredExport, "exportName" | "exportTitle" | "exportURI" | "exportPath">;

export type ExportsManagerConfig = Pick<UserConfig, "exportsPath" | "exportTimeoutMs" | "exportCleanupIntervalMs">;

type ExportsManagerEvents = {
    closed: [];
    "export-expired": [string];
    "export-available": [string];
};

export class ExportsManager extends EventEmitter<ExportsManagerEvents> {
    private storedExports: Record<StoredExport["exportName"], StoredExport> = {};
    private exportsCleanupInProgress: boolean = false;
    private exportsCleanupInterval?: NodeJS.Timeout;
    private readonly shutdownController: AbortController = new AbortController();

    private constructor(
        private readonly exportsDirectoryPath: string,
        private readonly config: ExportsManagerConfig,
        private readonly logger: LoggerBase
    ) {
        super();
    }

    public get availableExports(): AvailableExport[] {
        this.assertIsNotShuttingDown();
        return Object.values(this.storedExports)
            .filter((storedExport) => {
                return (
                    storedExport.exportStatus === "ready" &&
                    !isExportExpired(storedExport.exportCreatedAt, this.config.exportTimeoutMs)
                );
            })
            .map(({ exportName, exportTitle, exportURI, exportPath }) => ({
                exportName,
                exportTitle,
                exportURI,
                exportPath,
            }));
    }

    protected init(): void {
        if (!this.exportsCleanupInterval) {
            this.exportsCleanupInterval = setInterval(
                () => void this.cleanupExpiredExports(),
                this.config.exportCleanupIntervalMs
            );
        }
    }

    public async close(): Promise<void> {
        if (this.shutdownController.signal.aborted) {
            return;
        }
        try {
            clearInterval(this.exportsCleanupInterval);
            this.shutdownController.abort();
            await fs.rm(this.exportsDirectoryPath, { force: true, recursive: true });
            this.emit("closed");
        } catch (error) {
            this.logger.error({
                id: LogId.exportCloseError,
                context: "Error while closing ExportsManager",
                message: error instanceof Error ? error.message : String(error),
            });
        }
    }

    public async readExport(exportName: string): Promise<{ content: string; docsTransformed: number }> {
        try {
            this.assertIsNotShuttingDown();
            exportName = decodeAndNormalize(exportName);
            const exportHandle = this.storedExports[exportName];
            if (!exportHandle) {
                throw new Error("Requested export has either expired or does not exist.");
            }

            if (exportHandle.exportStatus === "in-progress") {
                throw new Error("Requested export is still being generated. Try again later.");
            }

            const { exportPath, docsTransformed } = exportHandle;

            return {
                content: await fs.readFile(exportPath, { encoding: "utf8", signal: this.shutdownController.signal }),
                docsTransformed,
            };
        } catch (error) {
            this.logger.error({
                id: LogId.exportReadError,
                context: `Error when reading export - ${exportName}`,
                message: error instanceof Error ? error.message : String(error),
            });
            throw error;
        }
    }

    public async createJSONExport({
        input,
        exportName,
        exportTitle,
        jsonExportFormat,
    }: {
        input: FindCursor | AggregationCursor;
        exportName: string;
        exportTitle: string;
        jsonExportFormat: JSONExportFormat;
    }): Promise<AvailableExport> {
        try {
            this.assertIsNotShuttingDown();
            const exportNameWithExtension = decodeAndNormalize(ensureExtension(exportName, "json"));
            if (this.storedExports[exportNameWithExtension]) {
                return Promise.reject(
                    new Error("Export with same name is either already available or being generated.")
                );
            }
            const exportURI = `exported-data://${encodeURIComponent(exportNameWithExtension)}`;
            const exportFilePath = path.join(this.exportsDirectoryPath, exportNameWithExtension);
            const inProgressExport: InProgressExport = (this.storedExports[exportNameWithExtension] = {
                exportName: exportNameWithExtension,
                exportTitle,
                exportPath: exportFilePath,
                exportURI: exportURI,
                exportStatus: "in-progress",
            });

            void this.startExport({ input, jsonExportFormat, inProgressExport });
            return Promise.resolve(inProgressExport);
        } catch (error) {
            this.logger.error({
                id: LogId.exportCreationError,
                context: "Error when registering JSON export request",
                message: error instanceof Error ? error.message : String(error),
            });
            throw error;
        }
    }

    private async startExport({
        input,
        jsonExportFormat,
        inProgressExport,
    }: {
        input: FindCursor | AggregationCursor;
        jsonExportFormat: JSONExportFormat;
        inProgressExport: InProgressExport;
    }): Promise<void> {
        try {
            let pipeSuccessful = false;
            let docsTransformed = 0;
            try {
                await fs.mkdir(this.exportsDirectoryPath, { recursive: true });
                const outputStream = createWriteStream(inProgressExport.exportPath);
                const ejsonTransform = this.docToEJSONStream(this.getEJSONOptionsForFormat(jsonExportFormat));
                await pipeline([input.stream(), ejsonTransform, outputStream], {
                    signal: this.shutdownController.signal,
                });
                docsTransformed = ejsonTransform.docsTransformed;
                pipeSuccessful = true;
            } catch (error) {
                // If the pipeline errors out then we might end up with
                // partial and incorrect export so we remove it entirely.
                delete this.storedExports[inProgressExport.exportName];
                // do not block the user, just delete the file in the background
                void this.silentlyRemoveExport(
                    inProgressExport.exportPath,
                    LogId.exportCreationCleanupError,
                    `Error when removing incomplete export ${inProgressExport.exportName}`
                );
                throw error;
            } finally {
                if (pipeSuccessful) {
                    this.storedExports[inProgressExport.exportName] = {
                        ...inProgressExport,
                        exportCreatedAt: Date.now(),
                        exportStatus: "ready",
                        docsTransformed,
                    };
                    this.emit("export-available", inProgressExport.exportURI);
                }
                void input.close();
            }
        } catch (error) {
            this.logger.error({
                id: LogId.exportCreationError,
                context: `Error when generating JSON export for ${inProgressExport.exportName}`,
                message: error instanceof Error ? error.message : String(error),
            });
        }
    }

    private getEJSONOptionsForFormat(format: JSONExportFormat): EJSONOptions | undefined {
        switch (format) {
            case "relaxed":
                return { relaxed: true };
            case "canonical":
                return { relaxed: false };
            default:
                return undefined;
        }
    }

    private docToEJSONStream(ejsonOptions: EJSONOptions | undefined): Transform & { docsTransformed: number } {
        let docsTransformed = 0;
        const result = Object.assign(
            new Transform({
                objectMode: true,
                transform(chunk: unknown, encoding, callback): void {
                    try {
                        const doc = EJSON.stringify(chunk, undefined, undefined, ejsonOptions);
                        if (docsTransformed === 0) {
                            this.push("[" + doc);
                        } else {
                            this.push(",\n" + doc);
                        }
                        docsTransformed++;
                        callback();
                    } catch (err) {
                        callback(err as Error);
                    }
                },
                flush(callback): void {
                    if (docsTransformed === 0) {
                        this.push("[]");
                    } else {
                        this.push("]");
                    }
                    result.docsTransformed = docsTransformed;
                    callback();
                },
            }),
            { docsTransformed }
        );

        return result;
    }

    private async cleanupExpiredExports(): Promise<void> {
        if (this.exportsCleanupInProgress) {
            return;
        }

        this.exportsCleanupInProgress = true;
        try {
            // first, unregister all exports that are expired, so they are not considered anymore for reading
            const exportsForCleanup: ReadyExport[] = [];
            for (const expiredExport of Object.values(this.storedExports)) {
                if (
                    expiredExport.exportStatus === "ready" &&
                    isExportExpired(expiredExport.exportCreatedAt, this.config.exportTimeoutMs)
                ) {
                    exportsForCleanup.push(expiredExport);
                    delete this.storedExports[expiredExport.exportName];
                }
            }

            // and then remove them (slow operation potentially) from disk.
            const allDeletionPromises: Promise<void>[] = [];
            for (const { exportPath, exportName } of exportsForCleanup) {
                allDeletionPromises.push(
                    this.silentlyRemoveExport(
                        exportPath,
                        LogId.exportCleanupError,
                        `Considerable error when removing export ${exportName}`
                    )
                );
            }

            await Promise.allSettled(allDeletionPromises);
        } catch (error) {
            this.logger.error({
                id: LogId.exportCleanupError,
                context: "Error when cleaning up exports",
                message: error instanceof Error ? error.message : String(error),
            });
        } finally {
            this.exportsCleanupInProgress = false;
        }
    }

    private async silentlyRemoveExport(exportPath: string, logId: MongoLogId, logContext: string): Promise<void> {
        try {
            await fs.unlink(exportPath);
        } catch (error) {
            // If the file does not exist or the containing directory itself
            // does not exist then we can safely ignore that error anything else
            // we need to flag.
            if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
                this.logger.error({
                    id: logId,
                    context: logContext,
                    message: error instanceof Error ? error.message : String(error),
                });
            }
        }
    }

    private assertIsNotShuttingDown(): void {
        if (this.shutdownController.signal.aborted) {
            throw new Error("ExportsManager is shutting down.");
        }
    }

    static init(
        config: ExportsManagerConfig,
        logger: LoggerBase,
        sessionId = new ObjectId().toString()
    ): ExportsManager {
        const exportsDirectoryPath = path.join(config.exportsPath, sessionId);
        const exportsManager = new ExportsManager(exportsDirectoryPath, config, logger);
        exportsManager.init();
        return exportsManager;
    }
}

export function decodeAndNormalize(text: string): string {
    return decodeURIComponent(text).normalize("NFKC");
}

/**
 * Ensures the path ends with the provided extension */
export function ensureExtension(pathOrName: string, extension: string): string {
    const extWithDot = extension.startsWith(".") ? extension : `.${extension}`;
    if (pathOrName.endsWith(extWithDot)) {
        return pathOrName;
    }
    return `${pathOrName}${extWithDot}`;
}

export function isExportExpired(createdAt: number, exportTimeoutMs: number): boolean {
    return Date.now() - createdAt > exportTimeoutMs;
}
