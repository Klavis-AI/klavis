import {
  ContainerTemplate,
  CustomContainerConfig,
} from "./container-templates.js";

export const createDeploymentSchema = {
  name: "create_deployment",
  description: "Create a new Kubernetes deployment",
  inputSchema: {
    type: "object",
    properties: {
      name: { type: "string" },
      namespace: { type: "string" },
      template: {
        type: "string",
        enum: ContainerTemplate.options,
      },
      replicas: { type: "number", default: 1 },
      ports: {
        type: "array",
        items: { type: "number" },
        optional: true,
      },
      customConfig: {
        type: "object",
        optional: true,
        properties: {
          image: { type: "string" },
          command: { type: "array", items: { type: "string" } },
          args: { type: "array", items: { type: "string" } },
          ports: {
            type: "array",
            items: {
              type: "object",
              properties: {
                containerPort: { type: "number" },
                name: { type: "string" },
                protocol: { type: "string" },
              },
            },
          },
          resources: {
            type: "object",
            properties: {
              limits: {
                type: "object",
                additionalProperties: { type: "string" },
              },
              requests: {
                type: "object",
                additionalProperties: { type: "string" },
              },
            },
          },
          env: {
            type: "array",
            items: {
              type: "object",
              properties: {
                name: { type: "string" },
                value: { type: "string" },
                valueFrom: { type: "object" },
              },
            },
          },
          volumeMounts: {
            type: "array",
            items: {
              type: "object",
              properties: {
                name: { type: "string" },
                mountPath: { type: "string" },
                readOnly: { type: "boolean" },
              },
            },
          },
        },
      },
    },
    required: ["name", "namespace", "template"],
  },
} as const;
