import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { CopyButton } from '../ui/copy-button';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { BOUQUET_PRESETS, describeConfigEntry } from '../../../shared/bouquet-presets.js';

const CORE_PRESETS = BOUQUET_PRESETS.filter((preset) => preset.category === 'core');
const ADVANCED_PRESETS = BOUQUET_PRESETS.filter((preset) => preset.category === 'advanced');
const BASE_URL = 'https://huggingface.co/mcp?login&';

const EXAMPLE_LINKS = [
	{
		title: 'Bouquet override',
		description: 'Specifying a bouquet overrides the tool list saved in your MCP Settings.',
		url: 'https://huggingface.co/mcp?login&bouquet=search',
	},
	{
		title: 'Mix with saved tools',
		description: 'Mixes layer additional tools on top of your saved settings or bouquet.',
		url: 'https://huggingface.co/mcp?login&mix=docs',
	},
	{
		title: 'Add Gradio Spaces',
		footer: 'Separate multiple Spaces with commas. Use “none” to disable Gradio tools while keeping other overrides.',
		url: 'https://huggingface.co/mcp?login&gradio=victor/websearch',
	},
	{
		title: 'Customise Options',
		description: 'Disable Gradio image downloads while keeping other features.',
		url: 'https://huggingface.co/mcp?login&no_image_content=true',
	},
] as const;

function PresetCard({ preset }: { preset: (typeof BOUQUET_PRESETS)[number] }) {
	const entries = preset.builtInTools.map((id) => describeConfigEntry(id));
	const paramOptions: Array<{ label: string; param: string; url: string }> = [];
	const directParams = preset.directParams ?? [];

	if (preset.supportsBouquet) {
		paramOptions.push({
			label: 'Bouquet',
			param: `bouquet=${preset.key}`,
			url: `${BASE_URL}bouquet=${preset.key}`,
		});
	}

	if (preset.supportsMix) {
		paramOptions.push({
			label: 'Mix',
			param: `mix=${preset.key}`,
			url: `${BASE_URL}mix=${preset.key}`,
		});
	}

	return (
		<div className="border border-border rounded-lg p-4 bg-background">
			<div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
		<div className="space-y-3">
			<h4 className="font-semibold text-foreground">{preset.label}</h4>
			<div className="inline-flex items-center gap-2 rounded-md bg-primary/10 text-primary px-2 py-1 text-xs font-mono uppercase tracking-wide">
				<span>Key</span>
				<span className="text-foreground/80 normal-case">{preset.key}</span>
			</div>
			<p className="text-sm text-muted-foreground">{preset.description}</p>
			{paramOptions.length > 0 && (
				<div className="flex flex-wrap items-center gap-2">
					{paramOptions.map((option) => (
						<div
							key={option.param}
							className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-mono border ${
								option.label === 'Bouquet'
									? 'border-sky-300 bg-sky-50/80 text-sky-700 dark:border-sky-400/40 dark:bg-sky-500/10 dark:text-sky-200'
									: 'border-emerald-300 bg-emerald-50/80 text-emerald-700 dark:border-emerald-400/40 dark:bg-emerald-500/10 dark:text-emerald-200'
							}`}
						>
							<span className="uppercase tracking-wide font-semibold">
								{option.label}
							</span>
							<code>{option.param}</code>
							<CopyButton
								content={option.url}
								iconOnly
								variant="ghost"
								size="sm"
								label={`Copy ${option.param}`}
								className="h-6 w-6 shrink-0 hover:bg-white/30 dark:hover:bg-white/10"
							/>
						</div>
					))}
				</div>
			)}
			{directParams.length > 0 && (
				<div className="flex flex-wrap gap-3">
					{directParams.map((option) => (
						<div key={option.param} className="space-y-1">
							<div className="flex items-center gap-2 rounded-lg border border-amber-400/60 bg-amber-50/80 px-3 py-1.5 text-xs font-mono dark:border-amber-300/40 dark:bg-amber-500/10">
								<span className="uppercase tracking-wide text-amber-700 dark:text-amber-300 font-semibold">
									Query
								</span>
								<code className="text-amber-700 dark:text-amber-200">{option.param}</code>
								<CopyButton
									content={`${BASE_URL}${option.param}`}
									iconOnly
									variant="ghost"
									size="sm"
									label={`Copy ${option.param}`}
									className="h-6 w-6 shrink-0 hover:bg-amber-100 dark:hover:bg-amber-500/20"
								/>
							</div>
							{option.description && (
								<p className="text-xs text-muted-foreground">{option.description}</p>
							)}
						</div>
					))}
				</div>
			)}
				</div>
			</div>
			<div className="mt-4">
				<div className="text-xs font-semibold uppercase text-muted-foreground tracking-wide">Includes</div>
				<ul className="mt-2 space-y-2">
					{entries.map((entry) => (
						<li key={entry.id} className="text-sm text-muted-foreground">
							<div className="font-medium text-foreground flex items-center gap-2">
								{entry.label}
								{entry.kind === 'behavior-flag' && (
									<span className="text-[11px] uppercase tracking-wide text-amber-600 bg-amber-100/60 dark:bg-amber-500/20 dark:text-amber-200 px-2 py-0.5 rounded-full">
										Flag
									</span>
								)}
							</div>
							{entry.description && <p className="text-xs text-muted-foreground mt-1">{entry.description}</p>}
						</li>
					))}
				</ul>
			</div>
		</div>
	);
}

export function ToolPresetsCard() {
	const [expanded, setExpanded] = useState(false);

	return (
		<Card className="mt-8">
			<CardHeader className="pb-0">
				<button
					type="button"
					onClick={() => setExpanded((prev) => !prev)}
					className="w-full flex items-center justify-between gap-3 text-left hover:text-primary transition-colors"
					aria-expanded={expanded}
				>
					<div className="text-left">
						<CardTitle className="text-xl font-semibold">Tool Presets and URL Options</CardTitle>
						<CardDescription>
							{expanded
								? 'Use bouquets to replace your active tool list or mixes to add tools on top of saved settings. Attach Gradio Spaces for custom endpoints.'
								: 'Click to view presets and customisation options.'}
						</CardDescription>
					</div>
					<span className="text-muted-foreground">
						{expanded ? <ChevronDown className="h-6 w-6" /> : <ChevronRight className="h-6 w-6" />}
					</span>
				</button>
			</CardHeader>
			{expanded && (
				<CardContent className="space-y-8 pt-0">
					<div className="p-4 border border-dashed border-border rounded-lg bg-muted/40 space-y-3">
						<p className="text-sm text-muted-foreground">
							Apply these options via query parameters or the headers{' '}
							<code className="font-mono text-xs bg-muted px-1 py-0.5 rounded">x-mcp-bouquet</code>,{' '}
							<code className="font-mono text-xs bg-muted px-1 py-0.5 rounded">x-mcp-mix</code>, and{' '}
							<code className="font-mono text-xs bg-muted px-1 py-0.5 rounded">x-mcp-gradio</code>.
						</p>
						<div className="grid gap-3 md:grid-cols-1">
							{EXAMPLE_LINKS.map((example) => (
								<div key={example.title} className="space-y-1">
									<div className="text-xs uppercase tracking-wide text-muted-foreground font-semibold">
										{example.title}
									</div>
									{example.description && <p className="text-xs text-muted-foreground">{example.description}</p>}
									<div className="mt-1 flex items-center gap-2">
										<code className="inline-block bg-background border border-border rounded px-2 py-1 text-xs font-mono">
											{example.url}
										</code>
										<CopyButton
											content={example.url}
											variant="outline"
											size="sm"
											iconOnly
											label={`Copy ${example.title} URL`}
											className="h-7 w-7 shrink-0"
										/>
									</div>
									{example.footer && <p className="text-xs text-muted-foreground mt-1">{example.footer}</p>}
								</div>
							))}
						</div>
					</div>

					<div>
						<h3 className="text-sm font-semibold text-foreground uppercase tracking-wide mb-3">Core presets</h3>
						<div className="space-y-3">
							{CORE_PRESETS.map((preset) => (
								<PresetCard key={preset.key} preset={preset} />
							))}
						</div>
					</div>

					<div>
						<h3 className="text-sm font-semibold text-foreground uppercase tracking-wide mb-3">Advanced presets</h3>
						<p className="text-xs text-muted-foreground mb-3">
							These presets introduce specialist tools or behavior flags. Mix them with your saved settings when you
							need targeted workflows.
						</p>
						<div className="space-y-3">
							{ADVANCED_PRESETS.map((preset) => (
								<PresetCard key={preset.key} preset={preset} />
							))}
						</div>
					</div>
				</CardContent>
			)}
		</Card>
	);
}
