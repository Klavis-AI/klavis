import { CallToolResult, Tool } from '@modelcontextprotocol/sdk/types.js';
import { SandboxService } from './sandbox-manager.js';
import { logger } from './logger.js';
import { SecurityValidator } from './security.js';
import { EXECUTION_TIMEOUT, MAX_OUTPUT_LENGTH, ExecutionResult } from './types.js';

export class E2BTools {
  constructor(private sandboxService: SandboxService) {}

  getToolDefinitions(): Tool[] {
    return [
      {
        name: 'execute_python',
        description: 'Execute Python code in an E2B sandbox environment',
        inputSchema: {
          type: 'object',
          properties: {
            code: {
              type: 'string',
              description: 'Python code to execute'
            },
            sandbox_id: {
              type: 'string',
              description: 'Optional sandbox ID to use specific sandbox'
            }
          },
          required: ['code']
        }
      },
      {
        name: 'execute_javascript',
        description: 'Execute JavaScript/Node.js code in an E2B sandbox environment',
        inputSchema: {
          type: 'object',
          properties: {
            code: {
              type: 'string',
              description: 'JavaScript code to execute'
            },
            sandbox_id: {
              type: 'string',
              description: 'Optional sandbox ID to use specific sandbox'
            }
          },
          required: ['code']
        }
      },
      {
        name: 'create_file',
        description: 'Create a file in the sandbox environment',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'File path to create'
            },
            content: {
              type: 'string',
              description: 'File content'
            },
            sandbox_id: {
              type: 'string',
              description: 'Optional sandbox ID to use specific sandbox'
            }
          },
          required: ['path', 'content']
        }
      },
      {
        name: 'read_file',
        description: 'Read a file from the sandbox environment',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'File path to read'
            },
            sandbox_id: {
              type: 'string',
              description: 'Optional sandbox ID to use specific sandbox'
            }
          },
          required: ['path']
        }
      },
      {
        name: 'list_files',
        description: 'List files in a directory in the sandbox environment',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Directory path to list (defaults to current directory)',
              default: '.'
            },
            sandbox_id: {
              type: 'string',
              description: 'Optional sandbox ID to use specific sandbox'
            }
          }
        }
      },
      {
        name: 'install_packages',
        description: 'Install packages in the sandbox environment (Python pip or Node.js npm)',
        inputSchema: {
          type: 'object',
          properties: {
            packages: {
              type: 'array',
              items: { type: 'string' },
              description: 'List of packages to install'
            },
            language: {
              type: 'string',
              enum: ['python', 'javascript'],
              description: 'Language ecosystem for package installation'
            },
            sandbox_id: {
              type: 'string',
              description: 'Optional sandbox ID to use specific sandbox'
            }
          },
          required: ['packages', 'language']
        }
      },
      {
        name: 'get_sandbox_info',
        description: 'Get information about sandbox status and resource usage',
        inputSchema: {
          type: 'object',
          properties: {
            sandbox_id: {
              type: 'string',
              description: 'Optional sandbox ID to get info for specific sandbox'
            }
          }
        }
      }
    ];
  }

  async executeTool(name: string, args: any): Promise<CallToolResult> {
    try {
      switch (name) {
        case 'execute_python':
          return await this.executePython(args);
        case 'execute_javascript':
          return await this.executeJavaScript(args);
        case 'create_file':
          return await this.createFile(args);
        case 'read_file':
          return await this.readFile(args);
        case 'list_files':
          return await this.listFiles(args);
        case 'install_packages':
          return await this.installPackages(args);
        case 'get_sandbox_info':
          return await this.getSandboxInfo(args);
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      logger.error(`Tool execution failed for ${name}:`, error);
      return {
        content: [{
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
        }],
        isError: true
      };
    }
  }

  private async executePython(args: { code: string; sandbox_id?: string }): Promise<CallToolResult> {
    const { code, sandbox_id } = args;
    
    if (!code || typeof code !== 'string') {
      throw new Error('Code parameter is required and must be a string');
    }

    // Security validation
    const validation = SecurityValidator.validateCode(code, 'python');
    if (!validation.isValid) {
      SecurityValidator.logSecurityEvent('code_validation_failed', { language: 'python', reason: validation.reason });
      throw new Error(`Security validation failed: ${validation.reason}`);
    }

    const sandbox = await this.sandboxService.getOrCreateSandbox('python', sandbox_id);
    
    logger.info(`Executing Python code in sandbox ${sandbox.id}`);
    
    const startTime = Date.now();
    try {
      const result = await sandbox.sandbox.runCode(code);
      
      const executionTime = Date.now() - startTime;
      
      let output = '';
      let hasError = false;

      // Process stdout/stderr logs
      if (result.logs) {
        if (result.logs.stdout && result.logs.stdout.length > 0) {
          output += result.logs.stdout.join('\n') + '\n';
        }
        if (result.logs.stderr && result.logs.stderr.length > 0) {
          output += result.logs.stderr.join('\n') + '\n';
        }
      }

      // Process results (interactive outputs)
      if (result.results && result.results.length > 0) {
        for (const res of result.results) {
          if (res.text) {
            output += res.text + '\n';
          }
        }
      }

      // Handle execution errors
      if (result.error) {
        output += `Error: ${result.error.name}: ${result.error.value}\n`;
        if (result.error.traceback) {
          output += result.error.traceback + '\n';
        }
        hasError = true;
      }

      // Truncate output if too long
      if (output.length > MAX_OUTPUT_LENGTH) {
        output = output.substring(0, MAX_OUTPUT_LENGTH) + '\n... (output truncated)';
      }

      // Sanitize output for security
      output = SecurityValidator.sanitizeOutput(output);

      return {
        content: [{
          type: 'text',
          text: `Execution completed in ${executionTime}ms\nSandbox ID: ${sandbox.id}\n\nOutput:\n${output || '(no output)'}`
        }],
        isError: hasError
      };
    } catch (error) {
      const executionTime = Date.now() - startTime;
      logger.error(`Python execution failed in sandbox ${sandbox.id}:`, error);
      
      return {
        content: [{
          type: 'text',
          text: `Execution failed after ${executionTime}ms\nSandbox ID: ${sandbox.id}\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`
        }],
        isError: true
      };
    }
  }

  private async executeJavaScript(args: { code: string; sandbox_id?: string }): Promise<CallToolResult> {
    const { code, sandbox_id } = args;
    
    if (!code || typeof code !== 'string') {
      throw new Error('Code parameter is required and must be a string');
    }

    // Security validation
    const validation = SecurityValidator.validateCode(code, 'javascript');
    if (!validation.isValid) {
      SecurityValidator.logSecurityEvent('code_validation_failed', { language: 'javascript', reason: validation.reason });
      throw new Error(`Security validation failed: ${validation.reason}`);
    }

    const sandbox = await this.sandboxService.getOrCreateSandbox('javascript', sandbox_id);
    
    logger.info(`Executing JavaScript code in sandbox ${sandbox.id}`);
    
    const startTime = Date.now();
    try {
      // Execute JavaScript code using the proper language context
      const result = await sandbox.sandbox.runCode(code, {
        language: 'javascript'
      });
      
      const executionTime = Date.now() - startTime;
      
      let output = '';
      let hasError = false;

      // Process stdout/stderr logs
      if (result.logs) {
        if (result.logs.stdout && result.logs.stdout.length > 0) {
          output += result.logs.stdout.join('\n') + '\n';
        }
        if (result.logs.stderr && result.logs.stderr.length > 0) {
          output += result.logs.stderr.join('\n') + '\n';
        }
      }

      // Process results (interactive outputs)
      if (result.results && result.results.length > 0) {
        for (const res of result.results) {
          if (res.text) {
            output += res.text + '\n';
          }
        }
      }

      // Handle execution errors
      if (result.error) {
        output += `Error: ${result.error.name}: ${result.error.value}\n`;
        if (result.error.traceback) {
          output += result.error.traceback + '\n';
        }
        hasError = true;
      }

      // Truncate output if too long
      if (output.length > MAX_OUTPUT_LENGTH) {
        output = output.substring(0, MAX_OUTPUT_LENGTH) + '\n... (output truncated)';
      }

      return {
        content: [{
          type: 'text',
          text: `Execution completed in ${executionTime}ms\nSandbox ID: ${sandbox.id}\n\nOutput:\n${output || '(no output)'}`
        }],
        isError: hasError
      };
    } catch (error) {
      const executionTime = Date.now() - startTime;
      logger.error(`JavaScript execution failed in sandbox ${sandbox.id}:`, error);
      
      return {
        content: [{
          type: 'text',
          text: `Execution failed after ${executionTime}ms\nSandbox ID: ${sandbox.id}\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`
        }],
        isError: true
      };
    }
  }

  private async createFile(args: { path: string; content: string; sandbox_id?: string }): Promise<CallToolResult> {
    const { path, content, sandbox_id } = args;
    
    if (!path || content === undefined) {
      throw new Error('Path and content parameters are required');
    }

    // Security validation
    const pathValidation = SecurityValidator.validateFilePath(path);
    if (!pathValidation.isValid) {
      SecurityValidator.logSecurityEvent('file_path_validation_failed', { path, reason: pathValidation.reason });
      throw new Error(`Path validation failed: ${pathValidation.reason}`);
    }

    const contentValidation = SecurityValidator.validateFileContent(content);
    if (!contentValidation.isValid) {
      SecurityValidator.logSecurityEvent('file_content_validation_failed', { path, reason: contentValidation.reason });
      throw new Error(`Content validation failed: ${contentValidation.reason}`);
    }

    // Default to Python for file operations if no specific sandbox
    const sandbox = await this.sandboxService.getOrCreateSandbox('python', sandbox_id);
    
    logger.info(`Creating file ${path} in sandbox ${sandbox.id}`);
    
    try {
      await sandbox.sandbox.files.write(path, content);
      
      return {
        content: [{
          type: 'text',
          text: `File created successfully: ${path}\nSandbox ID: ${sandbox.id}\nContent length: ${content.length} bytes`
        }]
      };
    } catch (error) {
      logger.error(`Failed to create file ${path} in sandbox ${sandbox.id}:`, error);
      throw error;
    }
  }

  private async readFile(args: { path: string; sandbox_id?: string }): Promise<CallToolResult> {
    const { path, sandbox_id } = args;
    
    if (!path) {
      throw new Error('Path parameter is required');
    }

    // Default to Python for file operations if no specific sandbox
    const sandbox = await this.sandboxService.getOrCreateSandbox('python', sandbox_id);
    
    logger.info(`Reading file ${path} from sandbox ${sandbox.id}`);
    
    try {
      const content = await sandbox.sandbox.files.read(path);
      
      return {
        content: [{
          type: 'text',
          text: `File: ${path}\nSandbox ID: ${sandbox.id}\nContent length: ${content.length} bytes\n\n${content}`
        }]
      };
    } catch (error) {
      logger.error(`Failed to read file ${path} from sandbox ${sandbox.id}:`, error);
      throw error;
    }
  }

  private async listFiles(args: { path?: string; sandbox_id?: string } = {}): Promise<CallToolResult> {
    const { path = '.', sandbox_id } = args;
    
    // Default to Python for file operations if no specific sandbox
    const sandbox = await this.sandboxService.getOrCreateSandbox('python', sandbox_id);
    
    logger.info(`Listing files in ${path} from sandbox ${sandbox.id}`);
    
    try {
      const files = await sandbox.sandbox.files.list(path);
      
      const fileList = files.map((file: any) => ({
        name: file.name,
        type: file.type,
        size: file.size
      }));
      
      return {
        content: [{
          type: 'text',
          text: `Directory: ${path}\nSandbox ID: ${sandbox.id}\nFiles (${fileList.length}):\n\n${fileList.map((f: any) => `${f.type === 'dir' ? '📁' : '📄'} ${f.name}${f.size ? ` (${f.size} bytes)` : ''}`).join('\n')}`
        }]
      };
    } catch (error) {
      logger.error(`Failed to list files in ${path} from sandbox ${sandbox.id}:`, error);
      throw error;
    }
  }

  private async installPackages(args: { packages: string[]; language: 'python' | 'javascript'; sandbox_id?: string }): Promise<CallToolResult> {
    const { packages, language, sandbox_id } = args;
    
    if (!packages || !Array.isArray(packages) || packages.length === 0) {
      throw new Error('Packages parameter is required and must be a non-empty array');
    }

    // Security validation
    const packageValidation = SecurityValidator.validatePackages(packages, language);
    if (!packageValidation.isValid) {
      SecurityValidator.logSecurityEvent('package_validation_failed', { packages, language, reason: packageValidation.reason });
      throw new Error(`Package validation failed: ${packageValidation.reason}`);
    }

    const sandbox = await this.sandboxService.getOrCreateSandbox(language, sandbox_id);
    
    logger.info(`Installing ${language} packages ${packages.join(', ')} in sandbox ${sandbox.id}`);
    
    try {
      let installCommand: string;
      if (language === 'python') {
        installCommand = `
import subprocess
import sys

packages = [${packages.map(p => `'${p}'`).join(', ')}]
for package in packages:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
print(f"Successfully installed: {', '.join(packages)}")
`;
      } else {
        installCommand = `
const { execSync } = require('child_process');
const packages = [${packages.map(p => `'${p}'`).join(', ')}];
try {
  const result = execSync('npm install ' + packages.join(' '), { 
    encoding: 'utf8', 
    cwd: process.cwd(),
    timeout: 30000 
  });
  console.log(result);
  console.log('Successfully installed:', packages.join(', '));
} catch (error) {
  console.error('Install failed:', error.message);
  throw error;
}`;
      }
      
      const result = await sandbox.sandbox.runCode(installCommand, {
        language: language === 'javascript' ? 'javascript' : 'python'
      });
      
      let output = '';
      let hasError = false;

      // Process stdout/stderr logs
      if (result.logs) {
        if (result.logs.stdout && result.logs.stdout.length > 0) {
          output += result.logs.stdout.join('\n') + '\n';
        }
        if (result.logs.stderr && result.logs.stderr.length > 0) {
          output += result.logs.stderr.join('\n') + '\n';
        }
      }

      // Process results (interactive outputs)
      if (result.results && result.results.length > 0) {
        for (const res of result.results) {
          if (res.text) {
            output += res.text + '\n';
          }
        }
      }

      // Handle execution errors
      if (result.error) {
        output += `Error: ${result.error.name}: ${result.error.value}\n`;
        if (result.error.traceback) {
          output += result.error.traceback + '\n';
        }
        hasError = true;
      }

      return {
        content: [{
          type: 'text',
          text: `Package installation ${hasError ? 'failed' : 'completed'}\nSandbox ID: ${sandbox.id}\nPackages: ${packages.join(', ')}\nLanguage: ${language}\n\nOutput:\n${output || '(no output)'}`
        }],
        isError: hasError
      };
    } catch (error) {
      logger.error(`Package installation failed in sandbox ${sandbox.id}:`, error);
      throw error;
    }
  }

  private async getSandboxInfo(args: { sandbox_id?: string } = {}): Promise<CallToolResult> {
    const { sandbox_id } = args;
    
    if (sandbox_id) {
      const sandbox = this.sandboxService.getSandbox(sandbox_id);
      if (!sandbox) {
        throw new Error(`Sandbox ${sandbox_id} not found`);
      }
      
      try {
        // Get file count
        const files = await sandbox.sandbox.files.list('.');
        const filesCount = files.length;
        
        const info = {
          id: sandbox.id,
          language: sandbox.language,
          createdAt: sandbox.createdAt.toISOString(),
          lastUsed: sandbox.lastUsed.toISOString(),
          status: 'active',
          filesCount
        };
        
        return {
          content: [{
            type: 'text',
            text: `Sandbox Information:\n${JSON.stringify(info, null, 2)}`
          }]
        };
      } catch (error) {
        logger.error(`Failed to get sandbox info for ${sandbox_id}:`, error);
        throw error;
      }
    } else {
      // List all sandboxes
      const sandboxes = this.sandboxService.listSandboxes();
      
      return {
        content: [{
          type: 'text',
          text: `Active Sandboxes (${sandboxes.length}):\n\n${sandboxes.map(sb => `ID: ${sb.id}\nLanguage: ${sb.language}\nCreated: ${sb.createdAt.toISOString()}\nLast Used: ${sb.lastUsed.toISOString()}\n`).join('\n')}`
        }]
      };
    }
  }
}