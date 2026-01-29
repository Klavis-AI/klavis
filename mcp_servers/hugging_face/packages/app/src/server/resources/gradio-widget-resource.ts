/**
 * Configuration and factory for the Gradio widget resource
 * This resource is used by the OpenAI MCP client (skybridge) to render Gradio spaces
 */

import { GRADIO_WIDGET_HTML } from './gradio-widget-content.js';

// CSP domains for Hugging Face and related services
const CSP_DOMAINS = {
	connect_domains: [
		'https://huggingface.co',
		'https://cdn-lfs.huggingface.co',
		'https://static.huggingface.co',
		'https://*.hf.space',
		'https://cdnjs.cloudflare.com',
		'https://cas-bridge.xethub.hf.co',
	],
	resource_domains: [
		'https://huggingface.co',
		'https://cdn-lfs.huggingface.co',
		'https://static.huggingface.co',
		'https://*.hf.space',
		'https://cdnjs.cloudflare.com',
		'https://cas-bridge.xethub.hf.co',
	],
	frame_domains: [
		'https://huggingface.co',
		'https://cdn-lfs.huggingface.co',
		'https://static.huggingface.co',
		'https://*.hf.space',
		'https://cas-bridge.xethub.hf.co',
	],
};

export interface GradioWidgetResourceConfig {
	name: string;
	version: string;
	uri: string;
	mimeType: string;
	htmlContent: string;
	metadata: {
		'openai/widgetCSP': typeof CSP_DOMAINS;
		'openai/widget': {
			csp: typeof CSP_DOMAINS;
		};
	};
}

/**
 * Creates a Gradio widget resource configuration
 * @param version - The package version to include in the URI
 * @returns Resource configuration object
 */
export function createGradioWidgetResourceConfig(version: string): GradioWidgetResourceConfig {
	const uri = `ui://widget/gradio-v${version}`;

	return {
		name: 'gradio-space',
		version,
		uri,
		mimeType: 'text/html+skybridge',
		htmlContent: GRADIO_WIDGET_HTML,
		metadata: {
			'openai/widgetCSP': CSP_DOMAINS,
			'openai/widget': {
				csp: CSP_DOMAINS,
			},
		},
	};
}
