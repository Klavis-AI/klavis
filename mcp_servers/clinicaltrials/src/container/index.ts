/**
 * @fileoverview Centralized dependency injection container setup.
 * This file provides a `composeContainer` function to act as the Composition
 * Root for the application. It also serves as a barrel file for exporting
 * the configured container and all DI tokens.
 * @module src/container
 */
import 'reflect-metadata';
import { container } from 'tsyringe';

import { registerCoreServices } from '@/container/registrations/core.js';
import { registerMcpServices } from '@/container/registrations/mcp.js';

let isContainerComposed = false;

/**
 * Composes the DI container by registering all services.
 * This function is designed to be called once at application startup.
 */
export function composeContainer(): void {
  if (isContainerComposed) {
    return;
  }

  registerCoreServices();
  registerMcpServices();

  isContainerComposed = true;
}

// --- Export DI tokens and the container instance ---
export * from '@/container/tokens.js';
export default container;
