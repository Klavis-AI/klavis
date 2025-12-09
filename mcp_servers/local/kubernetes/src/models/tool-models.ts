import { z } from "zod";

// Tool schemas
export const ToolSchema = z.object({
  name: z.string(),
  description: z.string(),
  inputSchema: z.record(z.any()),
});

export const ListToolsResponseSchema = z.object({
  tools: z.array(ToolSchema),
});

export const PingResponseSchema = z.object({});

export type K8sTool = z.infer<typeof ToolSchema>;
