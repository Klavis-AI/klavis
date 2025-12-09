import { z } from "zod";

// Resource schemas
export const ResourceSchema = z.object({
  uri: z.string(),
  name: z.string(),
  description: z.string(),
});

export const ListResourcesResponseSchema = z.object({
  resources: z.array(ResourceSchema),
});

export const ReadResourceResponseSchema = z.object({
  contents: z.array(
    z.object({
      uri: z.string(),
      mimeType: z.string(),
      text: z.string(),
    })
  ),
});

export type K8sResource = z.infer<typeof ResourceSchema>;

// Resource tracking interfaces
export interface ResourceTracker {
  kind: string;
  name: string;
  namespace: string;
  createdAt: Date;
}

export interface PortForwardTracker {
  id: string;
  server: { stop: () => Promise<void> };
  resourceType: string;
  name: string;
  namespace: string;
  ports: { local: number; remote: number }[];
}

export interface WatchTracker {
  id: string;
  abort: AbortController;
  resourceType: string;
  namespace: string;
}
