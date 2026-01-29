import type { ColumnDef } from '@tanstack/react-table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Table, TableBody, TableCell, TableRow } from './ui/table';
import { Wifi, WifiOff, AlertTriangle, Activity, Clock } from 'lucide-react';
import { DataTable } from './data-table';
import { createSortableHeader } from './data-table-utils';
import { useSessionCache } from '../hooks/useSessionCache';
import type { TransportMetricsResponse } from '../../shared/transport-metrics.js';

type SessionData = {
	id: string;
	connectedAt: string;
	lastActivity: string;
	requestCount: number;
	clientInfo?: {
		name: string;
		version: string;
	};
	isConnected: boolean;
	connectionStatus?: 'Connected' | 'Distressed' | 'Disconnected';
	pingFailures?: number;
	lastPingAttempt?: string;
	ipAddress?: string;
};

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
 * Format milliseconds to human readable time
 */
function formatMilliseconds(ms: number): string {
	if (ms < 1000) return `${ms}ms`;
	if (ms < 60000) return `${Math.round(ms / 1000)}s`;
	return `${Math.round(ms / 60000)}m`;
}

/**
 * Truncate session ID to show first 5 and last 5 characters
 */
function truncateSessionId(id: string): string {
	if (id.length <= 12) return id;
	return `${id.slice(0, 5)}...${id.slice(-5)}`;
}

/**
 * Truncate client name to show first 35 and last 5 characters
 */
function truncateClientName(name: string): string {
	if (name.length <= 42) return name;
	return `${name.slice(0, 35)}.....${name.slice(-5)}`;
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

interface StatefulTransportMetricsProps {
	metrics: TransportMetricsResponse;
}

export function StatefulTransportMetrics({ metrics }: StatefulTransportMetricsProps) {
	const apiSessions = metrics.sessions || [];
	const sessionData = useSessionCache(apiSessions);

	const transportTypeDisplay = {
		streamableHttp: 'Streamable HTTP',
	} as const;

	// Define columns for the sessions table
	const createSessionColumns = (): ColumnDef<SessionData>[] => [
		{
			accessorKey: 'clientInfo',
			header: createSortableHeader('Client'),
			cell: ({ row }) => {
				const session = row.original;
				const clientDisplay = session.clientInfo
					? `${truncateClientName(session.clientInfo.name)}@${session.clientInfo.version}`
					: 'unknown';
				return (
					<div
						className="font-mono text-sm"
						title={session.clientInfo ? `${session.clientInfo.name}@${session.clientInfo.version}` : 'unknown'}
					>
						{clientDisplay}
					</div>
				);
			},
		},
		{
			accessorKey: 'id',
			header: createSortableHeader('Session ID'),
			cell: ({ row }) => (
				<div className="font-mono text-sm" title={row.getValue<string>('id')}>
					{truncateSessionId(row.getValue<string>('id'))}
				</div>
			),
		},
		{
			accessorKey: 'connectionStatus',
			header: createSortableHeader('Status'),
			cell: ({ row }) => {
				const session = row.original;
				const status = session.connectionStatus || (session.isConnected ? 'Connected' : 'Disconnected');

				if (status === 'Connected') {
					return (
						<Badge variant="success" className="gap-1">
							<Wifi className="h-3 w-3" />
							Connected
						</Badge>
					);
				} else if (status === 'Distressed') {
					return (
						<Badge variant="destructive" className="gap-1">
							<AlertTriangle className="h-3 w-3" />
							Distressed {session.pingFailures ? `(${session.pingFailures} failed)` : ''}
						</Badge>
					);
				} else {
					return (
						<Badge variant="secondary" className="gap-1">
							<WifiOff className="h-3 w-3" />
							Disconnected
						</Badge>
					);
				}
			},
		},
		{
			accessorKey: 'connectedAt',
			header: createSortableHeader('Connected'),
			cell: ({ row }) => <div className="text-sm">{formatRelativeTime(row.getValue<string>('connectedAt'))}</div>,
		},
		{
			accessorKey: 'requestCount',
			header: createSortableHeader('Requests', 'right'),
			cell: ({ row }) => <div className="text-right font-mono text-sm">{row.getValue<number>('requestCount')}</div>,
		},
		{
			accessorKey: 'lastActivity',
			header: createSortableHeader('Last Activity'),
			cell: ({ row }) => <div className="text-sm">{formatRelativeTime(row.getValue<string>('lastActivity'))}</div>,
		},
		{
			accessorKey: 'ipAddress',
			header: createSortableHeader('IP Address'),
			cell: ({ row }) => (
				<div className="font-mono text-sm" title={row.getValue<string>('ipAddress') || 'Unknown'}>
					{row.getValue<string>('ipAddress') || '-'}
				</div>
			),
		},
	];

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

	const clientData = metrics.clients;

	return (
		<Card>
			<CardHeader>
				<CardTitle>📊 Transport Metrics</CardTitle>
				<CardDescription>
					Real-time connection and performance metrics for{' '}
					{transportTypeDisplay[metrics.transport as keyof typeof transportTypeDisplay] || metrics.transport} transport
				</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				{/* Transport Info */}
				<div className="grid grid-cols-2 gap-4">
					<div>
						<p className="text-sm font-medium text-muted-foreground">Transport Type</p>
						<p className="text-sm font-mono">
							{transportTypeDisplay[metrics.transport as keyof typeof transportTypeDisplay] || metrics.transport}
						</p>
					</div>
					<div>
						<p className="text-sm font-medium text-muted-foreground">Uptime</p>
						<p className="text-sm font-mono">{formatUptime(metrics.uptimeSeconds)}</p>
					</div>
				</div>

				{/* Configuration for stateful transports */}
				{metrics.configuration && (
					<>
						<div>
							<p className="text-sm font-medium text-muted-foreground mb-2">Configuration</p>
							<div className="grid grid-cols-1 gap-2">
								{metrics.pings && (
									<div className="text-xs text-muted-foreground bg-muted/30 p-2 rounded">
										{metrics.pings.sent > 0 && (
											<p>
												<span className="font-medium">Ping Status:</span> {metrics.pings.successful}/
												{metrics.pings.sent} successful (
												{metrics.pings.sent > 0 ? Math.round((metrics.pings.successful / metrics.pings.sent) * 100) : 0}
												%)
											</p>
										)}
									</div>
								)}
							</div>
						<p className="text-xs text-muted-foreground mt-2">
							Connections checked every {formatMilliseconds(metrics.configuration.heartbeatInterval || 30000)},
							sessions swept every {formatMilliseconds(metrics.configuration.staleCheckInterval)}, removed after{' '}
							{formatMilliseconds(metrics.configuration.staleTimeout)} inactive
								{metrics.configuration.pingEnabled &&
									metrics.configuration.pingInterval &&
									`, pings sent every ${formatMilliseconds(metrics.configuration.pingInterval)}`}
								{metrics.configuration.pingEnabled &&
									`, marked distressed after ${metrics.configuration.pingFailureThreshold || 1} failed ping${(metrics.configuration.pingFailureThreshold || 1) !== 1 ? 's' : ''}`}
							</p>
						</div>
					</>
				)}

				<Separator />

				{/* Metrics Table - 2 columns layout */}
				<div>
					<Table>
						<TableBody>
							<TableRow>
								<TableCell className="font-medium text-sm">Active Connections</TableCell>
								<TableCell className="text-sm font-mono">{metrics.connections.active}</TableCell>
								<TableCell className="font-medium text-sm">Cleaned Sessions</TableCell>
								<TableCell className="text-sm font-mono">{metrics.connections.cleaned ?? 0}</TableCell>
							</TableRow>
							<TableRow>
								<TableCell className="font-medium text-sm">Total Connections</TableCell>
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
							{metrics.sessionLifecycle && (
								<TableRow>
									<TableCell className="font-medium text-sm">Sessions New/Res-fail/Del</TableCell>
									<TableCell className="text-sm font-mono" colSpan={3}>
										{metrics.sessionLifecycle.created}/{metrics.sessionLifecycle.resumedFailed}/{metrics.sessionLifecycle.deleted}
									</TableCell>
								</TableRow>
							)}
							{metrics.pings && (
								<TableRow>
									<TableCell className="font-medium text-sm">Pings Sent</TableCell>
									<TableCell className="text-sm font-mono">{metrics.pings.sent}</TableCell>
									<TableCell className="font-medium text-sm">Ping Success Rate</TableCell>
									<TableCell className="text-sm font-mono">
										{metrics.pings.sent > 0
											? `${Math.round((metrics.pings.successful / metrics.pings.sent) * 100)}%`
											: '-'}
									</TableCell>
								</TableRow>
							)}
							{/* API Metrics (shown in external API mode) */}
							{metrics.apiMetrics && (
								<>
									<TableRow>
										<TableCell className="font-medium text-sm">Anonymous Users</TableCell>
										<TableCell className="text-sm font-mono">{metrics.apiMetrics.anonymous}</TableCell>
										<TableCell className="font-medium text-sm">Authenticated Users</TableCell>
										<TableCell className="text-sm font-mono">{metrics.apiMetrics.authenticated}</TableCell>
									</TableRow>
									<TableRow>
										<TableCell className="font-medium text-sm">401 Unauthorized Users</TableCell>
										<TableCell className="text-sm font-mono">{metrics.apiMetrics.unauthorized}</TableCell>
										<TableCell className="font-medium text-sm">403 Forbidden Users</TableCell>
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
								<TableCell className="font-medium text-sm">-</TableCell>
								<TableCell className="text-sm font-mono">-</TableCell>
							</TableRow>
						</TableBody>
					</Table>
				</div>

				{/* Sessions */}
				<>
					<Separator />
					<div>
						<h3 className="text-sm font-semibold text-foreground mb-3">
							Sessions ({sessionData.filter((s) => s.isConnected).length} active,{' '}
							{sessionData.filter((s) => !s.isConnected).length} disconnected)
						</h3>
						<DataTable
							columns={createSessionColumns()}
							data={sessionData}
							searchColumn="id"
							searchPlaceholder="Filter sessions..."
							pageSize={10}
							defaultSorting={[{ id: 'lastActivity', desc: true }]}
						/>
					</div>
				</>

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
