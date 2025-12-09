import { spawn } from "child_process";
import { z } from "zod";
import { KubernetesManager } from "../utils/kubernetes-manager.js";

// Use spawn instead of exec because port-forward is a long-running process
async function executeKubectlCommandAsync(
  command: string
): Promise<{ success: boolean; message: string; pid: number }> {
  return new Promise((resolve, reject) => {
    const [cmd, ...args] = command.split(" ");
    const process = spawn(cmd, args);

    let output = "";
    let errorOutput = "";

    process.stdout.on("data", (data) => {
      output += data.toString();
      if (output.includes("Forwarding from")) {
        resolve({
          success: true,
          message: "port-forwarding was successful",
          pid: process.pid!,
        });
      }
    });

    process.stderr.on("data", (data) => {
      errorOutput += data.toString();
    });

    process.on("error", (error) => {
      reject(new Error(`Failed to execute port-forward: ${error.message}`));
    });

    process.on("close", (code) => {
      if (code !== 0) {
        reject(
          new Error(
            `Port-forward process exited with code ${code}. Error: ${errorOutput}`
          )
        );
      }
    });

    // Set a timeout to reject if we don't see the success message
    setTimeout(() => {
      if (!output.includes("Forwarding from")) {
        reject(
          new Error("port-forwarding failed - no success message received")
        );
      }
    }, 5000);
  });
}

export const PortForwardSchema = {
  name: "port_forward",
  description: "Forward a local port to a port on a Kubernetes resource",
  inputSchema: {
    type: "object",
    properties: {
      resourceType: { type: "string" },
      resourceName: { type: "string" },
      localPort: { type: "number" },
      targetPort: { type: "number" },
      namespace: { type: "string" },
    },
    required: ["resourceType", "resourceName", "localPort", "targetPort"],
  },
};

export async function startPortForward(
  k8sManager: KubernetesManager,
  input: {
    resourceType: string;
    resourceName: string;
    localPort: number;
    targetPort: number;
    namespace?: string;
  }
): Promise<{ content: { success: boolean; message: string }[] }> {
  let command = `kubectl port-forward`;
  if (input.namespace) {
    command += ` -n ${input.namespace}`;
  }
  command += ` ${input.resourceType}/${input.resourceName} ${input.localPort}:${input.targetPort}`;

  try {
    const result = await executeKubectlCommandAsync(command);
    // Track the port-forward process
    k8sManager.trackPortForward({
      id: `${input.resourceType}-${input.resourceName}-${input.localPort}`,
      server: {
        stop: async () => {
          try {
            process.kill(result.pid);
          } catch (error) {
            console.error(
              `Failed to stop port-forward process ${result.pid}:`,
              error
            );
          }
        },
      },
      resourceType: input.resourceType,
      name: input.resourceName,
      namespace: input.namespace || "default",
      ports: [{ local: input.localPort, remote: input.targetPort }],
    });
    return {
      content: [{ success: result.success, message: result.message }],
    };
  } catch (error: any) {
    throw new Error(`Failed to execute port-forward: ${error.message}`);
  }
}

export const StopPortForwardSchema = {
  name: "stop_port_forward",
  description: "Stop a port-forward process",
  inputSchema: {
    type: "object",
    properties: {
      id: { type: "string" },
    },
    required: ["id"],
  },
};

export async function stopPortForward(
  k8sManager: KubernetesManager,
  input: {
    id: string;
  }
): Promise<{ content: { success: boolean; message: string }[] }> {
  const portForward = k8sManager.getPortForward(input.id);
  if (!portForward) {
    throw new Error(`Port-forward with id ${input.id} not found`);
  }

  try {
    await portForward.server.stop();
    k8sManager.removePortForward(input.id);
    return {
      content: [
        { success: true, message: "port-forward stopped successfully" },
      ],
    };
  } catch (error: any) {
    throw new Error(`Failed to stop port-forward: ${error.message}`);
  }
}
