import { useEffect, useRef, useState } from 'react';

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
};

type CachedSession = SessionData & {
	disconnectedAt?: string;
	lastSeenAt: string;
};

const RETENTION_TIME = 5 * 60 * 1000; // 5 minutes in milliseconds

/**
 * Custom hook to manage session data with 5-minute retention after disconnect
 * @param activeSessions - Current active sessions from the API
 * @returns Merged list of active and recently disconnected sessions
 */
export function useSessionCache(activeSessions: SessionData[]): SessionData[] {
	const [cachedSessions, setCachedSessions] = useState<Map<string, CachedSession>>(new Map());
	const cleanupIntervalRef = useRef<NodeJS.Timeout>();

	useEffect(() => {
		const now = new Date().toISOString();
		const activeSessionIds = new Set(activeSessions.map((s) => s.id));

		setCachedSessions((prevCache) => {
			const newCache = new Map(prevCache);

			// Update or add active sessions
			activeSessions.forEach((session) => {
				newCache.set(session.id, {
					...session,
					lastSeenAt: now,
					disconnectedAt: undefined,
				});
			});

			// Mark sessions as disconnected if they're no longer in active list
			newCache.forEach((cachedSession, sessionId) => {
				if (!activeSessionIds.has(sessionId) && !cachedSession.disconnectedAt) {
					newCache.set(sessionId, {
						...cachedSession,
						isConnected: false,
						connectionStatus: 'Disconnected',
						disconnectedAt: now,
						lastActivity: cachedSession.lastActivity || now,
					});
				}
			});

			return newCache;
		});
	}, [activeSessions]);

	// Cleanup old disconnected sessions every 30 seconds
	useEffect(() => {
		const cleanup = () => {
			const now = Date.now();

			setCachedSessions((prevCache) => {
				const newCache = new Map(prevCache);

				// Remove sessions that have been disconnected for more than RETENTION_TIME
				newCache.forEach((session, sessionId) => {
					if (session.disconnectedAt) {
						const disconnectedTime = new Date(session.disconnectedAt).getTime();
						if (now - disconnectedTime > RETENTION_TIME) {
							newCache.delete(sessionId);
						}
					}
				});

				return newCache;
			});
		};

		// Run cleanup immediately and then every 30 seconds
		cleanup();
		cleanupIntervalRef.current = setInterval(cleanup, 30000);

		return () => {
			if (cleanupIntervalRef.current) {
				clearInterval(cleanupIntervalRef.current);
			}
		};
	}, []);

	// Convert Map to array and sort by connection status and last activity
	const mergedSessions = Array.from(cachedSessions.values()).sort((a, b) => {
		// Connected sessions first
		if (a.isConnected !== b.isConnected) {
			return a.isConnected ? -1 : 1;
		}
		// Then by last activity (most recent first)
		return new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime();
	});

	return mergedSessions;
}
