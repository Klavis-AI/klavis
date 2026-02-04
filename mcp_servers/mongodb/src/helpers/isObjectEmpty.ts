type EmptyObject = { [x: string]: never } | null | undefined;

export function isObjectEmpty(value: object | null | undefined): value is EmptyObject {
    if (!value) {
        return true;
    }

    for (const prop in value) {
        if (Object.prototype.hasOwnProperty.call(value, prop)) {
            return false;
        }
    }

    return true;
}
