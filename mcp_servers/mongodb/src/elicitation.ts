import type { ElicitRequestFormParams } from "@modelcontextprotocol/sdk/types.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export class Elicitation {
    private readonly server: McpServer["server"];
    constructor({ server }: { server: McpServer["server"] }) {
        this.server = server;
    }

    /**
     * Checks if the client supports elicitation capabilities.
     * @returns True if the client supports elicitation, false otherwise.
     */
    public supportsElicitation(): boolean {
        const clientCapabilities = this.server.getClientCapabilities();
        return clientCapabilities?.elicitation !== undefined;
    }

    /**
     * Requests a boolean confirmation from the user.
     * @param message - The message to display to the user.
     * @returns True if the user confirms the action or the client does not support elicitation, false otherwise.
     */
    public async requestConfirmation(message: string): Promise<boolean> {
        if (!this.supportsElicitation()) {
            return true;
        }

        const result = await this.server.elicitInput({
            mode: "form",
            message,
            requestedSchema: Elicitation.CONFIRMATION_SCHEMA,
        });
        return result.action === "accept" && result.content?.confirmation === "Yes";
    }

    /**
     * The schema for the confirmation question.
     * TODO: In the future would be good to use Zod 4's toJSONSchema() to generate the schema.
     */
    public static CONFIRMATION_SCHEMA = {
        type: "object" as const,
        properties: {
            confirmation: {
                type: "string" as const,
                title: "Would you like to confirm?",
                description: "Would you like to confirm?",
                enum: ["Yes", "No"],
                enumNames: ["Yes, I confirm", "No, I do not confirm"],
            },
        },
        required: ["confirmation"],
    } satisfies ElicitRequestFormParams["requestedSchema"];
}
