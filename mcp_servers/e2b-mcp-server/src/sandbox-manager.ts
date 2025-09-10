import { Sandbox } from '@e2b/code-interpreter';
import { v4 as uuidv4 } from 'uuid';
import { logger } from './logger.js';
import { SandboxManager, SANDBOX_IDLE_TIMEOUT } from './types.js';

export class SandboxService {
  private sandboxes = new Map<string, SandboxManager>();
  private cleanupInterval: NodeJS.Timeout;

  constructor() {
    // Cleanup idle sandboxes every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanupIdleSandboxes();
    }, 60000);

    // Cleanup on process exit
    process.on('SIGINT', () => this.cleanup());
    process.on('SIGTERM', () => this.cleanup());
  }

  async createSandbox(language: 'python' | 'javascript'): Promise<string> {
    try {
      logger.info(`Creating new ${language} sandbox`);
      
      // Create sandbox with E2B API key from environment
      const sandbox = await Sandbox.create({
        apiKey: process.env.E2B_API_KEY,
        timeoutMs: 60000 // 60 seconds timeout for sandbox initialization
      });

      const id = uuidv4();
      const sandboxManager: SandboxManager = {
        id,
        sandbox,
        createdAt: new Date(),
        lastUsed: new Date(),
        language
      };

      this.sandboxes.set(id, sandboxManager);
      logger.info(`Created sandbox ${id} for ${language}`);
      
      return id;
    } catch (error) {
      logger.error('Failed to create sandbox:', error);
      throw new Error(`Failed to create sandbox: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  getSandbox(id: string): SandboxManager | undefined {
    const sandbox = this.sandboxes.get(id);
    if (sandbox) {
      sandbox.lastUsed = new Date();
    }
    return sandbox;
  }

  async getOrCreateSandbox(language: 'python' | 'javascript', sandboxId?: string): Promise<SandboxManager> {
    if (sandboxId) {
      const existing = this.getSandbox(sandboxId);
      if (existing && existing.language === language) {
        // Test if sandbox is still alive
        try {
          await existing.sandbox.files.list('.');
          return existing;
        } catch (error) {
          logger.warn(`Sandbox ${sandboxId} is stale, removing from cache`);
          this.sandboxes.delete(sandboxId);
        }
      }
    }

    // Always create a fresh sandbox instead of reusing potentially stale ones
    const newId = await this.createSandbox(language);
    return this.getSandbox(newId)!;
  }

  async terminateSandbox(id: string): Promise<void> {
    const sandboxManager = this.sandboxes.get(id);
    if (!sandboxManager) {
      return;
    }

    try {
      await sandboxManager.sandbox.kill();
      this.sandboxes.delete(id);
      logger.info(`Terminated sandbox ${id}`);
    } catch (error) {
      logger.error(`Failed to terminate sandbox ${id}:`, error);
      // Remove from map even if kill failed
      this.sandboxes.delete(id);
    }
  }

  private async cleanupIdleSandboxes(): Promise<void> {
    const now = new Date();
    const idleSandboxes: string[] = [];

    for (const [id, sandbox] of this.sandboxes.entries()) {
      const idleTime = now.getTime() - sandbox.lastUsed.getTime();
      if (idleTime > SANDBOX_IDLE_TIMEOUT) {
        idleSandboxes.push(id);
      }
    }

    for (const id of idleSandboxes) {
      logger.info(`Cleaning up idle sandbox ${id}`);
      await this.terminateSandbox(id);
    }
  }

  async cleanup(): Promise<void> {
    logger.info('Cleaning up all sandboxes');
    clearInterval(this.cleanupInterval);
    
    const terminationPromises = Array.from(this.sandboxes.keys()).map(id => 
      this.terminateSandbox(id)
    );
    
    await Promise.allSettled(terminationPromises);
    this.sandboxes.clear();
  }

  listSandboxes(): Array<{ id: string; language: string; createdAt: Date; lastUsed: Date }> {
    return Array.from(this.sandboxes.values()).map(sb => ({
      id: sb.id,
      language: sb.language,
      createdAt: sb.createdAt,
      lastUsed: sb.lastUsed
    }));
  }
}