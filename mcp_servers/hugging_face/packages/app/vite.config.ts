import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import tailwindcss from '@tailwindcss/vite';
import { viteSingleFile } from 'vite-plugin-singlefile';

// https://vite.dev/config/
export default defineConfig(() => {
	// Conditionally apply singlefile plugin for specific build targets
	const plugins = [react(), tailwindcss()];

	// Check which specific build target is being used
	const buildTarget = process.env.VITE_BUILD_TARGET;
	const isMcpWelcomeBuild = buildTarget === 'mcp-welcome';
	const isGradioWidgetBuild = buildTarget === 'gradio-widget';
	const isSingleFileBuild = isMcpWelcomeBuild || isGradioWidgetBuild;

	if (isSingleFileBuild) {
		plugins.push(viteSingleFile());
	}

	return {
		plugins,
		resolve: {
			alias: {
				'@': path.resolve(__dirname, './src/web'),
			},
		},
		build: {
			outDir: path.resolve(__dirname, './dist/web'),
			emptyOutDir: false, // This prevents deleting mcp-server.js during builds
			rollupOptions: {
				input: isMcpWelcomeBuild
					? { mcpWelcome: path.resolve(__dirname, './src/web/mcp-welcome.html') }
					: isGradioWidgetBuild
						? { gradioWidget: path.resolve(__dirname, './src/web/gradio-widget.html') }
						: {
								// Exclude mcp-welcome and gradio-widget from main build
								// They are built separately with viteSingleFile plugin
								main: path.resolve(__dirname, './src/web/index.html'),
								gradioWidgetDev: path.resolve(__dirname, './src/web/gradio-widget-dev.html'),
							},
			},
		},
		root: path.resolve(__dirname, './src/web'),
	};
});
