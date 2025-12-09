import { z } from "zod";
import type { V1Container } from "@kubernetes/client-node";

// Container template types
export const ContainerTemplate = z.enum([
  "ubuntu",
  "nginx",
  "busybox",
  "alpine",
  "custom",
]);

export type ContainerTemplateName = z.infer<typeof ContainerTemplate>;

// Custom container configuration schema
export const CustomContainerConfig = z.object({
  image: z.string(),
  command: z.array(z.string()).optional(),
  args: z.array(z.string()).optional(),
  ports: z
    .array(
      z.object({
        containerPort: z.number(),
        name: z.string().optional(),
        protocol: z.string().optional(),
      })
    )
    .optional(),
  resources: z
    .object({
      limits: z.record(z.string()).optional(),
      requests: z.record(z.string()).optional(),
    })
    .optional(),
  env: z
    .array(
      z.object({
        name: z.string(),
        value: z.string().optional(),
        valueFrom: z.any().optional(),
      })
    )
    .optional(),
  volumeMounts: z
    .array(
      z.object({
        name: z.string(),
        mountPath: z.string(),
        readOnly: z.boolean().optional(),
      })
    )
    .optional(),
});

export type CustomContainerConfigType = z.infer<typeof CustomContainerConfig>;

// Container template configurations with resource limits and settings
export const containerTemplates: Record<string, V1Container> = {
  ubuntu: {
    name: "main",
    image: "ubuntu:latest",
    command: ["/bin/bash"],
    args: ["-c", "sleep infinity"],
    resources: {
      limits: {
        cpu: "200m",
        memory: "256Mi",
      },
      requests: {
        cpu: "100m",
        memory: "128Mi",
      },
    },
    livenessProbe: {
      exec: {
        command: ["cat", "/proc/1/status"],
      },
      initialDelaySeconds: 5,
      periodSeconds: 10,
    },
  },
  nginx: {
    name: "main",
    image: "nginx:latest",
    ports: [{ containerPort: 80 }],
    resources: {
      limits: {
        cpu: "200m",
        memory: "256Mi",
      },
      requests: {
        cpu: "100m",
        memory: "128Mi",
      },
    },
    livenessProbe: {
      httpGet: {
        path: "/",
        port: 80,
      },
      initialDelaySeconds: 5,
      periodSeconds: 10,
    },
    readinessProbe: {
      httpGet: {
        path: "/",
        port: 80,
      },
      initialDelaySeconds: 2,
      periodSeconds: 5,
    },
  },
  busybox: {
    name: "main",
    image: "busybox:latest",
    command: ["sh"],
    args: ["-c", "sleep infinity"],
    resources: {
      limits: {
        cpu: "100m",
        memory: "64Mi",
      },
      requests: {
        cpu: "50m",
        memory: "32Mi",
      },
    },
    livenessProbe: {
      exec: {
        command: ["true"],
      },
      periodSeconds: 10,
    },
  },
  alpine: {
    name: "main",
    image: "alpine:latest",
    command: ["sh"],
    args: ["-c", "sleep infinity"],
    resources: {
      limits: {
        cpu: "100m",
        memory: "64Mi",
      },
      requests: {
        cpu: "50m",
        memory: "32Mi",
      },
    },
    livenessProbe: {
      exec: {
        command: ["true"],
      },
      periodSeconds: 10,
    },
  },
  custom: {
    name: "main",
    image: "busybox:latest", // Default image, will be overridden by custom config
    command: ["sh"],
    args: ["-c", "sleep infinity"],
    resources: {
      limits: {
        cpu: "100m",
        memory: "64Mi",
      },
      requests: {
        cpu: "50m",
        memory: "32Mi",
      },
    },
    livenessProbe: {
      exec: {
        command: ["true"],
      },
      periodSeconds: 10,
    },
  },
};
