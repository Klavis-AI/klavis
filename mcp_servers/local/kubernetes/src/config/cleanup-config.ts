export const cleanupSchema = {
  name: "cleanup",
  description: "Cleanup all managed resources",
  inputSchema: {
    type: "object",
    properties: {},
  },
  annotations: {
    destructiveHint: true,
  },
} as const;
