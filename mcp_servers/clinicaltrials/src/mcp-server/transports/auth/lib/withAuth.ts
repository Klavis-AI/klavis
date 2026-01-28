/**
 * @fileoverview Higher-order functions for declarative, scope-based authorization.
 * @module src/mcp-server/transports/auth/lib/withAuth
 */
import type { SdkContext } from '@/mcp-server/tools/utils/index.js';
import { withRequiredScopes } from '@/mcp-server/transports/auth/lib/authUtils.js';
import type { RequestContext } from '@/utils/index.js';

/**
 * A higher-order function that wraps a **tool's** logic function with a
 * scope-based authorization check.
 *
 * @param {string[]} requiredScopes An array of scopes required to execute the logic.
 * @param {Function} logicFn The core tool logic function to execute if authorization succeeds.
 * @returns A new async function that performs the auth check before executing the logic.
 */
export function withToolAuth<TInput, TOutput>(
  requiredScopes: string[],
  logicFn: (
    input: TInput,
    context: RequestContext,
    sdkContext: SdkContext,
  ) => TOutput | Promise<TOutput>,
): (
  input: TInput,
  context: RequestContext,
  sdkContext: SdkContext,
) => Promise<TOutput> {
  return async (
    input: TInput,
    context: RequestContext,
    sdkContext: SdkContext,
  ): Promise<TOutput> => {
    withRequiredScopes(requiredScopes);
    return Promise.resolve(logicFn(input, context, sdkContext));
  };
}

/**
 * A higher-order function that wraps a **resource's** logic function with a
 * scope-based authorization check.
 *
 * @param {string[]} requiredScopes An array of scopes required to execute the logic.
 * @param {Function} logicFn The core resource logic function to execute if authorization succeeds.
 * @returns A new async function that performs the auth check before executing the logic.
 */
export function withResourceAuth<TUri, TParams, TOutput>(
  requiredScopes: string[],
  logicFn: (
    uri: TUri,
    params: TParams,
    context: RequestContext,
  ) => TOutput | Promise<TOutput>,
): (uri: TUri, params: TParams, context: RequestContext) => Promise<TOutput> {
  return async (
    uri: TUri,
    params: TParams,
    context: RequestContext,
  ): Promise<TOutput> => {
    withRequiredScopes(requiredScopes);
    return Promise.resolve(logicFn(uri, params, context));
  };
}