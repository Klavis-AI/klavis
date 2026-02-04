import type { LoggerBase } from "./logger.js";
import { LogId } from "./logger.js";
import type { ManagedTimeout } from "./managedTimeout.js";
import { setManagedTimeout } from "./managedTimeout.js";

/**
 * Minimal interface for a transport that can be stored in a SessionStore.
 * The transport must have a close method for cleanup.
 */
export type CloseableTransport = {
    close(): Promise<void>;
};

export class SessionStore<T extends CloseableTransport = CloseableTransport> {
    private sessions: {
        [sessionId: string]: {
            logger: LoggerBase;
            transport: T;
            abortTimeout: ManagedTimeout;
            notificationTimeout: ManagedTimeout;
        };
    } = {};

    constructor(
        private readonly idleTimeoutMS: number,
        private readonly notificationTimeoutMS: number,
        private readonly logger: LoggerBase
    ) {
        if (idleTimeoutMS <= 0) {
            throw new Error("idleTimeoutMS must be greater than 0");
        }
        if (notificationTimeoutMS <= 0) {
            throw new Error("notificationTimeoutMS must be greater than 0");
        }
        if (idleTimeoutMS <= notificationTimeoutMS) {
            throw new Error("idleTimeoutMS must be greater than notificationTimeoutMS");
        }
    }

    getSession(sessionId: string): T | undefined {
        this.resetTimeout(sessionId);
        return this.sessions[sessionId]?.transport;
    }

    private resetTimeout(sessionId: string): void {
        const session = this.sessions[sessionId];
        if (!session) {
            return;
        }

        session.abortTimeout.restart();

        session.notificationTimeout.restart();
    }

    private sendNotification(sessionId: string): void {
        const session = this.sessions[sessionId];
        if (!session) {
            this.logger.warning({
                id: LogId.streamableHttpTransportSessionCloseNotificationFailure,
                context: "sessionStore",
                message: `session ${sessionId} not found, no notification delivered`,
            });
            return;
        }
        session.logger.info({
            id: LogId.streamableHttpTransportSessionCloseNotification,
            context: "sessionStore",
            message: "Session is about to be closed due to inactivity",
        });
    }

    setSession(sessionId: string, transport: T, logger: LoggerBase): void {
        const session = this.sessions[sessionId];
        if (session) {
            throw new Error(`Session ${sessionId} already exists`);
        }
        const abortTimeout = setManagedTimeout(async () => {
            if (this.sessions[sessionId]) {
                this.sessions[sessionId].logger.info({
                    id: LogId.streamableHttpTransportSessionCloseNotification,
                    context: "sessionStore",
                    message: "Session closed due to inactivity",
                });

                await this.closeSession(sessionId);
            }
        }, this.idleTimeoutMS);
        const notificationTimeout = setManagedTimeout(
            () => this.sendNotification(sessionId),
            this.notificationTimeoutMS
        );
        this.sessions[sessionId] = {
            transport,
            abortTimeout,
            notificationTimeout,
            logger,
        };
    }

    async closeSession(sessionId: string, closeTransport: boolean = true): Promise<void> {
        const session = this.sessions[sessionId];
        if (!session) {
            throw new Error(`Session ${sessionId} not found`);
        }
        session.abortTimeout.cancel();
        session.notificationTimeout.cancel();
        if (closeTransport) {
            try {
                await session.transport.close();
            } catch (error) {
                this.logger.error({
                    id: LogId.streamableHttpTransportSessionCloseFailure,
                    context: "streamableHttpTransport",
                    message: `Error closing transport ${sessionId}: ${error instanceof Error ? error.message : String(error)}`,
                });
            }
        }
        delete this.sessions[sessionId];
    }

    async closeAllSessions(): Promise<void> {
        await Promise.all(Object.keys(this.sessions).map((sessionId) => this.closeSession(sessionId)));
    }
}
