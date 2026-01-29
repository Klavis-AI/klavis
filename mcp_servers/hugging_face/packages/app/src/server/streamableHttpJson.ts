#!/usr/bin/env node

// Simple wrapper that adds --json flag and delegates to streamableHttp
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to the main streamableHttp script
const streamableHttpPath = join(__dirname, 'streamableHttp.js');

// Add --json flag to the arguments
const args = ['--json', ...process.argv.slice(2)];

// Spawn the main script with the --json flag
const child = spawn('node', [streamableHttpPath, ...args], {
  stdio: 'inherit',
  env: process.env
});

child.on('exit', (code) => {
  process.exit(code || 0);
});