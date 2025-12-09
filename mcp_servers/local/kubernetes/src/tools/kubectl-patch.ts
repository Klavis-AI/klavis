import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import { contextParameter, dryRunParameter, namespaceParameter } from "../models/common-parameters.js";

export const kubectlPatchSchema = {
  name: "kubectl_patch",
  description:
    "Update field(s) of a resource using strategic merge patch, JSON merge patch, or JSON patch",
  inputSchema: {
    type: "object",
    properties: {
      resourceType: {
        type: "string",
        description:
          "Type of resource to patch (e.g., pods, deployments, services)",
      },
      name: {
        type: "string",
        description: "Name of the resource to patch",
      },
      namespace: namespaceParameter,
      patchType: {
        type: "string",
        description: "Type of patch to apply",
        enum: ["strategic", "merge", "json"],
        default: "strategic",
      },
      patchData: {
        type: "object",
        description: "Patch data as a JSON object",
      },
      patchFile: {
        type: "string",
        description:
          "Path to a file containing the patch data (alternative to patchData)",
      },
      dryRun: dryRunParameter,
      context: contextParameter,
    },
    required: ["resourceType", "name"],
  },
};

export async function kubectlPatch(
  k8sManager: KubernetesManager,
  input: {
    resourceType: string;
    name: string;
    namespace?: string;
    patchType?: "strategic" | "merge" | "json";
    patchData?: object;
    patchFile?: string;
    dryRun?: boolean;
    context?: string;
  }
) {
  try {
    if (!input.patchData && !input.patchFile) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        "Either patchData or patchFile must be provided"
      );
    }

    const namespace = input.namespace || "default";
    const patchType = input.patchType || "strategic";
    const dryRun = input.dryRun || false;
    const context = input.context || "";
    let tempFile: string | null = null;

    const command = "kubectl";
    const args = ["patch", input.resourceType, input.name, "-n", namespace];

    // Add patch type flag
    switch (patchType) {
      case "strategic":
        args.push("--type", "strategic");
        break;
      case "merge":
        args.push("--type", "merge");
        break;
      case "json":
        args.push("--type", "json");
        break;
      default:
        args.push("--type", "strategic");
    }

    // Handle patch data
    if (input.patchData) {
      // Create a temporary file for the patch data
      const tmpDir = os.tmpdir();
      tempFile = path.join(tmpDir, `patch-${Date.now()}.json`);
      fs.writeFileSync(tempFile, JSON.stringify(input.patchData));
      args.push("--patch-file", tempFile);
    } else if (input.patchFile) {
      args.push("--patch-file", input.patchFile);
    }

    // Add dry-run flag if requested
    if (dryRun) {
      args.push("--dry-run=client");
    }

    // Add context if provided
    if (context) {
      args.push("--context", context);
    }

    // Execute the command
    try {
      const result = execFileSync(command, args, {
        encoding: "utf8",
        maxBuffer: getSpawnMaxBuffer(),
        env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
      });

      // Clean up temp file if created
      if (tempFile) {
        try {
          fs.unlinkSync(tempFile);
        } catch (err) {
          console.warn(`Failed to delete temporary file ${tempFile}: ${err}`);
        }
      }

      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
      };
    } catch (error: any) {
      // Clean up temp file if created, even if command failed
      if (tempFile) {
        try {
          fs.unlinkSync(tempFile);
        } catch (err) {
          console.warn(`Failed to delete temporary file ${tempFile}: ${err}`);
        }
      }

      throw new McpError(
        ErrorCode.InternalError,
        `Failed to patch resource: ${error.message}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      throw error;
    }

    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl patch command: ${error.message}`
    );
  }
}
