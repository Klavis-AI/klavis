export const contextParameter = {
  type: "string" as const,
  description: "Kubeconfig Context to use for the command (optional - defaults to null)",
  default: "",
};

export const namespaceParameter = {
  type: "string" as const,
  description: "Kubernetes namespace",
  default: "default",
};

export const dryRunParameter = {
  type: "boolean" as const,
  description: "If true, only validate the resource, don't actually execute the operation",
  default: false,
};