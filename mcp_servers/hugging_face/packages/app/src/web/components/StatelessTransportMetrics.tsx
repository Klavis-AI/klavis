import type { ColumnDef } from '@tanstack/react-table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Table, TableBody, TableCell, TableRow } from './ui/table';
import { Activity, Clock, Globe } from 'lucide-react';
import { DataTable } from './data-table';
import { createSortableHeader } from './data-table-utils';
import type { TransportMetricsResponse } from '../../shared/transport-metrics.js';

type ClientData = {
	name: string;
	version: string;
	requestCount: number;
	activeConnections: number;
	totalConnections: number;
	isConnected: boolean;
	lastSeen: string;
	firstSeen: string;
	toolCallCount: number;
	newIpCount: number;
	anonCount: number;
	uniqueAuthCount: number;
};

/**
 * Format relative time (e.g., "5m ago", "2h ago", "just now")
 */
function formatRelativeTime(timestamp: string): string {
	const now = new Date();
	const time = new Date(timestamp);
	const diffMs = now.getTime() - time.getTime();
	const diffSeconds = Math.floor(diffMs / 1000);

	if (diffSeconds < 60) return 'just now';

	const diffMinutes = Math.floor(diffSeconds / 60);
	if (diffMinutes < 60) return `${diffMinutes}m ago`;

	const diffHours = Math.floor(diffMinutes / 60);
	if (diffHours < 24) return `${diffHours}h ago`;

	const diffDays = Math.floor(diffHours / 24);
	return `${diffDays}d ago`;
}

/**
 * Format uptime in a human-readable way
 */
function formatUptime(seconds: number): string {
	const days = Math.floor(seconds / 86400);
	const hours = Math.floor((seconds % 86400) / 3600);
	const minutes = Math.floor((seconds % 3600) / 60);

	if (days > 0) return `${days}d ${hours}h ${minutes}m`;
	if (hours > 0) return `${hours}h ${minutes}m`;
	return `${minutes}m`;
}

/**
 * Check if a client was recently active (within last 5 minutes)
 */
function isRecentlyActive(lastSeen: string): boolean {
	const now = new Date();
	const lastSeenTime = new Date(lastSeen);
	const diffMs = now.getTime() - lastSeenTime.getTime();
	const diffMinutes = Math.floor(diffMs / 60000);
	return diffMinutes < 5;
}

/**
 * Truncate client name to show first 35 and last 5 characters
 */
function truncateClientName(name: string): string {
	if (name.length <= 42) return name;
	return `${name.slice(0, 35)}.....${name.slice(-5)}`;
}

interface StatelessTransportMetricsProps {
	metrics: TransportMetricsResponse;
}

export function StatelessTransportMetrics({ metrics }: StatelessTransportMetricsProps) {
	const clientData = metrics.clients;

	// Define columns for the client identities table
	const createClientColumns = (): ColumnDef<ClientData>[] => [
		{
			accessorKey: 'name',
			header: createSortableHeader('Client'),
			cell: ({ row }) => {
				const client = row.original;
				const clientDisplay = `${truncateClientName(client.name)}@${client.version}`;
				return (
					<div>
						<p className="font-medium font-mono text-sm" title={`${client.name}@${client.version}`}>
							{clientDisplay}
						</p>
						<p className="text-xs text-muted-foreground">First seen {formatRelativeTime(client.firstSeen)}</p>
					</div>
				);
			},
		},
		{
			accessorKey: 'requestCount',
			header: createSortableHeader('Initializations', 'right'),
			cell: ({ row }) => <div className="text-right font-mono text-sm">{row.getValue<number>('requestCount')}</div>,
		},
		{
			accessorKey: 'toolCallCount',
			header: createSortableHeader('Tool Calls', 'right'),
			cell: ({ row }) => <div className="text-right font-mono text-sm">{row.getValue<number>('toolCallCount')}</div>,
		},
		{
			accessorKey: 'newIpCount',
			header: createSortableHeader('New IPs', 'right'),
			cell: ({ row }) => <div className="text-right font-mono text-sm">{row.getValue<number>('newIpCount')}</div>,
		},
		{
			accessorKey: 'anonCount',
			header: createSortableHeader('Anon/Auth', 'right'),
			cell: ({ row }) => {
				const client = row.original;
				return (
					<div className="text-right font-mono text-sm">
						{client.anonCount}/{client.uniqueAuthCount}
					</div>
				);
			},
		},
		{
			accessorKey: 'isConnected',
			header: createSortableHeader('Status'),
			cell: ({ row }) => {
				const client = row.original;
				return (
					<div>
						{isRecentlyActive(client.lastSeen) ? (
							<Badge variant="success" className="gap-1">
								<Activity className="h-3 w-3" />
								Recent
							</Badge>
						) : (
							<Badge variant="secondary" className="gap-1">
								<Clock className="h-3 w-3" />
								Idle
							</Badge>
						)}
					</div>
				);
			},
		},
		{
			accessorKey: 'lastSeen',
			header: createSortableHeader('Last Seen', 'right'),
			cell: ({ row }) => (
				<div className="text-right text-sm">{formatRelativeTime(row.getValue<string>('lastSeen'))}</div>
			),
		},
	];

	return (
		<Card>
			<CardHeader>
				<CardTitle>📊 Transport Metrics</CardTitle>
				<CardDescription>
					Real-time connection and performance metrics for Stateless HTTP JSON transport
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				{/* Transport Info */}
				<div className="grid grid-cols-2 gap-4">
					<div>
						<p className="text-sm font-medium text-muted-foreground">Transport Type</p>
						<div className="flex items-center gap-2">
							<p className="text-sm font-mono">Stateless HTTP JSON</p>
							<Badge variant="secondary">
								{metrics.sessionLifecycle ? 'analytics' : 'stateless'}
							</Badge>
						</div>
					</div>
					<div>
						<p className="text-sm font-medium text-muted-foreground">Uptime</p>
						<p className="text-sm font-mono">{formatUptime(metrics.uptimeSeconds)}</p>
					</div>
				</div>

				<Separator />

				{/* Metrics Table - 2 columns layout */}
				<div>
					<Table>
						<TableBody>
							<TableRow>
								<TableCell className="font-medium text-sm">Request Count (MCP)</TableCell>
								<TableCell className="text-sm font-mono">{metrics.connections.total}</TableCell>
								<TableCell className="font-medium text-sm">Requests per Minute (tot/3hr/hr)</TableCell>
								<TableCell className="text-sm font-mono">
									{metrics.requests.averagePerMinute}/{metrics.requests.last3Hours}/{metrics.requests.lastHour}
								</TableCell>
							</TableRow>
							<TableRow>
								<TableCell className="font-medium text-sm">Unique IPs</TableCell>
								<TableCell className="text-sm font-mono">{metrics.connections.uniqueIps ?? 0}</TableCell>
								<TableCell className="font-medium text-sm">Client/Server Errors (4xx/5xx)</TableCell>
								<TableCell className="text-sm font-mono">
									{metrics.errors.expected}/{metrics.errors.unexpected}
								</TableCell>
							</TableRow>
							{(metrics.staticPageHits200 !== undefined || metrics.staticPageHits405 !== undefined) && (
								<TableRow>
									<TableCell className="font-medium text-sm">
										<div className="flex items-center gap-1">
											<Globe className="h-3 w-3" />
											hf.co/mcp (200/405)
										</div>
									</TableCell>
									<TableCell className="text-sm font-mono">
										{metrics.staticPageHits200 || 0}/{metrics.staticPageHits405 || 0}
									</TableCell>
									<TableCell className="font-medium text-sm">
										<div className="flex items-center gap-1">Auth Status (Anon/Auth/401)</div>
									</TableCell>
									<TableCell className="text-sm font-mono">
										{metrics.connections.anonymous}/{metrics.connections.authenticated}/
										{metrics.connections.unauthorized || 0}
									</TableCell>
								</TableRow>
							)}
							{/* API Metrics (shown in external API mode) */}
							{metrics.apiMetrics && (
								<>
									<TableRow>
										<TableCell className="font-medium text-sm">Tool API - Anonymous</TableCell>
										<TableCell className="text-sm font-mono">{metrics.apiMetrics.anonymous}</TableCell>
										<TableCell className="font-medium text-sm">Tool API - Authenticated</TableCell>
										<TableCell className="text-sm font-mono">{metrics.apiMetrics.authenticated}</TableCell>
									</TableRow>
									<TableRow>
										<TableCell className="font-medium text-sm">Tool API - 401 Unauthorized</TableCell>
										<TableCell className="text-sm font-mono">{metrics.apiMetrics.unauthorized}</TableCell>
										<TableCell className="font-medium text-sm">Tool API - 403 Forbidden</TableCell>
										<TableCell className="text-sm font-mono">{metrics.apiMetrics.forbidden}</TableCell>
									</TableRow>
								</>
							)}
							{/* Gradio Metrics - Always shown */}
							<TableRow>
								<TableCell className="font-medium text-sm">Gradio Success/Fail</TableCell>
								<TableCell className="text-sm font-mono">
									{metrics.gradioMetrics ? 
										`${metrics.gradioMetrics.success}/${metrics.gradioMetrics.failure}` : 
										'0/0'
									}
								</TableCell>
								
								{/* Session lifecycle metrics (analytics mode) - adjacent cells when present */}
								{metrics.sessionLifecycle ? (
									<>
										<TableCell className="font-medium text-sm">Sessions New/Res-fail/Del</TableCell>
										<TableCell className="text-sm font-mono">
											{metrics.sessionLifecycle.created}/{metrics.sessionLifecycle.resumedFailed}/{metrics.sessionLifecycle.deleted}
										</TableCell>
									</>
								) : (
									<>
										<TableCell className="font-medium text-sm">-</TableCell>
										<TableCell className="text-sm font-mono">-</TableCell>
									</>
								)}
							</TableRow>
						</TableBody>
					</Table>
				</div>

				{/* Client Identities */}
				<>
					<Separator />
					<div>
						<h3 className="text-sm font-semibold text-foreground mb-3">Client Identities</h3>
						<DataTable
							columns={createClientColumns()}
							data={clientData}
							searchColumn="name"
							searchPlaceholder="Filter clients..."
							pageSize={50}
							defaultSorting={[{ id: 'lastSeen', desc: true }]}
						/>
					</div>
				</>
			</CardContent>
		</Card>
	);
}
