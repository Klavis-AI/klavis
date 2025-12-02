#!/usr/bin/env node

// Mock test to verify the implementation structure without E2B API key
import { E2BTools } from './tools.js';
import { logger } from './logger.js';

function testToolDefinitions() {
  logger.info('Testing tool definitions structure...');
  
  // Create a mock sandbox service that doesn't require E2B
  const mockSandboxService = {
    getOrCreateSandbox: async () => ({
      id: 'mock-sandbox-123',
      sandbox: {
        runCode: async (code: string) => ({
          text: 'Mock execution result',
          logs: {
            stdout: ['Mock output'],
            stderr: []
          },
          results: [{
            text: 'Mock result'
          }],
          error: null
        }),
        files: {
          write: async (path: string, content: string) => `Mock file created: ${path}`,
          read: async (path: string) => `Mock file content for ${path}`,
          list: async (path: string) => [
            { name: 'file1.txt', type: 'file', size: 100 },
            { name: 'folder1', type: 'dir' }
          ]
        },
        close: async () => {}
      },
      language: 'python',
      createdAt: new Date(),
      lastUsed: new Date()
    }),
    getSandbox: () => null,
    listSandboxes: () => [],
    cleanup: async () => {}
  };

  const e2bTools = new E2BTools(mockSandboxService as any);
  
  const tools = e2bTools.getToolDefinitions();
  
  logger.info(`✓ Tool definitions test passed: Found ${tools.length} tools`);
  
  const expectedTools = [
    'execute_python',
    'execute_javascript', 
    'create_file',
    'read_file',
    'list_files',
    'install_packages',
    'get_sandbox_info'
  ];
  
  const foundTools = tools.map(t => t.name);
  const missingTools = expectedTools.filter(tool => !foundTools.includes(tool));
  const extraTools = foundTools.filter(tool => !expectedTools.includes(tool));
  
  if (missingTools.length > 0) {
    logger.error(`❌ Missing tools: ${missingTools.join(', ')}`);
    return false;
  }
  
  if (extraTools.length > 0) {
    logger.warn(`⚠️  Extra tools found: ${extraTools.join(', ')}`);
  }
  
  // Verify tool schemas
  for (const tool of tools) {
    if (!tool.inputSchema || typeof tool.inputSchema !== 'object') {
      logger.error(`❌ Tool ${tool.name} missing or invalid inputSchema`);
      return false;
    }
    
    if (!tool.description || typeof tool.description !== 'string') {
      logger.error(`❌ Tool ${tool.name} missing or invalid description`);
      return false;
    }
  }
  
  logger.info('✓ All tool schemas are valid');
  return true;
}

function testMethodSignatures() {
  logger.info('Testing method signatures...');
  
  const mockSandboxService = { 
    getOrCreateSandbox: async () => ({}),
    cleanup: async () => {}
  };
  const e2bTools = new E2BTools(mockSandboxService as any);
  
  // Test that methods exist and are functions
  const methods = ['getToolDefinitions', 'executeTool'];
  
  for (const method of methods) {
    if (typeof (e2bTools as any)[method] !== 'function') {
      logger.error(`❌ Method ${method} is not a function or doesn't exist`);
      return false;
    }
  }
  
  logger.info('✓ All method signatures are valid');
  return true;
}

async function runMockTests() {
  logger.info('🧪 Running mock tests (no E2B API key required)...\n');
  
  let allTestsPassed = true;
  
  try {
    allTestsPassed = testToolDefinitions() && allTestsPassed;
    allTestsPassed = testMethodSignatures() && allTestsPassed;
    
    if (allTestsPassed) {
      logger.info('\n🎉 All mock tests passed! Your E2B MCP server implementation is structurally correct.');
      logger.info('💡 To run full functionality tests, set your E2B_API_KEY and run: npm test');
      logger.info('\n📝 Setup instructions:');
      logger.info('1. Get your API key from https://e2b.dev');
      logger.info('2. Set it as an environment variable:');
      logger.info('   export E2B_API_KEY="your-api-key-here"');
      logger.info('3. Run full tests: npm test');
    } else {
      logger.error('\n❌ Some mock tests failed. Please check the implementation.');
      process.exit(1);
    }
  } catch (error) {
    logger.error('\n💥 Mock tests encountered an error:', error);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runMockTests();
}