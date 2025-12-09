import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import { contextParameter, namespaceParameter, dryRunParameter } from "../models/common-parameters.js";

export const kubectlApplySchema = {
  name: "kubectl_apply",
  description: "Apply a Kubernetes YAML manifest from a string or file",
  inputSchema: {
    type: "object",
    properties: {
      manifest: {
        type: "string",
        description: "YAML manifest to apply",
      },
      filename: {
        type: "string",
        description:
          "Path to a YAML file to apply (optional - use either manifest or filename)",
      },
      namespace: namespaceParameter,
      dryRun: dryRunParameter,
      force: {
        type: "boolean",
        description:
          "If true, immediately remove resources from API and bypass graceful deletion",
        default: false,
      },
      context: contextParameter,
    },
    required: [],
  },
} as const;

export async function kubectlApply(
  k8sManager: KubernetesManager,
  input: {
    manifest?: string;
    filename?: string;
    namespace?: string;
    dryRun?: boolean;
    force?: boolean;
    context?: string;
  }
) {
  try {
    if (!input.manifest && !input.filename) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        "Either manifest or filename must be provided"
      );
    }

    const namespace = input.namespace || "default";
    const dryRun = input.dryRun || false;
    const force = input.force || false;
    const context = input.context || "";

    let command = "kubectl";
    let args = ["apply"];
    let tempFile: string | null = null;

    // Process manifest content if provided
    if (input.manifest) {
      // Create temporary file for the manifest
      const tmpDir = os.tmpdir();
      tempFile = path.join(tmpDir, `manifest-${Date.now()}.yaml`);
      fs.writeFileSync(tempFile, input.manifest);
      args.push("-f", tempFile);
    } else if (input.filename) {
      args.push("-f", input.filename);
    }

    // Add namespace
    args.push("-n", namespace);

    // Add dry-run flag if requested
    if (dryRun) {
      args.push("--dry-run=client");
    }

    // Add force flag if requested
    if (force) {
      args.push("--force");
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
        `Failed to apply manifest: ${error.message}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      throw error;
    }

    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl apply command: ${error.message}`
    );
  }
}
