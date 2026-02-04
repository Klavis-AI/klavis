// Stub for UIRegistry - UI functionality is not enabled in this build
export type UIRegistryOptions = {
    enabled?: boolean;
};

export class UIRegistry {
    constructor(_options?: UIRegistryOptions) {}
    
    async get(_name: string): Promise<string | undefined> {
        return undefined;
    }
}
