import type { ColumnDef } from '@tanstack/react-table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Wifi, WifiOff } from 'lucide-react';
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

interface StdioTransportMetricsProps {
	metrics: TransportMetricsResponse;
}

export function StdioTransportMetrics({ metrics }: StdioTransportMetricsProps) {
	const apiSessions = metrics.sessions || [];
	const sessionData = useSessionCache(apiSessions);

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
			accessorKey: 'isConnected',
			header: createSortableHeader('Status'),
			cell: ({ row }) => {
				const session = row.original;
				return (
					<Badge variant={session.isConnected ? 'success' : 'secondary'} className="gap-1">
						{session.isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
						{session.isConnected ? 'Connected' : 'Disconnected'}
					</Badge>
				);
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
	];

	return (
		<Card>
			<CardHeader>
				<CardTitle>📊 Transport Metrics</CardTitle>
				<CardDescription>Real-time connection and performance metrics for STDIO transport</CardDescription>
			</CardHeader>
			<CardContent className="space-y-4">
				{/* Transport Info */}
				<div className="grid grid-cols-2 gap-4">
					<div>
						<p className="text-sm font-medium text-muted-foreground">Transport Type</p>
						<p className="text-sm font-mono">STDIO</p>
					</div>
					<div>
						<p className="text-sm font-medium text-muted-foreground">Uptime</p>
						<p className="text-sm font-mono">{formatUptime(metrics.uptimeSeconds)}</p>
					</div>
				</div>

				{/* Session */}
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
			</CardContent>
		</Card>
	);
}
