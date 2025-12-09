import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import * as yaml from "js-yaml";
import {
  contextParameter,
  namespaceParameter,
} from "../models/common-parameters.js";

export const kubectlGetSchema = {
  name: "kubectl_get",
  description:
    "Get or list Kubernetes resources by resource type, name, and optionally namespace",
  annotations: {
    readOnlyHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      resourceType: {
        type: "string",
        description:
          "Type of resource to get (e.g., pods, deployments, services, configmaps, events, etc.)",
      },
      name: {
        type: "string",
        description:
          "Name of the resource (optional - if not provided, lists all resources of the specified type)",
      },
      namespace: namespaceParameter,
      output: {
        type: "string",
        enum: ["json", "yaml", "wide", "name", "custom"],
        description: "Output format",
        default: "json",
      },
      allNamespaces: {
        type: "boolean",
        description: "If true, list resources across all namespaces",
        default: false,
      },
      labelSelector: {
        type: "string",
        description: "Filter resources by label selector (e.g. 'app=nginx')",
      },
      fieldSelector: {
        type: "string",
        description:
          "Filter resources by field selector (e.g. 'metadata.name=my-pod')",
      },
      sortBy: {
        type: "string",
        description:
          "Sort events by a field (default: lastTimestamp). Only applicable for events.",
      },
      context: contextParameter,
    },
    required: ["resourceType", "name", "namespace"],
  },
} as const;

export async function kubectlGet(
  k8sManager: KubernetesManager,
  input: {
    resourceType: string;
    name?: string;
    namespace?: string;
    output?: string;
    allNamespaces?: boolean;
    labelSelector?: string;
    fieldSelector?: string;
    sortBy?: string;
    context?: string;
  }
) {
  try {
    const resourceType = input.resourceType.toLowerCase();
    const name = input.name || "";
    const namespace = input.namespace || "default";
    const output = input.output || "json";
    const allNamespaces = input.allNamespaces || false;
    const labelSelector = input.labelSelector || "";
    const fieldSelector = input.fieldSelector || "";
    const sortBy = input.sortBy;
    const context = input.context || "";

    // Build the kubectl command
    const command = "kubectl";
    const args = ["get", resourceType];

    // Add name if provided
    if (name) {
      args.push(name);
    }

    // For events, default to all namespaces unless explicitly specified
    const shouldShowAllNamespaces =
      resourceType === "events"
        ? input.namespace
          ? false
          : true
        : allNamespaces;

    // Add namespace flag unless all namespaces is specified
    if (shouldShowAllNamespaces) {
      args.push("--all-namespaces");
    } else if (namespace && !isNonNamespacedResource(resourceType)) {
      args.push("-n", namespace);
    }

    if (context) {
      args.push("--context", context);
    }

    // Add label selector if provided
    if (labelSelector) {
      args.push("-l", labelSelector);
    }

    // Add field selector if provided
    if (fieldSelector) {
      args.push(`--field-selector=${fieldSelector}`);
    }

    // Add sort-by for events
    if (resourceType === "events" && sortBy) {
      args.push(`--sort-by=.${sortBy}`);
    } else if (resourceType === "events") {
      args.push(`--sort-by=.lastTimestamp`);
    }

    // Add output format
    if (output === "json") {
      args.push("-o", "json");
    } else if (output === "yaml") {
      args.push("-o", "yaml");
    } else if (output === "wide") {
      args.push("-o", "wide");
    } else if (output === "name") {
      args.push("-o", "name");
    } else if (output === "custom") {
      if (resourceType === "events") {
        args.push(
          "-o",
          "'custom-columns=LASTSEEN:.lastTimestamp,TYPE:.type,REASON:.reason,OBJECT:.involvedObject.name,MESSAGE:.message'"
        );
      } else {
        args.push(
          "-o",
          "'custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace,STATUS:.status.phase,AGE:.metadata.creationTimestamp'"
        );
      }
    }

    // Execute the command
    try {
      const result = execFileSync(command, args, {
        encoding: "utf8",
        maxBuffer: getSpawnMaxBuffer(),
        env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
      });

      // Apply secrets masking if enabled and dealing with secrets
      const shouldMaskSecrets =
        process.env.MASK_SECRETS !== "false" &&
        (resourceType === "secrets" || resourceType === "secret");

      let processedResult = result;
      if (shouldMaskSecrets) {
        processedResult = maskSecretsData(result, output);
      }

      // Format the results for better readability
      const isListOperation = !name;
      if (isListOperation && output === "json") {
        try {
          // Parse JSON and extract key information
          const parsed = JSON.parse(processedResult);

          if (parsed.kind && parsed.kind.endsWith("List") && parsed.items) {
            if (resourceType === "events") {
              const formattedEvents = parsed.items.map((event: any) => ({
                type: event.type || "",
                reason: event.reason || "",
                message: event.message || "",
                involvedObject: {
                  kind: event.involvedObject?.kind || "",
                  name: event.involvedObject?.name || "",
                  namespace: event.involvedObject?.namespace || "",
                },
                firstTimestamp: event.firstTimestamp || "",
                lastTimestamp: event.lastTimestamp || "",
                count: event.count || 0,
              }));

              return {
                content: [
                  {
                    type: "text",
                    text: JSON.stringify({ events: formattedEvents }, null, 2),
                  },
                ],
              };
            } else {
              const items = parsed.items.map((item: any) => ({
                name: item.metadata?.name || "",
                namespace: item.metadata?.namespace || "",
                kind: item.kind || resourceType,
                status: getResourceStatus(item),
                createdAt: item.metadata?.creationTimestamp,
              }));

              return {
                content: [
                  {
                    type: "text",
                    text: JSON.stringify({ items }, null, 2),
                  },
                ],
              };
            }
          }
        } catch (parseError) {
          // If JSON parsing fails, return the raw output
          console.error("Error parsing JSON:", parseError);
        }
      }

      return {
        content: [
          {
            type: "text",
            text: processedResult,
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
                  error: `Resource ${resourceType}${
                    name ? `/${name}` : ""
                  } not found`,
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
        `Failed to get resource: ${error.message}`
      );
    }
  } catch (error: any) {
    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl get command: ${error.message}`
    );
  }
}

// Extract status from various resource types
function getResourceStatus(resource: any): string {
  if (!resource) return "Unknown";

  // Pod status
  if (resource.status?.phase) {
    return resource.status.phase;
  }

  // Deployment, ReplicaSet, StatefulSet status
  if (resource.status?.readyReplicas !== undefined) {
    const ready = resource.status.readyReplicas || 0;
    const total = resource.status.replicas || 0;
    return `${ready}/${total} ready`;
  }

  // Service status
  if (resource.spec?.type) {
    return resource.spec.type;
  }

  // Node status
  if (resource.status?.conditions) {
    const readyCondition = resource.status.conditions.find(
      (c: any) => c.type === "Ready"
    );
    if (readyCondition) {
      return readyCondition.status === "True" ? "Ready" : "NotReady";
    }
  }

  // Job/CronJob status
  if (resource.status?.succeeded !== undefined) {
    return resource.status.succeeded ? "Completed" : "Running";
  }

  // PV/PVC status
  if (resource.status?.phase) {
    return resource.status.phase;
  }

  return "Active";
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

/**
 * Recursively traverses an object and masks values in 'data' sections of Kubernetes secrets.
 *
 * @param {any} obj - The object to traverse. Can be an array, object, or primitive value.
 * @returns {any} A new object with masked values in 'data' sections.
 */
function maskDataValues(obj: any): any {
  if (obj == null) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => maskDataValues(item));
  }

  if (typeof obj === "object") {
    const result: any = {};
    for (const key in obj) {
      if (key === "data" && typeof obj[key] === "object" && obj[key] !== null) {
        // This is a data section - mask all leaf values within it
        result[key] = maskAllLeafValues(obj[key]);
      } else {
        result[key] = maskDataValues(obj[key]);
      }
    }
    return result;
  }

  return obj;
}

/**
 * Recursively masks all leaf values (non-object, non-array values) in an object structure.
 *
 * @param {any} obj - The input object or value to process.
 * @returns {any} A new object or value with all leaf values replaced by a mask.
 */
function maskAllLeafValues(obj: any): any {
  const maskValue = "***";

  if (obj == null) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => maskAllLeafValues(item));
  }

  if (typeof obj === "object") {
    const result: any = {};
    for (const key in obj) {
      result[key] = maskAllLeafValues(obj[key]);
    }
    return result;
  }

  // This is a leaf value (string, number, boolean) - mask it
  return maskValue;
}

/**
 * Masks sensitive data in Kubernetes secrets by parsing the raw output and replacing
 * all leaf values in the "data" section with a placeholder value ("***").
 *
 * @param {string} output - The raw output from a `kubectl` command, containing secrets data.
 * @param {string} format - The format of the output, either "json" or "yaml".
 * @returns {string} - The masked output in the same format as the input.
 */
function maskSecretsData(output: string, format: string): string {
  try {
    if (format === "json") {
      const parsed = JSON.parse(output);
      const masked = maskDataValues(parsed);
      return JSON.stringify(masked, null, 2);
    } else if (format === "yaml") {
      // Parse YAML to JSON, mask, then convert back to YAML
      const parsed = yaml.load(output);
      const masked = maskDataValues(parsed);
      return yaml.dump(masked, {
        indent: 2,
        lineWidth: -1, // Don't wrap lines
        noRefs: true, // Don't use references
      });
    }
  } catch (error) {
    console.warn("Failed to parse secrets output for masking:", error);
  }

  return output;
}
