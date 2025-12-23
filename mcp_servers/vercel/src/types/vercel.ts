export interface VercelDeployment {
  uid: string;
  name: string;
  url: string;
  state: 'BUILDING' | 'ERROR' | 'INITIALIZING' | 'QUEUED' | 'READY' | 'CANCELED';
  created: number;
  projectId?: string;
  gitSource?: GitSource;
  meta?: Record<string, any>;
  target?: string;
  alias?: string[];
  aliasAssigned?: number;
  aliasError?: {
    code: string;
    message: string;
  };
  builds?: Build[];
  functions?: FunctionConfiguration[];
  routes?: Route[];
  plan?: string;
  public?: boolean;
  readyState?: string;
  type?: string;
}

export interface VercelProject {
  id: string;
  name: string;
  accountId: string;
  createdAt: number;
  framework?: string;
  gitRepository?: GitRepository;
  buildCommand?: string;
  devCommand?: string;
  installCommand?: string;
  outputDirectory?: string;
  publicSource?: boolean;
  rootDirectory?: string;
  serverlessFunctionRegion?: string;
  sourceFilesOutsideRootDirectory?: boolean;
  updatedAt?: number;
  live?: boolean;
  link?: {
    type: string;
    repo: string;
    repoId: number;
    org?: string;
  };
  targets?: Record<string, any>;
  latestDeployments?: VercelDeployment[];
}

export interface GitSource {
  type: 'github' | 'gitlab' | 'bitbucket';
  repo: string;
  repoId?: number;
  ref?: string;
  sha?: string;
  prId?: number;
}

export interface GitRepository {
  type: 'github' | 'gitlab' | 'bitbucket';
  repo: string;
  repoId?: number;
}

export interface Build {
  use: string;
  src?: string;
  dest?: string;
  config?: Record<string, any>;
}

export interface Route {
  src: string;
  dest?: string;
  headers?: Record<string, string>;
  methods?: string[];
  status?: number;
  continue?: boolean;
  important?: boolean;
  caseSensitive?: boolean;
  check?: boolean;
  locale?: Record<string, string>;
  middlewarePath?: string;
  middlewareRawSrc?: string[];
  override?: boolean;
}

export interface FunctionConfiguration {
  runtime?: string;
  memory?: number;
  maxDuration?: number;
}

export interface VercelDomain {
  name: string;
  apexName: string;
  projectId?: string;
  redirect?: string;
  redirectStatusCode?: number;
  gitBranch?: string;
  updatedAt?: number;
  createdAt?: number;
  verified: boolean;
  verification?: DomainVerification[];
}

export interface DomainVerification {
  type: string;
  domain: string;
  value: string;
  reason: string;
}

export interface VercelEnvironmentVariable {
  id: string;
  key: string;
  value: string;
  target: ('production' | 'preview' | 'development')[];
  gitBranch?: string;
  type: 'system' | 'secret' | 'encrypted' | 'plain';
  configurationId?: string;
  updatedAt?: number;
  createdAt?: number;
}

export interface VercelTeam {
  id: string;
  slug: string;
  name: string;
  createdAt: number;
  avatar?: string;
}

export interface DeploymentLog {
  object: 'list';
  data: LogEntry[];
}

export interface LogEntry {
  object: 'deployment-log';
  id: string;
  message: string;
  timestamp: number;
  type: 'stdout' | 'stderr' | 'info' | 'warn' | 'error';
  source: 'build' | 'static' | 'external';
}

export interface ApiResponse<T> {
  data?: T;
  error?: {
    code: string;
    message: string;
  };
  pagination?: {
    count: number;
    next?: number;
    prev?: number;
  };
}

export interface CreateDeploymentRequest {
  name: string;
  files?: FileUpload[];
  gitSource?: {
    type: 'github' | 'gitlab' | 'bitbucket';
    repo: string;
    repoId?: number;
    ref?: string;
  };
  projectSettings?: {
    buildCommand?: string;
    devCommand?: string;
    installCommand?: string;
    outputDirectory?: string;
    rootDirectory?: string;
    framework?: string;
  };
  target?: 'production' | 'staging';
  meta?: Record<string, string>;
  env?: Record<string, string>;
  build?: {
    env?: Record<string, string>;
  };
  functions?: Record<string, FunctionConfiguration>;
  routes?: Route[];
  regions?: string[];
  public?: boolean;
}

export interface FileUpload {
  file: string;
  data: string;
  encoding?: 'base64' | 'utf8';
}

export interface CreateProjectRequest {
  name: string;
  gitRepository?: {
    type: 'github' | 'gitlab' | 'bitbucket';
    repo: string;
  };
  buildCommand?: string;
  devCommand?: string;
  framework?: string;
  installCommand?: string;
  outputDirectory?: string;
  publicSource?: boolean;
  rootDirectory?: string;
  serverlessFunctionRegion?: string;
  environmentVariables?: Array<{
    key: string;
    value: string;
    target: ('production' | 'preview' | 'development')[];
  }>;
}

export interface UpdateProjectRequest {
  name?: string;
  buildCommand?: string;
  devCommand?: string;
  framework?: string;
  installCommand?: string;
  outputDirectory?: string;
  publicSource?: boolean;
  rootDirectory?: string;
  serverlessFunctionRegion?: string;
}
