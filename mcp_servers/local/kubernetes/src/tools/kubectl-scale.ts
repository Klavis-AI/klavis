import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import { contextParameter, namespaceParameter } from "../models/common-parameters.js";

export const kubectlScaleSchema = {
  name: "kubectl_scale",
  description: "Scale a Kubernetes deployment",
  inputSchema: {
    type: "object",
    properties: {
      name: {
        type: "string",
        description: "Name of the deployment to scale",
      },
      namespace: namespaceParameter,
      replicas: {
        type: "number",
        description: "Number of replicas to scale to",
      },
      resourceType: {
        type: "string",
        description:
          "Resource type to scale (deployment, replicaset, statefulset)",
        default: "deployment",
      },
      context: contextParameter,
    },
    required: ["name", "replicas"],
  },
};

export async function kubectlScale(
  k8sManager: KubernetesManager,
  input: {
    name: string;
    namespace?: string;
    replicas: number;
    resourceType?: string;
    context?: string;
  }
) {
  try {
    const namespace = input.namespace || "default";
    const resourceType = input.resourceType || "deployment";
    const context = input.context || "";

    const command = "kubectl";
    const args = [
      "scale",
      resourceType,
      input.name,
      `--replicas=${input.replicas}`,
      `--namespace=${namespace}`,
    ];

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

      return {
        content: [
          {
            success: true,
            message: `Scaled ${resourceType} ${input.name} to ${input.replicas} replicas`,
          },
        ],
      };
    } catch (error: any) {
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to scale ${resourceType}: ${error.message}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      return {
        content: [
          {
            success: false,
            message: error.message,
          },
        ],
      };
    }

    return {
      content: [
        {
          success: false,
          message: `Failed to scale resource: ${error.message}`,
        },
      ],
    };
  }
}
