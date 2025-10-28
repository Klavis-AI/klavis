// Copy all JSON files from src/openapi to dist/openapi after tsc build
// Usage: node scripts/copy-openapi-json.cjs

const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, '../src/openapi');
const distDir = path.join(__dirname, '../dist/openapi');

if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

const files = fs.readdirSync(srcDir);

for (const file of files) {
  if (file.endsWith('.json')) {
    const srcPath = path.join(srcDir, file);
    const destPath = path.join(distDir, file);
    fs.copyFileSync(srcPath, destPath);
  }
}
