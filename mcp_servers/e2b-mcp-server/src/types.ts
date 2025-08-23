export interface SandboxManager {
  id: string;
  sandbox: any;
  createdAt: Date;
  lastUsed: Date;
  language: 'python' | 'javascript';
}

export interface ExecutionResult {
  success: boolean;
  output?: string;
  error?: string;
  executionTime: number;
}

export interface FileOperation {
  path: string;
  content?: string;
}

export interface PackageInstallResult {
  success: boolean;
  installedPackages: string[];
  error?: string;
}

export interface SandboxInfo {
  id: string;
  language: 'python' | 'javascript';
  createdAt: Date;
  lastUsed: Date;
  status: 'active' | 'idle' | 'terminated';
  filesCount: number;
  memoryUsage?: number;
  cpuUsage?: number;
}

export const EXECUTION_TIMEOUT = 30000; // 30 seconds
export const SANDBOX_IDLE_TIMEOUT = 300000; // 5 minutes
export const MAX_OUTPUT_LENGTH = 10000; // 10KB