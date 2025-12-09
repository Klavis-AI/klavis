import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
import { KubernetesManager } from "../types.js";

export const getResourceHandlers = (k8sManager: KubernetesManager) => ({
  listResources: async () => {
    return {
      resources: [
        {
          uri: "k8s://default/pods",
          name: "Kubernetes Pods",
          mimeType: "application/json",
          description: "List of pods in the default namespace",
        },
        {
          uri: "k8s://default/deployments",
          name: "Kubernetes Deployments",
          mimeType: "application/json",
          description: "List of deployments in the default namespace",
        },
        {
          uri: "k8s://default/services",
          name: "Kubernetes Services",
          mimeType: "application/json",
          description: "List of services in the default namespace",
        },
        {
          uri: "k8s://namespaces",
          name: "Kubernetes Namespaces",
          mimeType: "application/json",
          description: "List of all namespaces",
        },
        {
          uri: "k8s://nodes",
          name: "Kubernetes Nodes",
          mimeType: "application/json",
          description: "List of all nodes in the cluster",
        },
      ],
    };
  },

  readResource: async (request: { params: { uri: string } }) => {
    try {
      const uri = request.params.uri;
      const parts = uri.replace("k8s://", "").split("/");

      const isNamespaces = parts[0] === "namespaces";
      const isNodes = parts[0] === "nodes";
      if ((isNamespaces || isNodes) && parts.length === 1) {
        const fn = isNodes ? "listNode" : "listNamespace";
        const { items } = await k8sManager.getCoreApi()[fn]();
        return {
          contents: [
            {
              uri: request.params.uri,
              mimeType: "application/json",
              text: JSON.stringify(items, null, 2),
            },
          ],
        };
      }

      const [namespace, resourceType] = parts;

      switch (resourceType) {
        case "pods": {
          const { items } = await k8sManager
            .getCoreApi()
            .listNamespacedPod({ namespace });
          return {
            contents: [
              {
                uri: request.params.uri,
                mimeType: "application/json",
                text: JSON.stringify(items, null, 2),
              },
            ],
          };
        }
        case "deployments": {
          const { items } = await k8sManager
            .getAppsApi()
            .listNamespacedDeployment({ namespace });
          return {
            contents: [
              {
                uri: request.params.uri,
                mimeType: "application/json",
                text: JSON.stringify(items, null, 2),
              },
            ],
          };
        }
        case "services": {
          const { items } = await k8sManager
            .getCoreApi()
            .listNamespacedService({ namespace });
          return {
            contents: [
              {
                uri: request.params.uri,
                mimeType: "application/json",
                text: JSON.stringify(items, null, 2),
              },
            ],
          };
        }
        default:
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Unsupported resource type: ${resourceType}`
          );
      }
    } catch (error) {
      if (error instanceof McpError) throw error;
      throw new McpError(
        ErrorCode.InternalError,
        `Failed to read resource: ${error}`
      );
    }
  },
});
