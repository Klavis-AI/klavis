import { LRUCache } from "lru-cache";
import { BaseEvent } from "./types.js";

/**
 * Singleton class for in-memory telemetry event caching
 * Provides a central storage for telemetry events that couldn't be sent
 * Uses LRU cache to automatically drop oldest events when limit is exceeded
 */
export class EventCache {
    private static instance: EventCache;
    private static readonly MAX_EVENTS = 1000;

    private cache: LRUCache<number, BaseEvent>;
    private nextId = 0;

    constructor() {
        this.cache = new LRUCache({
            max: EventCache.MAX_EVENTS,
            // Using FIFO eviction strategy for events
            allowStale: false,
            updateAgeOnGet: false,
        });
    }

    /**
     * Gets the singleton instance of EventCache
     * @returns The EventCache instance
     */
    public static getInstance(): EventCache {
        if (!EventCache.instance) {
            EventCache.instance = new EventCache();
        }
        return EventCache.instance;
    }

    /**
     * Gets a copy of the currently cached events
     * @returns Array of cached BaseEvent objects
     */
    public getEvents(): BaseEvent[] {
        return Array.from(this.cache.values());
    }

    /**
     * Appends new events to the cached events
     * LRU cache automatically handles dropping oldest events when limit is exceeded
     * @param events - The events to append
     */
    public appendEvents(events: BaseEvent[]): void {
        for (const event of events) {
            this.cache.set(this.nextId++, event);
        }
    }

    /**
     * Clears all cached events
     */
    public clearEvents(): void {
        this.cache.clear();
        this.nextId = 0;
    }
}
