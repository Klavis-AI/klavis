import { z } from "zod";

export const KubectlResponseSchema = z.object({
  content: z.array(
    z.object({
      type: z.literal("text"),
      text: z.string(),
    })
  ),
});

export interface ExplainResourceParams {
  resource: string;
  apiVersion?: string;
  recursive?: boolean;
  output?: "plaintext" | "plaintext-openapiv2";
  context?: string;
}

export interface ListApiResourcesParams {
  apiGroup?: string;
  namespaced?: boolean;
  verbs?: string[];
  output?: "wide" | "name" | "no-headers";
  context?: string;
}
