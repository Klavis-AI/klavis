import { execFileSync } from "child_process";
import {
  ExplainResourceParams,
  ListApiResourcesParams,
} from "../models/kubectl-models.js";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import { contextParameter } from "../models/common-parameters.js";

export const explainResourceSchema = {
  name: "explain_resource",
  description: "Get documentation for a Kubernetes resource or field",
  annotations: {
    readOnlyHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      resource: {
        type: "string",
        description:
          "Resource name or field path (e.g. 'pods' or 'pods.spec.containers')",
      },
      apiVersion: {
        type: "string",
        description: "API version to use (e.g. 'apps/v1')",
      },
      recursive: {
        type: "boolean",
        description: "Print the fields of fields recursively",
        default: false,
      },
      context: contextParameter,
      output: {
        type: "string",
        description: "Output format (plaintext or plaintext-openapiv2)",
        enum: ["plaintext", "plaintext-openapiv2"],
        default: "plaintext",
      },
    },
    required: ["resource"],
  },
};

export const listApiResourcesSchema = {
  name: "list_api_resources",
  description: "List the API resources available in the cluster",
  annotations: {
    readOnlyHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      apiGroup: {
        type: "string",
        description: "API group to filter by",
      },
      namespaced: {
        type: "boolean",
        description: "If true, only show namespaced resources",
      },
      context: {
        type: "string",
        description:
          "Kubeconfig Context to use for the command (optional - defaults to null)",
        default: "",
      },
      verbs: {
        type: "array",
        items: {
          type: "string",
        },
        description: "List of verbs to filter by",
      },
      output: {
        type: "string",
        description: "Output format (wide, name, or no-headers)",
        enum: ["wide", "name", "no-headers"],
        default: "wide",
      },
    },
  },
};

const executeKubectlCommand = (command: string, args: string[]): string => {
  try {
    return execFileSync(command, args, {
      encoding: "utf8",
      maxBuffer: getSpawnMaxBuffer(),
      env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
    });
  } catch (error: any) {
    throw new Error(`Kubectl command failed: ${error.message}`);
  }
};

export async function explainResource(
  params: ExplainResourceParams
): Promise<{ content: { type: string; text: string }[] }> {
  try {
    const command = "kubectl";
    const args = ["explain"];

    if (params.apiVersion) {
      args.push(`--api-version=${params.apiVersion}`);
    }

    if (params.recursive) {
      args.push("--recursive");
    }

    if (params.context) {
      args.push("--context", params.context);
    }

    if (params.output) {
      args.push(`--output=${params.output}`);
    }

    args.push(params.resource);

    const result = executeKubectlCommand(command, args);

    return {
      content: [
        {
          type: "text",
          text: result,
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to explain resource: ${error.message}`);
  }
}

export async function listApiResources(
  params: ListApiResourcesParams
): Promise<{ content: { type: string; text: string }[] }> {
  try {
    const command = "kubectl";
    const args = ["api-resources"];

    if (params.apiGroup) {
      args.push(`--api-group=${params.apiGroup}`);
    }

    if (params.namespaced !== undefined) {
      args.push(`--namespaced=${params.namespaced}`);
    }

    if (params.verbs && params.verbs.length > 0) {
      args.push(`--verbs=${params.verbs.join(",")}`);
    }

    if (params.output) {
      args.push(`-o`, params.output);
    }

    if (params.context) {
      args.push("--context", params.context);
    }

    const result = executeKubectlCommand(command, args);

    return {
      content: [
        {
          type: "text",
          text: result,
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to list API resources: ${error.message}`);
  }
}
