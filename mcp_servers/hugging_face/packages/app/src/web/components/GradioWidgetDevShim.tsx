import { useState, useEffect, useRef } from 'react';
import type { DisplayMode, OpenAiGlobals } from '../hooks';

const DEFAULT_TOOL_OUTPUT = {
	url: 'https://example.com/audio.wav',
};

const DEFAULT_WIDGET_STATE = {
	lastPlayed: null,
};

type MockOpenAiApi = Partial<OpenAiGlobals> & {
	setWidgetState: (state: unknown) => Promise<void>;
	callTool: (name: string, args: Record<string, unknown>) => Promise<{ result: string }>;
	sendFollowUpMessage: (args: { prompt: string }) => Promise<void>;
	openExternal: (payload: { href: string }) => void;
	requestDisplayMode: (args: { mode: DisplayMode }) => Promise<{ mode: DisplayMode }>;
};

type OpenAiHostWindow = Window & { openai?: MockOpenAiApi };

export function GradioWidgetDevShim() {
	const iframeRef = useRef<HTMLIFrameElement>(null);
	const [toolOutputJson, setToolOutputJson] = useState(
		JSON.stringify(DEFAULT_TOOL_OUTPUT, null, 2)
	);
	const [widgetStateJson, setWidgetStateJson] = useState(
		JSON.stringify(DEFAULT_WIDGET_STATE, null, 2)
	);
	const [displayMode, setDisplayMode] = useState<DisplayMode>('inline');
	const [maxHeight, setMaxHeight] = useState(800);
	const [theme, setTheme] = useState<'light' | 'dark'>('light');
	const [error, setError] = useState<string | null>(null);

	// Load persisted values from localStorage
	useEffect(() => {
		const saved = localStorage.getItem('gradio-widget-dev-state');
		if (saved) {
			try {
				const state = JSON.parse(saved);
				if (state.toolOutputJson) setToolOutputJson(state.toolOutputJson);
				if (state.widgetStateJson) setWidgetStateJson(state.widgetStateJson);
				if (state.displayMode) setDisplayMode(state.displayMode);
				if (state.maxHeight) setMaxHeight(state.maxHeight);
				if (state.theme) setTheme(state.theme);
			} catch (e) {
				console.error('Failed to load saved state:', e);
			}
		}
	}, []);

	// Save to localStorage on change
	useEffect(() => {
		const state = {
			toolOutputJson,
			widgetStateJson,
			displayMode,
			maxHeight,
			theme,
		};
		localStorage.setItem('gradio-widget-dev-state', JSON.stringify(state));
	}, [toolOutputJson, widgetStateJson, displayMode, maxHeight, theme]);

	// Auto-update when theme, displayMode, or maxHeight changes
	useEffect(() => {
		const iframe = iframeRef.current;
		if (!iframe?.contentWindow) return;

		const iframeWindow = iframe.contentWindow as OpenAiHostWindow;
		const openaiApi = iframeWindow.openai;
		if (!openaiApi) return;

		// Update the globals
		openaiApi.displayMode = displayMode;
		openaiApi.maxHeight = maxHeight;
		openaiApi.theme = theme;

		// Dispatch event to trigger hooks
		const event = new CustomEvent('openai:set_globals', {
			detail: {
				globals: {
					displayMode,
					maxHeight,
					theme,
				},
			},
		});
			iframeWindow.dispatchEvent(event);

			console.log('[Shim] Auto-updated displayMode, maxHeight, theme');
		}, [displayMode, maxHeight, theme]);

	// Initialize window.openai in iframe when it loads
		useEffect(() => {
			const iframe = iframeRef.current;
			if (!iframe) return;

			const handleLoad = () => {
				const iframeWindow = iframe.contentWindow;
				if (!iframeWindow) return;

				// Helper to dispatch custom events in iframe
				const dispatchGlobalsEvent = (globals: Partial<OpenAiGlobals>) => {
					const event = new CustomEvent('openai:set_globals', {
						detail: { globals },
					});
					iframeWindow.dispatchEvent(event);
				};

				// Mock the window.openai API
				const mockOpenAi: MockOpenAiApi = {
					theme,
					locale: 'en-US',
					displayMode,
					maxHeight,
					toolInput: {},
				toolOutput: null,
				toolResponseMetadata: null,
				widgetState: null,
				userAgent: {
					device: { type: 'desktop' },
					capabilities: { hover: true, touch: false },
				},
				safeArea: {
						insets: { top: 0, bottom: 0, left: 0, right: 0 },
					},
					setWidgetState: async (state: unknown) => {
						console.log('[Shim] setWidgetState called:', state);
						setWidgetStateJson(JSON.stringify(state, null, 2));
					mockOpenAi.widgetState = state;
					dispatchGlobalsEvent({ widgetState: state });
				},
				callTool: async (name: string, args: Record<string, unknown>) => {
					console.log('[Shim] callTool called:', name, args);
					return { result: 'Mock tool response' };
				},
				sendFollowUpMessage: async (args: { prompt: string }) => {
					console.log('[Shim] sendFollowUpMessage called:', args);
				},
				openExternal: (payload: { href: string }) => {
					console.log('[Shim] openExternal called:', payload);
					window.open(payload.href, '_blank');
				},
				requestDisplayMode: async (args: { mode: DisplayMode }) => {
					console.log('[Shim] requestDisplayMode called:', args);
					setDisplayMode(args.mode);
					return { mode: args.mode };
					},
				};

				// Inject into iframe's window BEFORE the widget loads
				const hostWindow = iframeWindow as OpenAiHostWindow;
				hostWindow.openai = mockOpenAi;

				console.log('[Shim] window.openai initialized in iframe');

			// Auto-send initial data after a short delay to ensure React is ready
			setTimeout(() => {
				try {
					const toolOutput = JSON.parse(toolOutputJson);
					const widgetState = widgetStateJson.trim()
						? JSON.parse(widgetStateJson)
						: null;

						mockOpenAi.toolOutput = toolOutput;
						mockOpenAi.widgetState = widgetState;

						dispatchGlobalsEvent({
							toolOutput,
							widgetState,
							displayMode,
						maxHeight,
						theme,
					});

					console.log('[Shim] Initial data sent to widget');
				} catch (e) {
					console.error('[Shim] Failed to send initial data:', e);
				}
			}, 100);
			};

			iframe.addEventListener('load', handleLoad);
			return () => iframe.removeEventListener('load', handleLoad);
			// eslint-disable-next-line react-hooks/exhaustive-deps
		}, []);

	const sendUpdate = () => {
		setError(null);
			const iframe = iframeRef.current;
			if (!iframe?.contentWindow) {
				setError('Iframe not loaded');
				return;
			}

			try {
			const toolOutput = JSON.parse(toolOutputJson);
			const widgetState = widgetStateJson.trim()
				? JSON.parse(widgetStateJson)
				: null;

				const iframeWindow = iframe.contentWindow as OpenAiHostWindow;
				const openaiApi = iframeWindow.openai;
				if (!openaiApi) {
					setError('window.openai not initialized');
					return;
				}

			// Update the globals
				openaiApi.toolOutput = toolOutput;
				openaiApi.widgetState = widgetState;
				openaiApi.displayMode = displayMode;
				openaiApi.maxHeight = maxHeight;
				openaiApi.theme = theme;

			// Dispatch event to trigger hooks
			const event = new CustomEvent('openai:set_globals', {
				detail: {
					globals: {
						toolOutput,
						widgetState,
						displayMode,
						maxHeight,
						theme,
					},
				},
				});
				iframeWindow.dispatchEvent(event);

				console.log('[Shim] Update sent to widget');
			} catch (e) {
				setError(`Invalid JSON: ${e instanceof Error ? e.message : String(e)}`);
			}
	};

	return (
		<div className="flex h-screen bg-gray-100">
			{/* Left: Widget iframe */}
			<div className="flex-1 p-4 overflow-hidden">
				<div className="h-full bg-white rounded-lg shadow-lg overflow-hidden">
					<iframe
						ref={iframeRef}
						src="/gradio-widget.html"
						className="w-full h-full border-0"
						title="Gradio Widget"
					/>
				</div>
			</div>

			{/* Right: Controls */}
			<div className="w-96 p-4 overflow-y-auto bg-white border-l border-gray-200">
				<div className="flex items-center gap-2 mb-4">
					<h1 className="text-2xl font-bold">Widget Dev</h1>
					<span className="px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
						IFRAME
					</span>
				</div>

				<div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-sm">
					<strong>Iframe Mode:</strong> Widget loads in isolated context. Check browser
					console for [Shim] logs.
				</div>

				{error && (
					<div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
						{error}
					</div>
				)}

				{/* Tool Output */}
				<div className="mb-6">
					<label className="block text-sm font-medium mb-2">
						Tool Output (JSON)
					</label>
					<textarea
						value={toolOutputJson}
						onChange={(e) => setToolOutputJson(e.target.value)}
						className="w-full h-32 p-2 border border-gray-300 rounded font-mono text-sm"
						spellCheck={false}
					/>
				</div>

				{/* Widget State */}
				<div className="mb-6">
					<label className="block text-sm font-medium mb-2">
						Widget State (JSON)
					</label>
					<textarea
						value={widgetStateJson}
						onChange={(e) => setWidgetStateJson(e.target.value)}
						className="w-full h-32 p-2 border border-gray-300 rounded font-mono text-sm"
						spellCheck={false}
					/>
				</div>

				{/* Display Mode */}
				<div className="mb-6">
					<label className="block text-sm font-medium mb-2">Display Mode</label>
					<div className="flex gap-2">
						{(['inline', 'fullscreen', 'pip'] as DisplayMode[]).map((mode) => (
							<button
								key={mode}
								onClick={() => setDisplayMode(mode)}
								className={`px-4 py-2 rounded font-medium ${
									displayMode === mode
										? 'bg-blue-500 text-white'
										: 'bg-gray-200 text-gray-700 hover:bg-gray-300'
								}`}
							>
								{mode}
							</button>
						))}
					</div>
				</div>

				{/* Max Height */}
				<div className="mb-6">
					<label className="block text-sm font-medium mb-2">
						Max Height: {maxHeight}px
					</label>
					<input
						type="range"
						min="400"
						max="1200"
						step="50"
						value={maxHeight}
						onChange={(e) => setMaxHeight(Number(e.target.value))}
						className="w-full"
					/>
				</div>

				{/* Theme */}
				<div className="mb-6">
					<label className="block text-sm font-medium mb-2">Theme</label>
					<div className="flex gap-2">
						{(['light', 'dark'] as const).map((t) => (
							<button
								key={t}
								onClick={() => setTheme(t)}
								className={`px-4 py-2 rounded font-medium ${
									theme === t
										? 'bg-blue-500 text-white'
										: 'bg-gray-200 text-gray-700 hover:bg-gray-300'
								}`}
							>
								{t}
							</button>
						))}
					</div>
				</div>

				{/* Send Button */}
				<button
					onClick={sendUpdate}
					className="w-full py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors"
				>
					Send Update
				</button>

				{/* Quick presets */}
				<div className="mt-8 pt-6 border-t border-gray-200">
					<h2 className="text-lg font-semibold mb-3">Quick Presets</h2>
					<div className="space-y-2">
						<button
							onClick={() => {
								setToolOutputJson(
									JSON.stringify(
										{ url: 'https://example.com/audio.wav' },
										null,
										2
									)
								);
								sendUpdate();
							}}
							className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded text-left"
						>
							Audio WAV
						</button>
						<button
							onClick={() => {
								setToolOutputJson(
									JSON.stringify(
										{ url: 'https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo.png' },
										null,
										2
									)
								);
								sendUpdate();
							}}
							className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded text-left"
						>
							Image PNG
						</button>
						<button
							onClick={() => {
								setToolOutputJson(
									JSON.stringify(
										{ url: 'https://example.com/video.mp4' },
										null,
										2
									)
								);
								sendUpdate();
							}}
							className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded text-left"
						>
							Video MP4
						</button>
						<button
							onClick={() => {
								setToolOutputJson(JSON.stringify({}, null, 2));
								sendUpdate();
							}}
							className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded text-left"
						>
							Empty (no content)
						</button>
						<button
							onClick={() => {
								setToolOutputJson('');
									const iframe = iframeRef.current;
									if (iframe?.contentWindow) {
										const iframeWindow = iframe.contentWindow as OpenAiHostWindow;
										const openaiApi = iframeWindow.openai;
										if (openaiApi) {
											openaiApi.toolOutput = null;
											const event = new CustomEvent('openai:set_globals', {
												detail: {
													globals: {
														toolOutput: null,
														widgetState: widgetStateJson.trim()
														? JSON.parse(widgetStateJson)
														: null,
													displayMode,
													maxHeight,
													theme,
													},
												},
											});
											iframeWindow.dispatchEvent(event);
											console.log('[Shim] Loading state activated');
										}
									}
								}}
							className="w-full px-3 py-2 text-sm bg-purple-100 hover:bg-purple-200 rounded text-left"
						>
							Show Loading
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}
