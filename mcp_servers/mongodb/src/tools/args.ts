import { z, type ZodString } from "zod";
import { EJSON } from "bson";

const NO_UNICODE_REGEX = /^[\x20-\x7E]*$/;
export const NO_UNICODE_ERROR = "String cannot contain special characters or Unicode symbols";

const ALLOWED_USERNAME_CHARACTERS_REGEX = /^[a-zA-Z0-9._-]+$/;
export const ALLOWED_USERNAME_CHARACTERS_ERROR =
    "Username can only contain letters, numbers, dots, hyphens, and underscores";

const ALLOWED_REGION_CHARACTERS_REGEX = /^[a-zA-Z0-9_-]+$/;
export const ALLOWED_REGION_CHARACTERS_ERROR = "Region can only contain letters, numbers, hyphens, and underscores";

const ALLOWED_CLUSTER_NAME_CHARACTERS_REGEX = /^[a-zA-Z0-9_-]+$/;
export const ALLOWED_CLUSTER_NAME_CHARACTERS_ERROR =
    "Cluster names can only contain ASCII letters, numbers, and hyphens.";

const ALLOWED_PROJECT_NAME_CHARACTERS_REGEX = /^[a-zA-Z0-9\s()@&+:._',-]+$/;
export const ALLOWED_PROJECT_NAME_CHARACTERS_ERROR =
    "Project names can't be longer than 64 characters and can only contain letters, numbers, spaces, and the following symbols: ( ) @ & + : . _ - ' ,";

export const CommonArgs = {
    string: (): ZodString => z.string().regex(NO_UNICODE_REGEX, NO_UNICODE_ERROR),

    objectId: (fieldName: string): z.ZodString =>
        z
            .string()
            .min(1, `${fieldName} is required`)
            .length(24, `${fieldName} must be exactly 24 characters`)
            .regex(/^[0-9a-fA-F]+$/, `${fieldName} must contain only hexadecimal characters`),
};

export const AtlasArgs = {
    projectId: (): z.ZodString => CommonArgs.objectId("projectId"),

    organizationId: (): z.ZodString => CommonArgs.objectId("organizationId"),

    clusterName: (): z.ZodString =>
        z
            .string()
            .min(1, "Cluster name is required")
            .max(64, "Cluster name must be 64 characters or less")
            .regex(ALLOWED_CLUSTER_NAME_CHARACTERS_REGEX, ALLOWED_CLUSTER_NAME_CHARACTERS_ERROR),

    connectionType: (): z.ZodDefault<z.ZodEnum<["standard", "private", "privateEndpoint"]>> =>
        z.enum(["standard", "private", "privateEndpoint"]).default("standard"),

    projectName: (): z.ZodString =>
        z
            .string()
            .min(1, "Project name is required")
            .max(64, "Project name must be 64 characters or less")
            .regex(ALLOWED_PROJECT_NAME_CHARACTERS_REGEX, ALLOWED_PROJECT_NAME_CHARACTERS_ERROR),

    username: (): z.ZodString =>
        z
            .string()
            .min(1, "Username is required")
            .max(100, "Username must be 100 characters or less")
            .regex(ALLOWED_USERNAME_CHARACTERS_REGEX, ALLOWED_USERNAME_CHARACTERS_ERROR),

    ipAddress: (): z.ZodString => z.string().ip({ version: "v4" }),

    cidrBlock: (): z.ZodString => z.string().cidr(),

    region: (): z.ZodString =>
        z
            .string()
            .min(1, "Region is required")
            .max(50, "Region must be 50 characters or less")
            .regex(ALLOWED_REGION_CHARACTERS_REGEX, ALLOWED_REGION_CHARACTERS_ERROR),

    password: (): z.ZodString =>
        z.string().min(1, "Password is required").max(100, "Password must be 100 characters or less"),
};

function toEJSON<T extends object | undefined>(value: T): T {
    if (!value) {
        return value;
    }

    return EJSON.deserialize(value, { relaxed: false }) as T;
}

export function zEJSON(): z.AnyZodObject {
    return z.object({}).passthrough().transform(toEJSON) as unknown as z.AnyZodObject;
}
