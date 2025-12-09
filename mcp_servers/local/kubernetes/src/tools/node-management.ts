/**
 * Tool: node_management
 * Manage Kubernetes nodes with cordon, drain, and uncordon operations.
 * Provides safety features for node operations and implements proper error handling
 * and confirmation requirements for destructive operations.
 * Note: Use kubectl_get with resourceType="nodes" to list nodes.
 */

import { execFileSync } from "child_process";
import { getSpawnMaxBuffer } from "../config/max-buffer.js";

/**
 * Schema for node_management tool.
 * - operation: Node operation to perform (cordon, drain, uncordon)
 * - nodeName: Name of the node to operate on (required for cordon, drain, uncordon)
 * - force: Force the operation even if there are unmanaged pods (for drain)
 * - gracePeriod: Grace period for pod termination (for drain)
 * - deleteLocalData: Delete local data even if emptyDir volumes are used (for drain)
 * - ignoreDaemonsets: Ignore DaemonSet-managed pods (for drain)
 * - timeout: Timeout for drain operation
 * - dryRun: Show what would be done without actually doing it (for drain)
 * - confirmDrain: Explicit confirmation to drain the node (required for drain)
 */
export const nodeManagementSchema = {
  name: "node_management",
  description:
    "Manage Kubernetes nodes with cordon, drain, and uncordon operations",
  annotations: {
    destructiveHint: true,
  },
  inputSchema: {
    type: "object",
    properties: {
      operation: {
        type: "string",
        description: "Node operation to perform",
        enum: ["cordon", "drain", "uncordon"],
      },
      nodeName: {
        type: "string",
        description:
          "Name of the node to operate on (required for cordon, drain, uncordon)",
      },
      force: {
        type: "boolean",
        description:
          "Force the operation even if there are pods not managed by a ReplicationController, ReplicaSet, Job, DaemonSet or StatefulSet (for drain operation)",
        default: false,
      },
      gracePeriod: {
        type: "number",
        description:
          "Period of time in seconds given to each pod to terminate gracefully (for drain operation). If set to -1, uses the kubectl default grace period.",
        default: -1,
      },
      deleteLocalData: {
        type: "boolean",
        description:
          "Delete local data even if emptyDir volumes are used (for drain operation)",
        default: false,
      },
      ignoreDaemonsets: {
        type: "boolean",
        description: "Ignore DaemonSet-managed pods (for drain operation)",
        default: true,
      },
      timeout: {
        type: "string",
        description:
          "The length of time to wait before giving up (for drain operation, e.g., '5m', '1h')",
        default: "0",
      },
      dryRun: {
        type: "boolean",
        description:
          "Show what would be done without actually doing it (for drain operation)",
        default: false,
      },
      confirmDrain: {
        type: "boolean",
        description:
          "Explicit confirmation to drain the node (required for drain operation)",
        default: false,
      },
    },
    required: ["operation"],
  },
};

/**
 * Interface for node_management tool parameters.
 */
interface NodeManagementParams {
  operation: "cordon" | "drain" | "uncordon";
  nodeName?: string;
  force?: boolean;
  gracePeriod?: number;
  deleteLocalData?: boolean;
  ignoreDaemonsets?: boolean;
  timeout?: string;
  dryRun?: boolean;
  confirmDrain?: boolean;
}

/**
 * Execute a command using child_process.execFileSync with proper error handling.
 * @param command - The command to execute
 * @param args - Array of command arguments
 * @returns The command output as a string
 * @throws Error if command execution fails
 */
const executeCommand = (command: string, args: string[]): string => {
  try {
    return execFileSync(command, args, {
      encoding: "utf8",
      timeout: 300000, // 5 minutes timeout for node operations
      maxBuffer: getSpawnMaxBuffer(),
      env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG },
    });
  } catch (error: any) {
    throw new Error(`${command} command failed: ${error.message}`);
  }
};

/**
 * Get the status of a specific node.
 * @param nodeName - Name of the node to get status for
 * @returns Node status as JSON object
 * @throws Error if node status retrieval fails
 */
const getNodeStatus = (nodeName: string): any => {
  try {
    const output = executeCommand("kubectl", [
      "get",
      "node",
      nodeName,
      "-o",
      "json",
    ]);
    return JSON.parse(output);
  } catch (error: any) {
    throw new Error(`Failed to get node status: ${error.message}`);
  }
};

/**
 * Main node_management function that handles all node operations.
 * Implements safety features and proper error handling for node management tasks.
 * @param params - Node management parameters
 * @returns Promise with operation results
 */
export async function nodeManagement(
  params: NodeManagementParams
): Promise<{ content: { type: string; text: string }[] }> {
  const {
    operation,
    nodeName,
    force = false,
    gracePeriod = -1,
    deleteLocalData = false,
    ignoreDaemonsets = true,
    timeout = "0",
    dryRun = false,
    confirmDrain = false,
  } = params;

  try {
    switch (operation) {
      case "cordon":
        return handleCordonNode(nodeName!);
      case "uncordon":
        return handleUncordonNode(nodeName!);
      case "drain":
        return handleDrainNode({
          nodeName: nodeName!,
          force,
          gracePeriod,
          deleteLocalData,
          ignoreDaemonsets,
          timeout,
          dryRun,
          confirmDrain,
        });
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Node management operation failed: ${error.message}`,
        },
      ],
    };
  }
}

/**
 * Handle the cordon node operation.
 * @param nodeName - Name of the node to cordon
 * @returns Promise with cordon operation results
 */
async function handleCordonNode(
  nodeName: string
): Promise<{ content: { type: string; text: string }[] }> {
  try {
    // Check if node exists and get current status
    const nodeStatus = getNodeStatus(nodeName);
    const isSchedulable = !nodeStatus.spec.unschedulable;

    if (!isSchedulable) {
      return {
        content: [
          {
            type: "text",
            text: `Node '${nodeName}' is already cordoned (unschedulable)`,
          },
        ],
      };
    }

    // Cordon the node
    executeCommand("kubectl", ["cordon", nodeName]);

    return {
      content: [
        {
          type: "text",
          text: `Successfully cordoned node '${nodeName}'. The node is now unschedulable.`,
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to cordon node: ${error.message}`);
  }
}

/**
 * Handle the uncordon node operation.
 * @param nodeName - Name of the node to uncordon
 * @returns Promise with uncordon operation results
 */
async function handleUncordonNode(
  nodeName: string
): Promise<{ content: { type: string; text: string }[] }> {
  try {
    // Check if node exists and get current status
    const nodeStatus = getNodeStatus(nodeName);
    const isSchedulable = !nodeStatus.spec.unschedulable;

    if (isSchedulable) {
      return {
        content: [
          {
            type: "text",
            text: `Node '${nodeName}' is already uncordoned (schedulable)`,
          },
        ],
      };
    }

    // Uncordon the node
    executeCommand("kubectl", ["uncordon", nodeName]);

    return {
      content: [
        {
          type: "text",
          text: `Successfully uncordoned node '${nodeName}'. The node is now schedulable.`,
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to uncordon node: ${error.message}`);
  }
}

/**
 * Handle the drain node operation with safety checks and confirmation.
 * @param params - Drain operation parameters
 * @returns Promise with drain operation results
 */
async function handleDrainNode(params: {
  nodeName: string;
  force: boolean;
  gracePeriod: number;
  deleteLocalData: boolean;
  ignoreDaemonsets: boolean;
  timeout: string;
  dryRun: boolean;
  confirmDrain: boolean;
}): Promise<{ content: { type: string; text: string }[] }> {
  const {
    nodeName,
    force,
    gracePeriod,
    deleteLocalData,
    ignoreDaemonsets,
    timeout,
    dryRun,
    confirmDrain,
  } = params;

  try {
    // Check if node exists and get current status
    const nodeStatus = getNodeStatus(nodeName);
    const isSchedulable = !nodeStatus.spec.unschedulable;

    if (!isSchedulable) {
      return {
        content: [
          {
            type: "text",
            text: `Node '${nodeName}' is already cordoned (unschedulable). Drain operation may not be necessary.`,
          },
        ],
      };
    }

    // Check for confirmation if not in dry run mode
    if (!dryRun && !confirmDrain) {
      return {
        content: [
          {
            type: "text",
            text: `Drain operation requires explicit confirmation. Set confirmDrain=true to proceed with draining node '${nodeName}'.`,
          },
        ],
      };
    }

    // Build drain command arguments
    const drainArgs = ["drain", nodeName];

    if (force) drainArgs.push("--force");
    if (gracePeriod >= 0)
      drainArgs.push("--grace-period", gracePeriod.toString());
    if (deleteLocalData) drainArgs.push("--delete-local-data");
    if (ignoreDaemonsets) drainArgs.push("--ignore-daemonsets");
    if (timeout !== "0") drainArgs.push("--timeout", timeout);
    if (dryRun) drainArgs.push("--dry-run=client");

    // Execute drain command
    const drainOutput = executeCommand("kubectl", drainArgs);

    if (dryRun) {
      return {
        content: [
          {
            type: "text",
            text: `Dry run drain operation for node '${nodeName}':\n\n${drainOutput}\n\nTo perform the actual drain, set dryRun=false and confirmDrain=true.`,
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Successfully drained node '${nodeName}'.\n\n${drainOutput}`,
        },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to drain node: ${error.message}`);
  }
}
