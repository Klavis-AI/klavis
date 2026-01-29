import useSWR from 'swr';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { AlertTriangle } from 'lucide-react';
import { StdioTransportMetrics } from './StdioTransportMetrics';
import { StatefulTransportMetrics } from './StatefulTransportMetrics';
import { StatelessTransportMetrics } from './StatelessTransportMetrics';
import type { TransportMetricsResponse } from '../../shared/transport-metrics.js';

// SWR fetcher function
const fetcher = (url: string) =>
	fetch(url).then((res) => {
		if (!res.ok) {
			throw new Error(`Failed to fetch: ${res.status}`);
		}
		return res.json();
	});

export function TransportMetricsCard() {
	// Use SWR for metrics with auto-refresh every 3 seconds
	const { data: metrics, error } = useSWR<TransportMetricsResponse>('/api/transport-metrics', fetcher, {
		refreshInterval: 3000,
		revalidateOnFocus: true,
		revalidateOnReconnect: true,
	});

	if (error) {
		return (
			<Card>
				<CardHeader>
					<CardTitle>📊 Transport Metrics</CardTitle>
				</CardHeader>
				<CardContent>
					<Alert variant="destructive">
						<AlertTriangle className="h-4 w-4" />
						<AlertTitle>Error Loading Metrics</AlertTitle>
						<AlertDescription>Failed to load transport metrics: {error.message}</AlertDescription>
					</Alert>
				</CardContent>
			</Card>
		);
	}

	if (!metrics) {
		return (
			<Card>
				<CardHeader>
					<CardTitle>📊 Transport Metrics</CardTitle>
				</CardHeader>
				<CardContent>
					<div className="animate-pulse space-y-2">
						<div className="h-4 bg-gray-200 rounded w-3/4"></div>
						<div className="h-4 bg-gray-200 rounded w-1/2"></div>
						<div className="h-4 bg-gray-200 rounded w-2/3"></div>
					</div>
				</CardContent>
			</Card>
		);
	}

	// Route to appropriate component based on transport type
	if (metrics.transport === 'stdio') {
		return <StdioTransportMetrics metrics={metrics} />;
	}

	if (metrics.isStateless) {
		return <StatelessTransportMetrics metrics={metrics} />;
	}

	return <StatefulTransportMetrics metrics={metrics} />;
}
