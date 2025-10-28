import axios, { AxiosResponse } from "axios";
import { OpenAPI } from "@mintlify/openapi-types";

// A recursive type representing nested objects or strings
export type NestedRecord = string | { [key: string]: NestedRecord };

export type SimpleRecord = Record<string, NestedRecord>;

/**
 * Initializes an object along a given path, creating nested objects if needed.
 */
export function initializeObject(
  obj: SimpleRecord,
  path: string[]
): SimpleRecord {
  let current: NestedRecord = obj;

  for (const key of path) {
    if (!current[key] || typeof current[key] !== "object") {
      current[key] = {};
    }
    current = current[key];
  }
  return current;
}

/**
 * Gets a unique file ID based on spec title and version.
 */
export function getFileId(
  spec: OpenAPI.Document,
  index: number
): string | number {
  var _a;
  return ((_a = spec.info) === null || _a === void 0 ? void 0 : _a.title) &&
    spec?.info?.version
    ? `${spec?.info?.title} - ${spec?.info?.version}`
    : index;
}

/**
 * Throws an error if the Axios response indicates a failure.
 */
export function throwOnAxiosError(
  response: AxiosResponse,
  errMsg: string
): void {
  var _a, _b;
  if (response.status !== 200) {
    if (
      ((_a = response.headers["content-type"]) === null || _a === void 0
        ? void 0
        : _a.includes("application/json")) &&
      ((_b = response.data) === null || _b === void 0 ? void 0 : _b.error)
    ) {
      throw new Error(`${errMsg}: ${response.data.error}`);
    } else {
      throw new Error(
        `${errMsg}: ${response.status} ${response.statusText || ""}`
      );
    }
  }
  if (!response.data) {
    throw new Error(`${errMsg}: ${response.status} ${response.statusText}`);
  }
}

/**
 * Formats various types of errors into human-readable strings.
 */
export function formatErr(err: unknown) {
  var _a, _b;
  if (axios.isAxiosError(err)) {
    if (err.message) {
      return err.message;
    } else if (err.response) {
      return (_b =
        (_a = err.response.data) === null || _a === void 0
          ? void 0
          : _a.error) !== null && _b !== void 0
        ? _b
        : `${err.response.status} ${err.response.statusText}`;
    } else if (err.request) {
      return "No response received from server";
    } else {
      err = "An unknown error occurred";
    }
  } else if (err instanceof Error) {
    return err.message;
  } else {
    return JSON.stringify(err, undefined, 2);
  }
}
