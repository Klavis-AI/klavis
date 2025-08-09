import { z } from 'zod';

// Common validation schemas
export const DeploymentStateSchema = z.enum(['BUILDING', 'ERROR', 'INITIALIZING', 'QUEUED', 'READY', 'CANCELED']);

export const TargetEnvironmentSchema = z.enum(['production', 'preview', 'development']);

export const GitSourceSchema = z.object({
  type: z.enum(['github', 'gitlab', 'bitbucket']),
  repo: z.string(),
  repoId: z.number().optional(),
  ref: z.string().optional(),
  sha: z.string().optional(),
  prId: z.number().optional(),
});

// Tool input schemas
export const ListDeploymentsSchema = z.object({
  projectId: z.string().optional(),
  state: DeploymentStateSchema.optional(),
  limit: z.number().min(1).max(100).default(20).optional(),
  until: z.number().optional(),
  since: z.number().optional(),
});

export const GetDeploymentSchema = z.object({
  deploymentId: z.string().min(1, 'Deployment ID is required'),
});

export const CreateDeploymentSchema = z.object({
  name: z.string().min(1, 'Project name is required'),
  gitSource: GitSourceSchema.optional(),
  files: z.array(z.object({
    file: z.string(),
    data: z.string(),
    encoding: z.enum(['base64', 'utf8']).optional(),
  })).optional(),
  target: z.enum(['production', 'staging']).optional(),
  projectSettings: z.object({
    buildCommand: z.string().optional(),
    devCommand: z.string().optional(),
    installCommand: z.string().optional(),
    outputDirectory: z.string().optional(),
    rootDirectory: z.string().optional(),
    framework: z.string().optional(),
  }).optional(),
  meta: z.record(z.string()).optional(),
  env: z.record(z.string()).optional(),
  deploymentId: z.string().optional(),
  deploymentUrl: z.string().optional(),
});

export const CancelDeploymentSchema = z.object({
  deploymentId: z.string().min(1, 'Deployment ID is required'),
});

export const GetDeploymentLogsSchema = z.object({
  deploymentId: z.string().min(1, 'Deployment ID is required'),
  follow: z.boolean().default(false).optional(),
  since: z.number().optional(),
  until: z.number().optional(),
});

export const ListProjectsSchema = z.object({
  limit: z.number().min(1).max(100).default(20).optional(),
  from: z.string().optional(),
  search: z.string().optional(),
});

export const GetProjectSchema = z.object({
  projectId: z.string().min(1, 'Project ID is required'),
});

export const CreateProjectSchema = z.object({
  name: z.string().min(1, 'Project name is required'),
  gitRepository: z.object({
    type: z.enum(['github', 'gitlab', 'bitbucket']),
    repo: z.string().min(1, 'Repository is required'),
  }).optional(),
  buildCommand: z.string().optional(),
  devCommand: z.string().optional(),
  framework: z.string().optional(),
  installCommand: z.string().optional(),
  outputDirectory: z.string().optional(),
  publicSource: z.boolean().optional(),
  rootDirectory: z.string().optional(),
  serverlessFunctionRegion: z.string().optional(),
  environmentVariables: z.array(z.object({
    key: z.string().min(1),
    value: z.string(),
    target: z.array(TargetEnvironmentSchema).min(1),
  })).optional(),
});

export const UpdateProjectSchema = z.object({
  projectId: z.string().min(1, 'Project ID is required'),
  name: z.string().optional(),
  buildCommand: z.string().optional(),
  devCommand: z.string().optional(),
  framework: z.string().optional(),
  installCommand: z.string().optional(),
  outputDirectory: z.string().optional(),
  publicSource: z.boolean().optional(),
  rootDirectory: z.string().optional(),
  serverlessFunctionRegion: z.string().optional(),
});

export const DeleteProjectSchema = z.object({
  projectId: z.string().min(1, 'Project ID is required'),
});

export const ListDomainsSchema = z.object({
  limit: z.number().min(1).max(100).default(20).optional(),
  since: z.number().optional(),
  until: z.number().optional(),
});

export const AddDomainSchema = z.object({
  name: z.string().min(1, 'Domain name is required'),
  redirect: z.string().optional(),
  redirectStatusCode: z.number().optional(),
  gitBranch: z.string().optional(),
});

export const VerifyDomainSchema = z.object({
  domainName: z.string().min(1, 'Domain name is required'),
});

export const RemoveDomainSchema = z.object({
  domainName: z.string().min(1, 'Domain name is required'),
});

export const ListEnvVarsSchema = z.object({
  projectId: z.string().min(1, 'Project ID is required'),
  decrypt: z.boolean().default(false).optional(),
});

export const CreateEnvVarSchema = z.object({
  projectId: z.string().min(1, 'Project ID is required'),
  key: z.string().min(1, 'Environment variable key is required'),
  value: z.string().min(1, 'Environment variable value is required'),
  target: z.array(TargetEnvironmentSchema).min(1, 'At least one target environment is required'),
  gitBranch: z.string().optional(),
  type: z.enum(['system', 'secret', 'encrypted', 'plain']).default('encrypted').optional(),
});

export const UpdateEnvVarSchema = z.object({
  projectId: z.string().min(1, 'Project ID is required'),
  envVarId: z.string().min(1, 'Environment variable ID is required'),
  key: z.string().optional(),
  value: z.string().optional(),
  target: z.array(TargetEnvironmentSchema).optional(),
  gitBranch: z.string().optional(),
  type: z.enum(['system', 'secret', 'encrypted', 'plain']).optional(),
});

export const DeleteEnvVarSchema = z.object({
  projectId: z.string().min(1, 'Project ID is required'),
  envVarId: z.string().min(1, 'Environment variable ID is required'),
});

// Response validation schemas
export const VercelErrorSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
  }),
});

export const PaginationSchema = z.object({
  count: z.number(),
  next: z.number().optional(),
  prev: z.number().optional(),
});

export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: dataSchema.optional(),
    error: z.object({
      code: z.string(),
      message: z.string(),
    }).optional(),
    pagination: PaginationSchema.optional(),
  });

// Utility function to validate and parse input
export function validateInput<T>(schema: z.ZodSchema<T>, input: unknown): T {
  const result = schema.safeParse(input);
  if (!result.success) {
    const errors = result.error.errors.map(err => 
      `${err.path.join('.')}: ${err.message}`
    ).join(', ');
    throw new Error(`Validation failed: ${errors}`);
  }
  return result.data;
}
