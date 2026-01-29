//import "./App.css";

import { useState, useEffect } from 'react';
import useSWR, { mutate } from 'swr';
import { ToolsCard } from './components/ToolsCard';
import { GradioEndpointsCard } from './components/GradioEndpointsCard';
import { TransportMetricsCard } from './components/TransportMetricsCard';
import { McpMethodsCard } from './components/McpMethodsCard';
import { ConnectionFooter } from './components/ConnectionFooter';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Separator } from './components/ui/separator';
import { Copy, Settings } from 'lucide-react';
import type { TransportInfo } from '../shared/transport-info.js';
import { GRADIO_IMAGE_FILTER_FLAG, README_INCLUDE_FLAG } from '../shared/behavior-flags.js';
import { normalizeBuiltInTools } from '../shared/tool-normalizer.js';
import {
	SPACE_SEARCH_TOOL_ID,
	MODEL_SEARCH_TOOL_ID,
	PAPER_SEARCH_TOOL_ID,
	DATASET_SEARCH_TOOL_ID,
	DUPLICATE_SPACE_TOOL_ID,
	SPACE_FILES_TOOL_ID,
	DOCS_SEMANTIC_SEARCH_TOOL_ID,
	DOC_FETCH_TOOL_ID,
	HUB_INSPECT_TOOL_ID,
	SEMANTIC_SEARCH_TOOL_CONFIG,
	MODEL_SEARCH_TOOL_CONFIG,
	PAPER_SEARCH_TOOL_CONFIG,
	DATASET_SEARCH_TOOL_CONFIG,
	HUB_INSPECT_TOOL_CONFIG,
	DUPLICATE_SPACE_TOOL_CONFIG,
	SPACE_FILES_TOOL_CONFIG,
	DOCS_SEMANTIC_SEARCH_CONFIG,
	DOC_FETCH_CONFIG,
} from '@llmindset/hf-mcp';

type SpaceTool = {
	_id: string;
	name: string;
	subdomain: string;
	emoji: string;
};

type AppSettings = {
	builtInTools: string[];
	spaceTools: SpaceTool[];
};

// SWR fetcher function
const fetcher = (url: string) =>
	fetch(url).then((res) => {
		if (!res.ok) {
			throw new Error(`Failed to fetch: ${res.status}`);
		}
		return res.json();
	});

function App() {
	// Use SWR for transport info with auto-refresh
	const { data: transportInfo, error: transportError } = useSWR<TransportInfo>('/api/transport', fetcher, {
		refreshInterval: 3000, // Refresh every 3 seconds
		revalidateOnFocus: true,
		revalidateOnReconnect: true,
	});

	// Use SWR for sessions to trigger stdioClient update
	useSWR('/api/sessions', fetcher, {
		refreshInterval: 3000, // Refresh every 3 seconds
		revalidateOnFocus: true,
	});

	// Use SWR for settings
	const { data: settings } = useSWR<AppSettings>('/api/settings', fetcher);
	const readmeFlagEnabled = settings?.builtInTools?.includes(README_INCLUDE_FLAG) ?? false;
	const gradioImageFilterEnabled = settings?.builtInTools?.includes(GRADIO_IMAGE_FILTER_FLAG) ?? false;

	// Simple state: 3 text boxes, 3 checkboxes
	const [spaceNames, setSpaceNames] = useState<string[]>(['', '', '']);
	const [spaceSubdomains, setSpaceSubdomains] = useState<string[]>(['', '', '']);
	const [enabledSpaces, setEnabledSpaces] = useState<boolean[]>([false, false, false]);

	// Load space tools from API settings only on initial load
	const [initialLoadDone, setInitialLoadDone] = useState(false);
	useEffect(() => {
		if (settings?.spaceTools && !initialLoadDone) {
			const names = ['', '', ''];
			const subdomains = ['', '', ''];
			const enabled = [false, false, false];

			settings.spaceTools.forEach((tool, index) => {
				if (index < 3) {
					names[index] = tool.name;
					subdomains[index] = tool.subdomain;
					enabled[index] = true;
				}
			});

			setSpaceNames(names);
			setSpaceSubdomains(subdomains);
			setEnabledSpaces(enabled);
			setInitialLoadDone(true);
		}
	}, [settings, initialLoadDone]);

	const isLoading = !transportInfo && !transportError;
	const error = transportError ? transportError.message : null;

	// Handle checkbox changes
	const handleToolToggle = async (toolId: string, checked: boolean) => {
		try {
			// Optimistic update - immediately update the UI
			const currentSettings = settings || { builtInTools: [] };
			const currentTools = normalizeBuiltInTools(currentSettings.builtInTools);
			const updatedTools = checked
				? [...currentTools.filter((id) => id !== toolId), toolId]
				: currentTools.filter((id) => id !== toolId);
			const newTools = normalizeBuiltInTools(updatedTools);

			const optimisticSettings = {
				...currentSettings,
				builtInTools: newTools,
			};

			// Update the cache optimistically
			mutate('/api/settings', optimisticSettings, false);

			// Make the API call
			const response = await fetch('/api/settings', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ builtInTools: newTools }),
			});

			if (!response.ok) {
				throw new Error(`Failed to update tool settings: ${response.status}`);
			}

			// Revalidate to get fresh data from server
			mutate('/api/settings');

			console.log(`${toolId} is now ${checked ? 'enabled' : 'disabled'}`);
		} catch (err) {
			console.error(`Error updating tool settings:`, err);
			alert(`Error updating ${toolId}: ${err instanceof Error ? err.message : 'Unknown error'}`);

			// Revert optimistic update on error
			mutate('/api/settings');
		}
	};

	// Handle space tool toggle - just update checkbox and send to API
	const handleSpaceToolToggle = async (index: number, enabled: boolean) => {
		const newEnabled = [...enabledSpaces];
		newEnabled[index] = enabled;
		setEnabledSpaces(newEnabled);

		// Send only checked items to API
		await updateSpaceToolsAPI(newEnabled);
	};

	// Handle space tool name change - just update the text box
	const handleSpaceToolNameChange = async (index: number, name: string) => {
		const newNames = [...spaceNames];
		newNames[index] = name;
		setSpaceNames(newNames);

		// Send to API if this one is checked
		if (enabledSpaces[index]) {
			await updateSpaceToolsAPI(enabledSpaces);
		}
	};

	// Handle space tool subdomain change - just update the text box
	const handleSpaceToolSubdomainChange = async (index: number, subdomain: string) => {
		const newSubdomains = [...spaceSubdomains];
		newSubdomains[index] = subdomain;
		setSpaceSubdomains(newSubdomains);

		// Send to API if this one is checked
		if (enabledSpaces[index]) {
			await updateSpaceToolsAPI(enabledSpaces);
		}
	};

	// Simple helper to send current state to API
	const updateSpaceToolsAPI = async (enabledArray: boolean[]) => {
		try {
			const spaceTools: SpaceTool[] = [];

			// Only include checked items
			for (let i = 0; i < 3; i++) {
				if (enabledArray[i] && spaceNames[i] && spaceSubdomains[i]) {
					spaceTools.push({
						_id: `space-${i}`,
						name: spaceNames[i],
						subdomain: spaceSubdomains[i],
						emoji: '🔧',
					});
				}
			}

			const response = await fetch('/api/settings', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ spaceTools }),
			});

			if (!response.ok) {
				throw new Error(`Failed to update space tools: ${response.status}`);
			}
		} catch (err) {
			console.error('Error updating space tools:', err);
		}
	};

	// Handler for copying MCP URL
	const handleCopyMcpUrl = async () => {
		const mcpUrl = `https://huggingface.co/mcp`;

		try {
			await navigator.clipboard.writeText(mcpUrl);
		} catch (err) {
			console.error('Failed to copy URL:', err);
		}
	};

	// Handler for going to settings (switch to search tab)
	const handleGoToSettings = () => {
		window.open('https://huggingface.co/settings/mcp', '_blank');
	};

	/** should we use annotations / Title here? */
	const searchTools = {
		paper_search: {
			id: PAPER_SEARCH_TOOL_ID,
			label: PAPER_SEARCH_TOOL_CONFIG.annotations.title,
			description: PAPER_SEARCH_TOOL_CONFIG.description,
			settings: { enabled: settings?.builtInTools?.includes(PAPER_SEARCH_TOOL_ID) ?? true },
		},
		space_search: {
			id: SPACE_SEARCH_TOOL_ID,
			label: SEMANTIC_SEARCH_TOOL_CONFIG.annotations.title,
			description: SEMANTIC_SEARCH_TOOL_CONFIG.description,
			settings: { enabled: settings?.builtInTools?.includes(SPACE_SEARCH_TOOL_ID) ?? true },
		},
		model_search: {
			id: MODEL_SEARCH_TOOL_ID,
			label: MODEL_SEARCH_TOOL_CONFIG.annotations.title,
			description: MODEL_SEARCH_TOOL_CONFIG.description,
			settings: { enabled: settings?.builtInTools?.includes(MODEL_SEARCH_TOOL_ID) ?? true },
		},
		dataset_search: {
			id: DATASET_SEARCH_TOOL_ID,
			label: DATASET_SEARCH_TOOL_CONFIG.annotations.title,
			description: DATASET_SEARCH_TOOL_CONFIG.description,
			settings: { enabled: settings?.builtInTools?.includes(DATASET_SEARCH_TOOL_ID) ?? true },
		},
		hub_repo_details: {
			id: HUB_INSPECT_TOOL_ID,
			label: HUB_INSPECT_TOOL_CONFIG.annotations.title,
			description: HUB_INSPECT_TOOL_CONFIG.description,
			settings: { enabled: settings?.builtInTools?.includes(HUB_INSPECT_TOOL_ID) ?? true },
		},
		include_readme: {
			id: README_INCLUDE_FLAG,
			label: 'Allow README Include (flag)',
			description:
				'Allows hub_repo_details to attach README content when the tool request explicitly opts in. Requires reconnect to take effect.',
			settings: { enabled: readmeFlagEnabled },
		},
		doc_semantic_search: {
			id: DOCS_SEMANTIC_SEARCH_TOOL_ID,
			label: DOCS_SEMANTIC_SEARCH_CONFIG.annotations.title,
			description: DOCS_SEMANTIC_SEARCH_CONFIG.description,
			settings: { enabled: settings?.builtInTools?.includes(DOCS_SEMANTIC_SEARCH_TOOL_ID) ?? true },
		},
		doc_fetch: {
			id: DOC_FETCH_TOOL_ID,
			label: DOC_FETCH_CONFIG.annotations.title,
			description: DOC_FETCH_CONFIG.description,
			settings: { enabled: settings?.builtInTools?.includes(DOC_FETCH_TOOL_ID) ?? true },
		},
	};

	const spaceTools = {
		duplicate_space: {
			id: DUPLICATE_SPACE_TOOL_ID,
			label: DUPLICATE_SPACE_TOOL_CONFIG.annotations.title,
			description: DUPLICATE_SPACE_TOOL_CONFIG.description || 'Duplicate a Hugging Face Space to your account.',
			settings: { enabled: settings?.builtInTools?.includes(DUPLICATE_SPACE_TOOL_ID) ?? true },
		},
		space_files: {
			id: SPACE_FILES_TOOL_ID,
			label: SPACE_FILES_TOOL_CONFIG.annotations.title,
			description:
				SPACE_FILES_TOOL_CONFIG.description || 'List all files in a static Hugging Face Space with download URLs.',
			settings: { enabled: settings?.builtInTools?.includes(SPACE_FILES_TOOL_ID) ?? true },
		},
		no_gradio_images: {
			id: GRADIO_IMAGE_FILTER_FLAG,
			label: 'Disable Gradio Images (flag)',
			description:
				"Strips image responses from Gradio spaces. Mirrors the 'no_image_content' URL parameter and requires reconnect to take effect.",
			settings: { enabled: gradioImageFilterEnabled },
		},

	};

	return (
		<>
			<div className="min-h-screen p-4 sm:p-8 pb-20">
				<div className="max-w-4xl mx-auto">
					<Tabs defaultValue="metrics" className="w-full">
						<TabsList className="mb-6 w-full overflow-x-auto flex-nowrap">
							<TabsTrigger value="metrics" className="whitespace-nowrap">
								📊 Metrics
							</TabsTrigger>
							<TabsTrigger value="mcp" className="whitespace-nowrap">
								🔧 MCP
							</TabsTrigger>
							{!transportInfo?.externalApiMode && (
								<TabsTrigger value="search" className="whitespace-nowrap">
									🔍 Search
								</TabsTrigger>
							)}
							{!transportInfo?.externalApiMode && (
								<TabsTrigger value="spaces" className="whitespace-nowrap">
									🚀 Spaces
								</TabsTrigger>
							)}
							{!transportInfo?.externalApiMode && (
								<TabsTrigger value="gradio" className="whitespace-nowrap">
									🚀 Gradio
								</TabsTrigger>
							)}
							<TabsTrigger value="home" className="whitespace-nowrap">
								🏠 Home
							</TabsTrigger>
						</TabsList>
						<TabsContent value="metrics" className="mt-0">
							<TransportMetricsCard />
						</TabsContent>
						<TabsContent value="mcp" className="mt-0">
							<McpMethodsCard />
						</TabsContent>
						{!transportInfo?.externalApiMode && (
							<TabsContent value="search" className="mt-0">
								<ToolsCard
									title="🤗 Hugging Face Search Tools (MCP)"
									description="Find and use Hugging Face and Community content."
									tools={searchTools}
									onToolToggle={handleToolToggle}
								/>
							</TabsContent>
						)}
						{!transportInfo?.externalApiMode && (
							<TabsContent value="spaces" className="mt-0">
								<ToolsCard
									title="🤗 Hugging Face Space Tools (MCP)"
									description="Manage and duplicate Hugging Face Spaces."
									tools={spaceTools}
									onToolToggle={handleToolToggle}
								/>
							</TabsContent>
						)}
						{!transportInfo?.externalApiMode && (
							<TabsContent value="gradio" className="mt-0">
								<GradioEndpointsCard
									spaceNames={spaceNames}
									spaceSubdomains={spaceSubdomains}
									enabledSpaces={enabledSpaces}
									onSpaceToolToggle={handleSpaceToolToggle}
									onSpaceToolNameChange={handleSpaceToolNameChange}
									onSpaceToolSubdomainChange={handleSpaceToolSubdomainChange}
								/>
							</TabsContent>
						)}
						<TabsContent value="home" className="mt-0">
							{/* HF MCP Server Card */}
							<Card>
								<CardHeader>
									<CardTitle>🤗 HF MCP Server</CardTitle>
									<CardDescription>Connect with AI assistants through the Model Context Protocol</CardDescription>
								</CardHeader>
								<CardContent className="space-y-6">
									{/* What's MCP Section */}
									<div>
										<h3 className="text-sm font-semibold text-foreground mb-3">What's MCP?</h3>
										<p className="text-sm text-muted-foreground leading-relaxed">
											The Model Context Protocol (MCP) is an open standard that enables AI assistants to securely
											connect to external data sources and tools. This HF MCP Server provides access to Hugging Face's
											ecosystem of models, datasets, and Spaces, allowing AI assistants to search, analyze, and interact
											with ML resources directly.
										</p>
									</div>

									<Separator />

									{/* Tool Management Scope Information */}
									<div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
										<div className="flex items-start space-x-3">
											<div className="flex-shrink-0 mt-0.5">
												<svg
													className="h-5 w-5 text-blue-600 dark:text-blue-400"
													fill="currentColor"
													viewBox="0 0 20 20"
												>
													<path
														fillRule="evenodd"
														d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
														clipRule="evenodd"
													/>
												</svg>
											</div>
											<div>
												<h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
													Tool Management Scope
												</h3>
												{(transportInfo?.externalApiMode ||
													(transportInfo?.transport !== 'stdio' && !transportInfo?.externalApiMode)) && (
													<p className="text-sm text-blue-700 dark:text-blue-300 leading-relaxed">
														{transportInfo?.externalApiMode ? (
															<>
																<strong>External API Mode:</strong> Tools are managed by an external API. Tool Selection
																Tabs are not available.
															</>
														) : (
															<>
																<strong>Shared Mode:</strong> Tool toggles in this interface affect{' '}
																<strong>all connected MCP server instances</strong> and control tool availability for
																all connected Hosts.
															</>
														)}
													</p>
												)}
											</div>
										</div>
									</div>

									<Separator />

									{/* Action Buttons */}
									<div className="flex flex-col gap-4">
										<Button
											size="xl"
											onClick={handleCopyMcpUrl}
											className="w-full transition-all duration-200 active:bg-green-500 active:border-green-500 touch-manipulation"
										>
											<Copy className="mr-2 h-5 w-5" />
											Copy MCP URL
										</Button>
										<Button
											size="xl"
											variant="outline"
											onClick={handleGoToSettings}
											className="w-full touch-manipulation"
										>
											<Settings className="mr-2 h-5 w-5" />
											Go to Settings
										</Button>
									</div>
								</CardContent>
							</Card>
						</TabsContent>
					</Tabs>
				</div>
			</div>

			<ConnectionFooter isLoading={isLoading} error={error} transportInfo={transportInfo || { transport: 'unknown' }} />
		</>
	);
}

export default App;
