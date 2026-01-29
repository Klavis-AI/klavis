#!/usr/bin/env node
/**
 * Converts the built gradio-widget.html file to a TypeScript constant
 * Usage: node scripts/html-to-ts.js
 */

import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Paths
const htmlPath = join(__dirname, '../dist/web/gradio-widget.html');
const outputPath = join(__dirname, '../src/server/resources/gradio-widget-content.ts');

try {
	// Read the HTML file
	const htmlContent = readFileSync(htmlPath, 'utf-8');

	// Escape backticks and ${} in the HTML content
	const escapedContent = htmlContent
		.replace(/\\/g, '\\\\')
		.replace(/`/g, '\\`')
		.replace(/\$/g, '\\$');

	// Generate TypeScript file content
	const tsContent = `/**
 * Auto-generated file - DO NOT EDIT
 * Generated from dist/web/gradio-widget.html
 * Run 'pnpm run build:gradio-widget' to regenerate
 */

export const GRADIO_WIDGET_HTML = \`${escapedContent}\`;
`;

	// Write the TypeScript file
	writeFileSync(outputPath, tsContent, 'utf-8');

	console.log(`✓ Generated ${outputPath}`);
	console.log(`  HTML size: ${htmlContent.length.toLocaleString()} bytes`);
} catch (error) {
	console.error('Failed to convert HTML to TypeScript:', error);
	process.exit(1);
}
