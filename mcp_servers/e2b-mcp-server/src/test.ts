#!/usr/bin/env node

// Comprehensive test script to validate the MCP server
import { SandboxService } from './sandbox-manager.js';
import { E2BTools } from './tools.js';
import { logger } from './logger.js';

async function testBasicFunctionality() {
  logger.info('Starting basic functionality tests...');

  // Test environment validation
  if (!process.env.E2B_API_KEY) {
    logger.error('E2B_API_KEY is required for testing');
    process.exit(1);
  }

  const sandboxService = new SandboxService();
  const e2bTools = new E2BTools(sandboxService);

  try {
    logger.info('Testing tool definitions...');
    const tools = e2bTools.getToolDefinitions();
    logger.info(`Found ${tools.length} tools: ${tools.map(t => t.name).join(', ')}`);

    // Test Python execution
    logger.info('Testing Python code execution...');
    const pythonResult = await e2bTools.executeTool('execute_python', {
      code: 'print("Hello from Python!")\nresult = 2 + 2\nprint(f"2 + 2 = {result}")\nresult'
    });
    logger.info('Python execution result:', pythonResult);

    // Test JavaScript execution
    logger.info('Testing JavaScript code execution...');
    const jsResult = await e2bTools.executeTool('execute_javascript', {
      code: 'console.log("Hello from JavaScript!");\nconst result = 2 + 2;\nconsole.log(`2 + 2 = ${result}`);\nresult;'
    });
    logger.info('JavaScript execution result:', jsResult);

    // Test file creation and reading
    logger.info('Testing file operations...');
    const createFileResult = await e2bTools.executeTool('create_file', {
      path: 'test.txt',
      content: 'Hello, E2B MCP Server!'
    });
    logger.info('File creation result:', createFileResult);

    const readFileResult = await e2bTools.executeTool('read_file', {
      path: 'test.txt'
    });
    logger.info('File read result:', readFileResult);

    // Test directory listing
    logger.info('Testing file listing...');
    const listFilesResult = await e2bTools.executeTool('list_files', {});
    logger.info('File listing result:', listFilesResult);

    // Test Python package installation
    logger.info('Testing Python package installation...');
    const pyPackageResult = await e2bTools.executeTool('install_packages', {
      packages: ['requests'],
      language: 'python'
    });
    logger.info('Python package installation result:', pyPackageResult);

    // Test JavaScript package installation
    logger.info('Testing JavaScript package installation...');
    const jsPackageResult = await e2bTools.executeTool('install_packages', {
      packages: ['lodash'],
      language: 'javascript'
    });
    logger.info('JavaScript package installation result:', jsPackageResult);

    // Test sandbox info
    logger.info('Testing sandbox info...');
    const sandboxInfoResult = await e2bTools.executeTool('get_sandbox_info', {});
    logger.info('Sandbox info result:', sandboxInfoResult);

    logger.info('All basic tests completed successfully!');

  } catch (error) {
    logger.error('Test failed:', error);
    throw error;
  } finally {
    await sandboxService.cleanup();
  }
}

async function testErrorHandling() {
  logger.info('Testing error handling...');
  
  const sandboxService = new SandboxService();
  const e2bTools = new E2BTools(sandboxService);

  try {
    // Test invalid Python code
    const errorResult = await e2bTools.executeTool('execute_python', {
      code: 'invalid_python_code('
    });
    logger.info('Error handling test result:', errorResult);
    
    // Test reading non-existent file
    const fileErrorResult = await e2bTools.executeTool('read_file', {
      path: 'non_existent_file.txt'
    });
    logger.info('File error test result:', fileErrorResult);

  } catch (error) {
    logger.error('Error handling test failed:', error);
    throw error;
  } finally {
    await sandboxService.cleanup();
  }
}

async function runTests() {
  try {
    await testBasicFunctionality();
    await testErrorHandling();
    logger.info('🎉 All tests passed!');
  } catch (error) {
    logger.error('❌ Tests failed:', error);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runTests();
}