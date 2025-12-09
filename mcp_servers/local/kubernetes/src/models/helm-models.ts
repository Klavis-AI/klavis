import { z } from "zod";

export const HelmResponseSchema = z.object({
  content: z.array(
    z.object({
      type: z.literal("text"),
      text: z.string(),
    })
  ),
});

export const HelmValuesSchema = z.record(z.any());

export interface HelmUninstallOperation {
  name: string;
  namespace: string;
}

export interface HelmInstallOperation {
  name: string;
  chart: string;
  namespace: string;
  repo?: string;
  values?: Record<string, any>;
  valuesFile?: string;
  createNamespace?: boolean;
  useTemplate?: boolean;
}

export interface HelmUpgradeOperation {
  name: string;
  chart: string;
  namespace: string;
  repo?: string;
  values?: Record<string, any>;
  valuesFile?: string;
}

export type HelmResponse = {
  status: "installed" | "upgraded" | "uninstalled" | "failed";
  message?: string;
  error?: string;
  steps?: string[];
};
