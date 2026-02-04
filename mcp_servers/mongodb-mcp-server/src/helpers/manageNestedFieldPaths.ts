// We respect the max nesting depth allowed for BSON documents.
// Ref: https://www.mongodb.com/docs/manual/reference/limits/?atlas-provider=aws&atlas-class=general#mongodb-limit-Nested-Depth-for-BSON-Documents
const MAX_DEPTH = 100;

export function setFieldPath(document: Record<string, unknown>, fieldPath: string, value: unknown): void {
    const parts = fieldPath.split(".");
    if (parts.some((part) => !part.trim())) {
        throw new Error(`Invalid field path: '${fieldPath}'`);
    }

    if (parts.length > MAX_DEPTH) {
        throw new Error(`Field path "${fieldPath}" has too many nested levels (maximum ${MAX_DEPTH} allowed).`);
    }
    _setFieldPath(document, parts, value, "");
}

function _setFieldPath(current: Record<string, unknown>, parts: string[], value: unknown, parentPath: string): void {
    const [key, ...rest] = parts;

    // This should never happen since we validate fieldPath in setFieldPath,
    // but TypeScript needs this check for type narrowing.
    if (!key) {
        throw new Error(`Cannot set field at provided path: Unexpected empty key - '${key}' in field path.`);
    }

    if (rest.length === 0) {
        safeDefineProperty(current, key, value);
        return;
    }

    const currentPath = parentPath ? `${parentPath}.${key}` : key;
    const hasOwnProperty = Object.prototype.hasOwnProperty.call(current, key);
    const existingValue = hasOwnProperty ? current[key] : undefined;

    if (existingValue === undefined || existingValue === null) {
        safeDefineProperty(current, key, {});
    } else if (typeof existingValue !== "object" || Array.isArray(existingValue)) {
        throw new Error(`Cannot set field at provided path: intermediate path '${currentPath}' is not an object.`);
    }

    _setFieldPath(current[key] as Record<string, unknown>, rest, value, currentPath);
}

// The provided field path might include some internal Object properties such as
// `__proto__`. For such paths, we need to ensure that we don't override the
// derived properties on the object so we explicitly set these properties as
// Object's own property.
function safeDefineProperty(obj: Record<string, unknown>, key: string, value: unknown): void {
    Object.defineProperty(obj, key, {
        value,
        writable: true,
        enumerable: true,
        configurable: true,
    });
}
