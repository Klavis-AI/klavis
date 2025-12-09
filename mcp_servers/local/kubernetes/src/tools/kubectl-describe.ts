import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import {
  namespaceParameter,
  contextParameter,
} from "../models/common-parameters.js";

export const kubectlDescribeSchema = {
  name: "kubectl_describe",
  description:
    "Describe Kubernetes resources by resource type, name, and optionally namespace",
  annotations: {
    readOnlyHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      resourceType: {
        type: "string",
        description:
          "Type of resource to describe (e.g., pods, deployments, services, etc.)",
      },
      name: {
        type: "string",
        description: "Name of the resource to describe",
      },
      namespace: namespaceParameter,
      context: contextParameter,
      allNamespaces: {
        type: "boolean",
        description: "If true, describe resources across all namespaces",
        default: false,
      },
    },
    required: ["resourceType", "name"],
  },
} as const;

export async function kubectlDescribe(
  k8sManager: KubernetesManager,
  input: {
    resourceType: string;
    name: string;
    namespace?: string;
    allNamespaces?: boolean;
    context?: string;
  }
) {
  try {
    const resourceType = input.resourceType.toLowerCase();
    const name = input.name;
    const namespace = input.namespace || "default";
    const allNamespaces = input.allNamespaces || false;
    const context = input.context || "";

    // Build the kubectl command
    const command = "kubectl";
    const args = ["describe", resourceType, name];

    // Add namespace flag unless all namespaces is specified
    if (allNamespaces) {
      args.push("--all-namespaces");
    } else if (namespace && !isNonNamespacedResource(resourceType)) {
      args.push("-n", namespace);
    }

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

      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
      };
    } catch (error: any) {
      if (error.status === 404 || error.message.includes("not found")) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  error: `Resource ${resourceType}/${name} not found`,
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
        `Failed to describe resource: ${error.message}`
      );
    }
  } catch (error: any) {
    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl describe command: ${error.message}`
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
