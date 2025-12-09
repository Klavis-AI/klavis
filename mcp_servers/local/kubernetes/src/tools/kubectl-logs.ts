import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import {
  contextParameter,
  namespaceParameter,
} from "../models/common-parameters.js";

export const kubectlLogsSchema = {
  name: "kubectl_logs",
  description:
    "Get logs from Kubernetes resources like pods, deployments, or jobs",
  annotations: {
    readOnlyHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      resourceType: {
        type: "string",
        enum: ["pod", "deployment", "job", "cronjob"],
        description: "Type of resource to get logs from",
      },
      name: {
        type: "string",
        description: "Name of the resource",
      },
      namespace: namespaceParameter,
      container: {
        type: "string",
        description:
          "Container name (required when pod has multiple containers)",
      },
      tail: {
        type: "number",
        description: "Number of lines to show from end of logs",
      },
      since: {
        type: "string",
        description: "Show logs since relative time (e.g. '5s', '2m', '3h')",
      },
      sinceTime: {
        type: "string",
        description: "Show logs since absolute time (RFC3339)",
      },
      timestamps: {
        type: "boolean",
        description: "Include timestamps in logs",
        default: false,
      },
      previous: {
        type: "boolean",
        description: "Include logs from previously terminated containers",
        default: false,
      },
      follow: {
        type: "boolean",
        description: "Follow logs output (not recommended, may cause timeouts)",
        default: false,
      },
      labelSelector: {
        type: "string",
        description: "Filter resources by label selector",
      },
      context: contextParameter,
    },
    required: ["resourceType", "name", "namespace"],
  },
} as const;

export async function kubectlLogs(
  k8sManager: KubernetesManager,
  input: {
    resourceType: string;
    name: string;
    namespace: string;
    container?: string;
    tail?: number;
    since?: string;
    sinceTime?: string;
    timestamps?: boolean;
    previous?: boolean;
    follow?: boolean;
    labelSelector?: string;
    context?: string;
  }
) {
  try {
    const resourceType = input.resourceType.toLowerCase();
    const name = input.name;
    const namespace = input.namespace || "default";
    const context = input.context || "";

    const command = "kubectl";
    // Handle different resource types
    if (resourceType === "pod") {
      // Direct pod logs
      let args = ["-n", namespace, "logs", name];

      // If container is specified, add it
      if (input.container) {
        args.push(`-c`, input.container);
      }

      // Add options
      args = addLogOptions(args, input);

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
        return formatLogOutput(name, result);
      } catch (error: any) {
        return handleCommandError(error, `pod ${name}`);
      }
    } else if (
      resourceType === "deployment" ||
      resourceType === "job" ||
      resourceType === "cronjob"
    ) {
      // For deployments, jobs and cronjobs we need to find the pods first
      let selectorArgs;

      if (resourceType === "deployment") {
        selectorArgs = [
          "-n",
          namespace,
          "get",
          "deployment",
          name,
          "-o",
          "jsonpath='{.spec.selector.matchLabels}'",
        ];
      } else if (resourceType === "job") {
        // For jobs, we use the job-name label
        return getLabelSelectorLogs(`job-name=${name}`, namespace, input);
      } else if (resourceType === "cronjob") {
        // For cronjobs, it's more complex - need to find the job first
        const jobsArgs = [
          "-n",
          namespace,
          "get",
          "jobs",
          "--selector=job-name=" + name,
          "-o",
          "jsonpath='{.items[*].metadata.name}'",
        ];
        try {
          const jobs = execFileSync(command, jobsArgs, {
            encoding: "utf8",
            maxBuffer: getSpawnMaxBuffer(),
            env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
          })
            .trim()
            .split(" ");

          if (jobs.length === 0 || (jobs.length === 1 && jobs[0] === "")) {
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(
                    {
                      message: `No jobs found for cronjob ${name} in namespace ${namespace}`,
                    },
                    null,
                    2
                  ),
                },
              ],
            };
          }

          // Get logs for all jobs
          const allJobLogs: Record<string, any> = {};

          for (const job of jobs) {
            // Get logs for pods from this job
            const result = await getLabelSelectorLogs(
              `job-name=${job}`,
              namespace,
              input
            );
            const jobLog = JSON.parse(result.content[0].text);
            allJobLogs[job] = jobLog.logs;
          }

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(
                  {
                    cronjob: name,
                    namespace: namespace,
                    jobs: allJobLogs,
                  },
                  null,
                  2
                ),
              },
            ],
          };
        } catch (error: any) {
          return handleCommandError(error, `cronjob ${name}`);
        }
      }

      try {
        if (resourceType === "deployment") {
          // Get the deployment's selector
          if (!selectorArgs) {
            throw new Error("Selector command is undefined");
          }
          const selectorJson = execFileSync(command, selectorArgs, {
            encoding: "utf8",
            maxBuffer: getSpawnMaxBuffer(),
            env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
          }).trim();
          const selector = JSON.parse(selectorJson.replace(/'/g, '"'));

          // Convert to label selector format
          const labelSelector = Object.entries(selector)
            .map(([key, value]) => `${key}=${value}`)
            .join(",");

          return getLabelSelectorLogs(labelSelector, namespace, input);
        }

        // For jobs and cronjobs, the logic is handled above
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  error: `Unexpected resource type: ${resourceType}`,
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      } catch (error: any) {
        return handleCommandError(error, `${resourceType} ${name}`);
      }
    } else if (input.labelSelector) {
      // Handle logs by label selector
      return getLabelSelectorLogs(input.labelSelector, namespace, input);
    } else {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Unsupported resource type: ${resourceType}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) throw error;
    throw new McpError(
      ErrorCode.InternalError,
      `Failed to get logs: ${error.message}`
    );
  }
}

// Helper function to add log options to the kubectl command
function addLogOptions(args: string[], input: any): string[] {
  // Add options based on inputs
  if (input.tail !== undefined) {
    args.push(`--tail=${input.tail}`);
  }

  if (input.since) {
    args.push(`--since=${input.since}`);
  }

  if (input.sinceTime) {
    args.push(`--since-time=${input.sinceTime}`);
  }

  if (input.timestamps) {
    args.push(`--timestamps`);
  }

  if (input.previous) {
    args.push(`--previous`);
  }

  if (input.follow) {
    args.push(`--follow`);
  }

  if (input.context) {
    args.push("--context", input.context);
  }

  return args;
}

// Helper function to get logs for resources selected by labels
async function getLabelSelectorLogs(
  labelSelector: string,
  namespace: string,
  input: any
): Promise<{ content: Array<{ type: string; text: string }> }> {
  try {
    const command = "kubectl";
    // First, find all pods matching the label selector
    const podsArgs = [
      "-n",
      namespace,
      "get",
      "pods",
      `--selector=${labelSelector}`,
      "-o",
      "jsonpath='{.items[*].metadata.name}'",
    ];
    const pods = execFileSync(command, podsArgs, {
      encoding: "utf8",
      maxBuffer: getSpawnMaxBuffer(),
      env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
    })
      .trim()
      .split(" ");

    if (pods.length === 0 || (pods.length === 1 && pods[0] === "")) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                message: `No pods found with label selector "${labelSelector}" in namespace ${namespace}`,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    // Get logs for each pod
    const logsMap: Record<string, string> = {};

    for (const pod of pods) {
      // Skip empty pod names
      if (!pod) continue;

      let podArgs = ["-n", namespace, "logs", pod];

      // Add container if specified
      if (input.container) {
        podArgs.push(`-c`, input.container);
      }

      // Add other options
      podArgs = addLogOptions(podArgs, input);

      try {
        const logs = execFileSync(command, podArgs, {
          encoding: "utf8",
          maxBuffer: getSpawnMaxBuffer(),
          env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
        });
        logsMap[pod] = logs;
      } catch (error: any) {
        logsMap[pod] = `Error: ${error.message}`;
      }
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              selector: labelSelector,
              namespace: namespace,
              logs: logsMap,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error: any) {
    return handleCommandError(error, `pods with selector "${labelSelector}"`);
  }
}

// Helper function to format log output
function formatLogOutput(resourceName: string, logOutput: string) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(
          {
            name: resourceName,
            logs: logOutput,
          },
          null,
          2
        ),
      },
    ],
  };
}

// Helper function to handle command errors
function handleCommandError(error: any, resourceDescription: string) {
  console.error(`Error getting logs for ${resourceDescription}:`, error);

  if (error.status === 404 || error.message.includes("not found")) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              error: `Resource ${resourceDescription} not found`,
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

  // Check for multi-container pod error
  if (error.message.includes("a container name must be specified")) {
    // Extract pod name and available containers from error message
    const podNameMatch = error.message.match(/for pod ([^,]+)/);
    const containersMatch = error.message.match(/choose one of: \[([^\]]+)\]/);
    const initContainersMatch = error.message.match(
      /or one of the init containers: \[([^\]]+)\]/
    );

    const podName = podNameMatch ? podNameMatch[1] : "unknown";
    const containers = containersMatch
      ? containersMatch[1].split(" ").map((c: string) => c.trim())
      : [];
    const initContainers = initContainersMatch
      ? initContainersMatch[1].split(" ").map((c: string) => c.trim())
      : [];

    // Generate structured context for the MCP client to make decisions
    const context = {
      error: "Multi-container pod requires container specification",
      status: "multi_container_error",
      pod_name: podName,
      available_containers: containers,
      init_containers: initContainers,
      suggestion: `Please specify a container name using the 'container' parameter. Available containers: ${containers.join(
        ", "
      )}${
        initContainers.length > 0
          ? `. Init containers: ${initContainers.join(", ")}`
          : ""
      }`,
    };

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(context, null, 2),
        },
      ],
      isError: true,
    };
  }

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(
          {
            error: `Failed to get logs for ${resourceDescription}: ${error.message}`,
            status: "general_error",
            original_error: error.message,
          },
          null,
          2
        ),
      },
    ],
    isError: true,
  };
}
