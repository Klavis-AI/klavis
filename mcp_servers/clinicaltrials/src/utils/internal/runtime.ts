/**
 * @fileoverview Runtime capability detection for multi-environment support.
 * Detects presence of Node features, Web/Workers APIs, and common globals.
 * @module src/utils/internal/runtime
 */

export interface RuntimeCapabilities {
  isNode: boolean;
  isWorkerLike: boolean;
  isBrowserLike: boolean;
  hasProcess: boolean;
  hasBuffer: boolean;
  hasTextEncoder: boolean;
  hasPerformanceNow: boolean;
}

// Best-effort static detection without throwing in restricted envs
const safeHas = (key: string): boolean => {
  try {
    // @ts-expect-error index access on globalThis
    return typeof globalThis[key] !== 'undefined';
  } catch {
    return false;
  }
};

const isNode =
  typeof process !== 'undefined' &&
  typeof (process as unknown as { versions?: { node?: string } }).versions
    ?.node === 'string';
const hasProcess = typeof process !== 'undefined';
const hasBuffer = typeof Buffer !== 'undefined';
const hasTextEncoder = safeHas('TextEncoder');
const hasPerformanceNow =
  typeof (globalThis as { performance?: { now?: () => number } }).performance
    ?.now === 'function';

// Cloudflare Workers expose "Web Worker"-like environment (self, caches, fetch, etc.)
const isWorkerLike =
  !isNode &&
  typeof (globalThis as { WorkerGlobalScope?: unknown }).WorkerGlobalScope !==
    'undefined';
const isBrowserLike = !isNode && !isWorkerLike && safeHas('window');

export const runtimeCaps: RuntimeCapabilities = {
  isNode,
  isWorkerLike,
  isBrowserLike,
  hasProcess,
  hasBuffer,
  hasTextEncoder,
  hasPerformanceNow,
};
