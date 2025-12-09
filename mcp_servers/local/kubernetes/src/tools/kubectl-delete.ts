import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import {
  contextParameter,
  namespaceParameter,
} from "../models/common-parameters.js";

export const kubectlDeleteSchema = {
  name: "kubectl_delete",
  description:
    "Delete Kubernetes resources by resource type, name, labels, or from a manifest file",
  annotations: {
    destructiveHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      resourceType: {
        type: "string",
        description:
          "Type of resource to delete (e.g., pods, deployments, services, etc.)",
      },
      name: {
        type: "string",
        description: "Name of the resource to delete",
      },
      namespace: namespaceParameter,
      labelSelector: {
        type: "string",
        description:
          "Delete resources matching this label selector (e.g. 'app=nginx')",
      },
      manifest: {
        type: "string",
        description: "YAML manifest defining resources to delete (optional)",
      },
      filename: {
        type: "string",
        description: "Path to a YAML file to delete resources from (optional)",
      },
      allNamespaces: {
        type: "boolean",
        description: "If true, delete resources across all namespaces",
        default: false,
      },
      force: {
        type: "boolean",
        description:
          "If true, immediately remove resources from API and bypass graceful deletion",
        default: false,
      },
      gracePeriodSeconds: {
        type: "number",
        description:
          "Period of time in seconds given to the resource to terminate gracefully",
      },
      context: contextParameter,
    },
    required: ["resourceType", "name", "namespace"],
  },
} as const;

export async function kubectlDelete(
  k8sManager: KubernetesManager,
  input: {
    resourceType?: string;
    name?: string;
    namespace?: string;
    labelSelector?: string;
    manifest?: string;
    filename?: string;
    allNamespaces?: boolean;
    force?: boolean;
    gracePeriodSeconds?: number;
    context?: string;
  }
) {
  try {
    // Validate input - need at least one way to identify resources
    if (!input.resourceType && !input.manifest && !input.filename) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        "Either resourceType, manifest, or filename must be provided"
      );
    }

    // If resourceType is provided, need either name or labelSelector
    if (input.resourceType && !input.name && !input.labelSelector) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        "When using resourceType, either name or labelSelector must be provided"
      );
    }

    const namespace = input.namespace || "default";
    const allNamespaces = input.allNamespaces || false;
    const force = input.force || false;
    const context = input.context || "";

    const command = "kubectl";
    const args = ["delete"];
    let tempFile: string | null = null;

    // Handle deleting from manifest or file
    if (input.manifest) {
      // Create temporary file for the manifest
      const tmpDir = os.tmpdir();
      tempFile = path.join(tmpDir, `delete-manifest-${Date.now()}.yaml`);
      fs.writeFileSync(tempFile, input.manifest);
      args.push("-f", tempFile);
    } else if (input.filename) {
      args.push("-f", input.filename);
    } else {
      // Handle deleting by resource type and name/selector
      args.push(input.resourceType!);

      if (input.name) {
        args.push(input.name);
      }

      if (input.labelSelector) {
        args.push("-l", input.labelSelector);
      }
    }

    // Add namespace flags
    if (allNamespaces) {
      args.push("--all-namespaces");
    } else if (
      namespace &&
      input.resourceType &&
      !isNonNamespacedResource(input.resourceType)
    ) {
      args.push("-n", namespace);
    }

    // Add force flag if requested
    if (force) {
      args.push("--force");
    }

    // Add grace period if specified
    if (input.gracePeriodSeconds !== undefined) {
      args.push(`--grace-period=${input.gracePeriodSeconds}`);
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

      if (error.status === 404 || error.message.includes("not found")) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  error: `Resource not found`,
                  status: "not_found",
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }

      throw new McpError(
        ErrorCode.InternalError,
        `Failed to delete resource: ${error.message}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      throw error;
    }

    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl delete command: ${error.message}`
    );
  }
}

// Helper function to determine if a resource is non-namespaced
function isNonNamespacedResource(resourceType: string): boolean {
  const nonNamespacedResources = [
    "nodes",
    "node",
    "no",
    "namespaces",
    "namespace",
    "ns",
    "persistentvolumes",
    "pv",
    "storageclasses",
    "sc",
    "clusterroles",
    "clusterrolebindings",
    "customresourcedefinitions",
    "crd",
    "crds",
  ];

  return nonNamespacedResources.includes(resourceType.toLowerCase());
}
