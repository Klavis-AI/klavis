import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import { contextParameter, namespaceParameter } from "../models/common-parameters.js";

export const kubectlRolloutSchema = {
  name: "kubectl_rollout",
  description:
    "Manage the rollout of a resource (e.g., deployment, daemonset, statefulset)",
  inputSchema: {
    type: "object",
    properties: {
      subCommand: {
        type: "string",
        description: "Rollout subcommand to execute",
        enum: ["history", "pause", "restart", "resume", "status", "undo"],
        default: "status",
      },
      resourceType: {
        type: "string",
        description: "Type of resource to manage rollout for",
        enum: ["deployment", "daemonset", "statefulset"],
        default: "deployment",
      },
      name: {
        type: "string",
        description: "Name of the resource",
      },
      namespace: namespaceParameter,
      revision: {
        type: "number",
        description: "Revision to rollback to (for undo subcommand)",
      },
      toRevision: {
        type: "number",
        description: "Revision to roll back to (for history subcommand)",
      },
      timeout: {
        type: "string",
        description:
          "The length of time to wait before giving up (e.g., '30s', '1m', '2m30s')",
      },
      watch: {
        type: "boolean",
        description: "Watch the rollout status in real-time until completion",
        default: false,
      },
      context: contextParameter,
    },
    required: ["subCommand", "resourceType", "name", "namespace"],
  },
};

export async function kubectlRollout(
  k8sManager: KubernetesManager,
  input: {
    subCommand: "history" | "pause" | "restart" | "resume" | "status" | "undo";
    resourceType: "deployment" | "daemonset" | "statefulset";
    name: string;
    namespace?: string;
    revision?: number;
    toRevision?: number;
    timeout?: string;
    watch?: boolean;
    context?: string;
  }
) {
  try {
    const namespace = input.namespace || "default";
    const watch = input.watch || false;
    const context = input.context || "";

    const command = "kubectl";
    const args = [
      "rollout",
      input.subCommand,
      `${input.resourceType}/${input.name}`,
      "-n",
      namespace,
    ];

    // Add revision for undo
    if (input.subCommand === "undo" && input.revision !== undefined) {
      args.push(`--to-revision=${input.revision}`);
    }

    // Add revision for history
    if (input.subCommand === "history" && input.toRevision !== undefined) {
      args.push(`--revision=${input.toRevision}`);
    }

    // Add timeout if specified
    if (input.timeout) {
      args.push(`--timeout=${input.timeout}`);
    }

    // Add context if provided
    if (context) {
      args.push("--context", context);
    }

    // Execute the command
    try {
      // For status command with watch flag, we need to handle it differently
      // since it's meant to be interactive and follow the progress
      if (input.subCommand === "status" && watch) {
        args.push("--watch");
        // For watch we are limited in what we can do - we'll execute it with a reasonable timeout
        // and capture the output until that point
        const result = execFileSync(command, args, {
          encoding: "utf8",
          maxBuffer: getSpawnMaxBuffer(),
          timeout: 15000, // Reduced from 30 seconds to 15 seconds
          env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
        });

        return {
          content: [
            {
              type: "text",
              text:
                result +
                "\n\nNote: Watch operation was limited to 15 seconds. The rollout may still be in progress.",
            },
          ],
        };
      } else {
        const result = execFileSync(command, args, {
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
      }
    } catch (error: any) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to execute rollout command: ${error.message}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      throw error;
    }

    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl rollout command: ${error.message}`
    );
  }
}
