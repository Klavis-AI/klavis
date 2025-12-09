import { z } from "zod";

// Common response structure for tool operations
const ToolResponseContent = z.object({
  type: z.literal("text"),
  text: z.string(),
});

export const CreateNamespaceResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const DeleteNamespaceResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const CreatePodResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const CreateDeploymentResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const DeletePodResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const DeleteDeploymentResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const CleanupResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ListPodsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ListDeploymentsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ListServicesResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ListNamespacesResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ListNodesResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const GetLogsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const GetEventsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ListCronJobsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const CreateCronJobResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const DescribeCronJobResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ListJobsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const GetJobLogsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const PortForwardResponseSchema = z.object({
  content: z.array(
    z.object({
      success: z.boolean(),
      message: z.string(),
    })
  ),
});

export const ScaleDeploymentResponseSchema = z.object({
  content: z.array(
    z.object({
      success: z.boolean(),
      message: z.string(),
    })
  ),
});

export const DeleteCronJobResponseSchema = z.object({
  content: z.array(
    z.object({
      success: z.boolean(),
      message: z.string(),
    })
  ),
});

export const CreateConfigMapResponseSchema = z.object({
  content: z.array(
    z.object({
      success: z.boolean(),
      message: z.string(),
    })
  ),
});

export const GetConfigMapResponseSchema = z.object({
  content: z.array(
    z.object({
      success: z.boolean(),
      message: z.string(),
      data: z.record(z.string(), z.string()).optional(),
    })
  ),
});

export const UpdateConfigMapResponseSchema = z.object({
  content: z.array(
    z.object({
      success: z.boolean(),
      message: z.string(),
    })
  ),
});

export const DeleteConfigMapResponseSchema = z.object({
  content: z.array(
    z.object({
      success: z.boolean(),
      message: z.string(),
    })
  ),
});

export const ListContextsResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const GetCurrentContextResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});
export const SetCurrentContextResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const DescribeNodeResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});

export const ExecInPodResponseSchema = z.object({
  content: z.array(ToolResponseContent),
});
