import { KubernetesManager } from "../types.js";
import { execFileSync } from "child_process";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";
import { contextParameter, namespaceParameter, dryRunParameter } from "../models/common-parameters.js";

export const kubectlCreateSchema = {
  name: "kubectl_create",
  description:
    "Create Kubernetes resources using various methods (from file or using subcommands)",
  inputSchema: {
    type: "object",
    properties: {
      // General options
      dryRun: dryRunParameter,
      output: {
        type: "string",
        enum: [
          "json",
          "yaml",
          "name",
          "go-template",
          "go-template-file",
          "template",
          "templatefile",
          "jsonpath",
          "jsonpath-as-json",
          "jsonpath-file",
        ],
        description:
          "Output format. One of: json|yaml|name|go-template|go-template-file|template|templatefile|jsonpath|jsonpath-as-json|jsonpath-file",
        default: "yaml",
      },
      validate: {
        type: "boolean",
        description: "If true, validate resource schema against server schema",
        default: true,
      },

      // Create from file method
      manifest: {
        type: "string",
        description: "YAML manifest to create resources from",
      },
      filename: {
        type: "string",
        description: "Path to a YAML file to create resources from",
      },

      // Resource type to create (determines which subcommand to use)
      resourceType: {
        type: "string",
        description:
          "Type of resource to create (namespace, configmap, deployment, service, etc.)",
      },

      // Common parameters for most resource types
      name: {
        type: "string",
        description: "Name of the resource to create",
      },
      namespace: namespaceParameter,

      // ConfigMap specific parameters
      fromLiteral: {
        type: "array",
        items: { type: "string" },
        description:
          'Key-value pair for creating configmap (e.g. ["key1=value1", "key2=value2"])',
      },
      fromFile: {
        type: "array",
        items: { type: "string" },
        description:
          'Path to file for creating configmap (e.g. ["key1=/path/to/file1", "key2=/path/to/file2"])',
      },

      // Namespace specific parameters
      // No special parameters for namespace, just name is needed

      // Secret specific parameters
      secretType: {
        type: "string",
        enum: ["generic", "docker-registry", "tls"],
        description: "Type of secret to create (generic, docker-registry, tls)",
      },

      // Service specific parameters
      serviceType: {
        type: "string",
        enum: ["clusterip", "nodeport", "loadbalancer", "externalname"],
        description:
          "Type of service to create (clusterip, nodeport, loadbalancer, externalname)",
      },
      tcpPort: {
        type: "array",
        items: { type: "string" },
        description:
          'Port pairs for tcp service (e.g. ["80:8080", "443:8443"])',
      },

      // Deployment specific parameters
      image: {
        type: "string",
        description: "Image to use for the containers in the deployment",
      },
      replicas: {
        type: "number",
        description: "Number of replicas to create for the deployment",
        default: 1,
      },
      port: {
        type: "number",
        description: "Port that the container exposes",
      },

      // CronJob specific parameters
      schedule: {
        type: "string",
        description:
          'Cron schedule expression for the CronJob (e.g. "*/5 * * * *")',
      },
      suspend: {
        type: "boolean",
        description: "Whether to suspend the CronJob",
        default: false,
      },

      // Job specific parameters
      command: {
        type: "array",
        items: { type: "string" },
        description: "Command to run in the container",
      },

      // Additional common parameters
      labels: {
        type: "array",
        items: { type: "string" },
        description:
          'Labels to apply to the resource (e.g. ["key1=value1", "key2=value2"])',
      },
      annotations: {
        type: "array",
        items: { type: "string" },
        description:
          'Annotations to apply to the resource (e.g. ["key1=value1", "key2=value2"])',
      },
      context: contextParameter,
    },
    required: [],
  },
} as const;

export async function kubectlCreate(
  k8sManager: KubernetesManager,
  input: {
    // General options
    dryRun?: boolean;
    output?: string;
    validate?: boolean;

    // Create from file
    manifest?: string;
    filename?: string;

    // Resource type and common parameters
    resourceType?: string;
    name?: string;
    namespace?: string;

    // ConfigMap specific
    fromLiteral?: string[];
    fromFile?: string[];

    // Secret specific
    secretType?: "generic" | "docker-registry" | "tls";

    // Service specific
    serviceType?: "clusterip" | "nodeport" | "loadbalancer" | "externalname";
    tcpPort?: string[];

    // Deployment specific
    image?: string;
    replicas?: number;
    port?: number;

    // Job specific
    command?: string[];

    // Additional common parameters
    labels?: string[];
    annotations?: string[];
    schedule?: string;
    suspend?: boolean;
    context?: string;
  }
) {
  try {
    // Check if we have enough information to proceed
    if (!input.manifest && !input.filename && !input.resourceType) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        "Either manifest, filename, or resourceType must be provided"
      );
    }

    // If resourceType is provided, check if name is provided for most resource types
    if (
      input.resourceType &&
      !input.name &&
      input.resourceType !== "namespace"
    ) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Name is required when creating a ${input.resourceType}`
      );
    }

    // Set up common parameters
    const namespace = input.namespace || "default";
    const dryRun = input.dryRun || false;
    const validate = input.validate ?? true;
    const output = input.output || "yaml";
    const context = input.context || "";

    const command = "kubectl";
    const args = ["create"];
    let tempFile: string | null = null;

    // Process manifest content if provided (file-based creation)
    if (input.manifest || input.filename) {
      if (input.manifest) {
        // Create temporary file for the manifest
        const tmpDir = os.tmpdir();
        tempFile = path.join(tmpDir, `create-manifest-${Date.now()}.yaml`);
        fs.writeFileSync(tempFile, input.manifest);
        args.push("-f", tempFile);
      } else if (input.filename) {
        args.push("-f", input.filename);
      }
    } else {
      // Process subcommand-based creation
      switch (input.resourceType?.toLowerCase()) {
        case "namespace":
          args.push("namespace", input.name!);
          break;

        case "configmap":
          args.push("configmap", input.name!);

          // Add --from-literal arguments
          if (input.fromLiteral && input.fromLiteral.length > 0) {
            input.fromLiteral.forEach((literal) => {
              args.push(`--from-literal=${literal}`);
            });
          }

          // Add --from-file arguments
          if (input.fromFile && input.fromFile.length > 0) {
            input.fromFile.forEach((file) => {
              args.push(`--from-file=${file}`);
            });
          }
          break;

        case "secret":
          if (!input.secretType) {
            throw new McpError(
              ErrorCode.InvalidRequest,
              "secretType is required when creating a secret"
            );
          }

          args.push("secret", input.secretType, input.name!);

          // Add --from-literal arguments
          if (input.fromLiteral && input.fromLiteral.length > 0) {
            input.fromLiteral.forEach((literal) => {
              args.push(`--from-literal=${literal}`);
            });
          }

          // Add --from-file arguments
          if (input.fromFile && input.fromFile.length > 0) {
            input.fromFile.forEach((file) => {
              args.push(`--from-file=${file}`);
            });
          }
          break;

        case "service":
          if (!input.serviceType) {
            // Default to clusterip if not specified
            input.serviceType = "clusterip";
          }

          args.push("service", input.serviceType, input.name!);

          // Add --tcp arguments for ports
          if (input.tcpPort && input.tcpPort.length > 0) {
            input.tcpPort.forEach((port) => {
              args.push(`--tcp=${port}`);
            });
          }
          break;

        case "cronjob":
          if (!input.image) {
            throw new McpError(
              ErrorCode.InvalidRequest,
              "image is required when creating a cronjob"
            );
          }

          if (!input.schedule) {
            throw new McpError(
              ErrorCode.InvalidRequest,
              "schedule is required when creating a cronjob"
            );
          }

          args.push(
            "cronjob",
            input.name!,
            `--image=${input.image}`,
            `--schedule=${input.schedule}`
          );

          // Add command if specified
          if (input.command && input.command.length > 0) {
            args.push("--", ...input.command);
          }

          // Add suspend flag if specified
          if (input.suspend === true) {
            args.push(`--suspend`);
          }
          break;

        case "deployment":
          if (!input.image) {
            throw new McpError(
              ErrorCode.InvalidRequest,
              "image is required when creating a deployment"
            );
          }

          args.push("deployment", input.name!, `--image=${input.image}`);

          // Add replicas if specified
          if (input.replicas) {
            args.push(`--replicas=${input.replicas}`);
          }

          // Add port if specified
          if (input.port) {
            args.push(`--port=${input.port}`);
          }
          break;

        case "job":
          if (!input.image) {
            throw new McpError(
              ErrorCode.InvalidRequest,
              "image is required when creating a job"
            );
          }

          args.push("job", input.name!, `--image=${input.image}`);

          // Add command if specified
          if (input.command && input.command.length > 0) {
            args.push("--", ...input.command);
          }
          break;

        default:
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Unsupported resource type: ${input.resourceType}`
          );
      }
    }

    // Add namespace if not creating a namespace itself
    if (input.resourceType !== "namespace") {
      args.push("-n", namespace);
    }

    // Add labels if specified
    if (input.labels && input.labels.length > 0) {
      input.labels.forEach((label) => {
        args.push("-l", label);
      });
    }

    // Add annotations if specified
    if (input.annotations && input.annotations.length > 0) {
      input.annotations.forEach((annotation) => {
        args.push(`--annotation=${annotation}`);
      });
    }

    // Add dry-run flag if requested
    if (dryRun) {
      args.push("--dry-run=client");
    }

    // Add validate flag if needed
    if (!validate) {
      args.push("--validate=false");
    }

    // Add output format
    args.push("-o", output);

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
        `Failed to create resource: ${error.message}`
      );
    }
  } catch (error: any) {
    if (error instanceof McpError) {
      throw error;
    }

    throw new McpError(
      ErrorCode.InternalError,
      `Failed to execute kubectl create command: ${error.message}`
    );
  }
}
