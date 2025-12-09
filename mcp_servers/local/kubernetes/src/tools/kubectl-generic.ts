import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import {
  contextParameter,
  namespaceParameter,
} from "../models/common-parameters.js";

export const kubectlGenericSchema = {
  name: "kubectl_generic",
  description:
    "Execute any kubectl command with the provided arguments and flags",
  annotations: {
    destructiveHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      command: {
        type: "string",
        description:
          "The kubectl command to execute (e.g. patch, rollout, top)",
      },
      subCommand: {
        type: "string",
        description: "Subcommand if applicable (e.g. 'history' for rollout)",
      },
      resourceType: {
        type: "string",
        description: "Resource type (e.g. pod, deployment)",
      },
      name: {
        type: "string",
        description: "Resource name",
      },
      namespace: namespaceParameter,
      outputFormat: {
        type: "string",
        description: "Output format (e.g. json, yaml, wide)",
        enum: ["json", "yaml", "wide", "name", "custom"],
      },
      flags: {
        type: "object",
        description: "Command flags as key-value pairs",
        additionalProperties: true,
      },
      args: {
        type: "array",
        items: { type: "string" },
        description: "Additional command arguments",
      },
      context: contextParameter,
    },
    required: ["command"],
  },
};

export async function kubectlGeneric(
  k8sManager: KubernetesManager,
  input: {
    command: string;
    subCommand?: string;
    resourceType?: string;
    name?: string;
    namespace?: string;
    outputFormat?: string;
    flags?: Record<string, any>;
    args?: string[];
    context?: string;
  }
) {
  try {
    // Start building the kubectl command
    const command = "kubectl";
    const cmdArgs: string[] = [input.command];

    // Add subcommand if provided
    if (input.subCommand) {
      cmdArgs.push(input.subCommand);
    }

    // Add resource type if provided
    if (input.resourceType) {
      cmdArgs.push(input.resourceType);
    }

    // Add resource name if provided
    if (input.name) {
      cmdArgs.push(input.name);
    }

    // Add namespace if provided
    if (input.namespace) {
      cmdArgs.push(`--namespace=${input.namespace}`);
    }

    // Add output format if provided
    if (input.outputFormat) {
      cmdArgs.push(`-o=${input.outputFormat}`);
    }

    // Add any provided flags
    if (input.flags) {
      for (const [key, value] of Object.entries(input.flags)) {
        if (value === true) {
          // Handle boolean flags
          cmdArgs.push(`--${key}`);
        } else if (value !== false && value !== null && value !== undefined) {
          // Skip false/null/undefined values, add others as --key=value
          cmdArgs.push(`--${key}=${value}`);
        }
      }
    }

    // Add any additional arguments
    if (input.args && input.args.length > 0) {
      cmdArgs.push(...input.args);
    }

    // Add context if provided
    if (input.context) {
      cmdArgs.push("--context", input.context);
    }

    // Execute the command
    try {
      console.error(`Executing: kubectl ${cmdArgs.join(" ")}`);
      const result = execFileSync(command, cmdArgs, {
        encoding: "utf8",
        maxBuffer: getSpawnMaxBuffer(),
        env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
      });

      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
      };
    } catch (error: any) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to execute kubectl command: ${error.message}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      throw error;
    }

    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl command: ${error.message}`
    );
  }
}
