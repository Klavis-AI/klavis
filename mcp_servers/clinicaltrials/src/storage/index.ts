/**
 * @fileoverview Barrel file for the storage module.
 * This file re-exports the main storage service and interfaces, providing a single
 * entry point for other parts of the application to interact with the storage layer.
 * @module src/storage
 */

export type {
  IStorageProvider,
  StorageOptions,
  ListOptions,
  ListResult,
} from './core/IStorageProvider.js';
export {
  createStorageProvider,
  type StorageFactoryDeps,
} from './core/storageFactory.js';
export { StorageService } from './core/StorageService.js';
export * from './core/storageValidation.js';
