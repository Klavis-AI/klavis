import type {
    CompleteResourceTemplateCallback,
    ListResourcesCallback,
    ReadResourceTemplateCallback,
} from "@modelcontextprotocol/sdk/server/mcp.js";
import { ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { Server } from "../../server.js";
import { LogId } from "../../common/logger.js";
import type { Session } from "../../common/session.js";
import { formatUntrustedData } from "../../tools/tool.js";

export class ExportedData {
    private readonly name = "exported-data";
    private readonly description = "Data files exported in the current session.";
    private readonly uri = "exported-data://{exportName}";
    private server?: Server;

    constructor(private readonly session: Session) {}

    public register(server: Server): void {
        this.server = server;
        this.server.mcpServer.registerResource(
            this.name,
            new ResourceTemplate(this.uri, {
                /**
                 * A few clients have the capability of listing templated
                 * resources as well and this callback provides support for that
                 * */
                list: this.listResourcesCallback,
                /**
                 * This is to provide auto completion when user starts typing in
                 * value for template variable, in our case, exportName */
                complete: {
                    exportName: this.autoCompleteExportName,
                },
            }),
            { description: this.description },
            this.readResourceCallback
        );
        this.session.exportsManager.on("export-available", (uri: string): void => {
            server.sendResourceListChanged();
            server.sendResourceUpdated(uri);
        });
        this.session.exportsManager.on("export-expired", (): void => {
            server.sendResourceListChanged();
        });
    }

    private listResourcesCallback: ListResourcesCallback = () => {
        try {
            return {
                resources: this.session.exportsManager.availableExports.map(
                    ({ exportName, exportTitle, exportURI }) => ({
                        name: exportName,
                        description: exportTitle,
                        uri: exportURI,
                        mimeType: "application/json",
                    })
                ),
            };
        } catch (error) {
            this.session.logger.error({
                id: LogId.exportedDataListError,
                context: "Error when listing exported data resources",
                message: error instanceof Error ? error.message : String(error),
            });
            return {
                resources: [],
            };
        }
    };

    private autoCompleteExportName: CompleteResourceTemplateCallback = (value) => {
        try {
            return this.session.exportsManager.availableExports
                .filter(({ exportName, exportTitle }) => {
                    const lcExportName = exportName.toLowerCase();
                    const lcExportTitle = exportTitle.toLowerCase();
                    const lcValue = value.toLowerCase();
                    return lcExportName.startsWith(lcValue) || lcExportTitle.includes(lcValue);
                })
                .map(({ exportName }) => exportName);
        } catch (error) {
            this.session.logger.error({
                id: LogId.exportedDataAutoCompleteError,
                context: "Error when autocompleting exported data",
                message: error instanceof Error ? error.message : String(error),
            });
            return [];
        }
    };

    private readResourceCallback: ReadResourceTemplateCallback = async (url, { exportName }) => {
        try {
            if (typeof exportName !== "string") {
                throw new Error("Cannot retrieve exported data, exportName not provided.");
            }

            const { content, docsTransformed } = await this.session.exportsManager.readExport(exportName);

            const text = formatUntrustedData(`The exported data contains ${docsTransformed} documents.`, content)
                .map((t) => t.text)
                .join("\n");

            return {
                contents: [
                    {
                        uri: url.href,
                        text,
                        mimeType: "application/json",
                    },
                ],
            };
        } catch (error) {
            return {
                contents: [
                    {
                        uri: url.href,
                        text: `Error reading ${url.href}: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    };
}
