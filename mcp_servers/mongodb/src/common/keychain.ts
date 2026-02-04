import type { Secret } from "mongodb-redact";
export type { Secret } from "mongodb-redact";

/**
 * This class holds the secrets of a single server. Ideally, we might want to have a keychain
 * per session, but right now the loggers are set up by server and are not aware of the concept
 * of session and this would require a bigger refactor.
 *
 * Whenever we identify or create a secret (for example, Atlas login, CLI arguments...) we
 * should register them in the root Keychain (`Keychain.root.register`) or preferably
 * on the session keychain if available `this.session.keychain`.
 **/
export class Keychain {
    private secrets: Secret[];
    private static rootKeychain: Keychain = new Keychain();

    constructor() {
        this.secrets = [];
    }

    static get root(): Keychain {
        return Keychain.rootKeychain;
    }

    register(value: Secret["value"], kind: Secret["kind"]): void {
        this.secrets.push({ value, kind });
    }

    clearAllSecrets(): void {
        this.secrets = [];
    }

    get allSecrets(): Secret[] {
        return [...this.secrets];
    }
}

export function registerGlobalSecretToRedact(value: Secret["value"], kind: Secret["kind"]): void {
    Keychain.root.register(value, kind);
}
