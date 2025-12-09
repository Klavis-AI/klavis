#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

const version = process.argv[2];
if (!version) {
  console.error('Usage: node scripts/update-version.js <version>');
  console.error('Example: node scripts/update-version.js 2.6.0');
  process.exit(1);
}

// Validate version format (basic semver check)
if (!/^\d+\.\d+\.\d+(-[\w\.-]+)?$/.test(version)) {
  console.error(`Invalid version format: ${version}`);
  console.error('Expected format: major.minor.patch (e.g., 2.6.0 or 2.6.0-beta.1)');
  process.exit(1);
}

const files = [
  {
    path: 'package.json',
    update: (content) => {
      const pkg = JSON.parse(content);
      pkg.version = version;
      return JSON.stringify(pkg, null, 2) + '\n';
    }
  },
  {
    path: 'manifest.json',
    update: (content) => {
      const manifest = JSON.parse(content);
      manifest.version = version;
      return JSON.stringify(manifest, null, 2) + '\n';
    }
  },
  {
    path: 'CITATION.cff',
    update: (content) => content.replace(/^version: .*/m, `version: ${version}`)
  },
  {
    path: 'README.md',
    update: (content) => content.replace(/version = \{\{\{VERSION\}\}\}/g, `version = {${version}}`)
  }
];

let hasErrors = false;

files.forEach(({ path, update }) => {
  try {
    if (!existsSync(path)) {
      console.error(`✗ File not found: ${path}`);
      hasErrors = true;
      return;
    }

    const content = readFileSync(path, 'utf8');
    const updatedContent = update(content);
    writeFileSync(path, updatedContent);
    console.log(`✓ Updated ${path}`);
  } catch (error) {
    console.error(`✗ Failed to update ${path}:`, error.message);
    hasErrors = true;
  }
});

if (hasErrors) {
  console.error(`\n❌ Some files failed to update. Please check the errors above.`);
  process.exit(1);
} else {
  console.log(`\n🎉 All files updated to version ${version}`);
} 