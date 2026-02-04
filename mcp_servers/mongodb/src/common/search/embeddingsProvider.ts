import { createVoyage } from "voyage-ai-provider";
import type { VoyageProvider } from "voyage-ai-provider";
import { embedMany } from "ai";
import type { UserConfig } from "../config/userConfig.js";
import { createFetch } from "@mongodb-js/devtools-proxy-support";
import {
    type EmbeddingParameters,
    type VoyageEmbeddingParameters,
    type VoyageModels,
    zVoyageAPIParameters,
} from "../../tools/mongodb/mongodbSchemas.js";

type EmbeddingsInput = string;
type Embeddings = number[] | unknown[];

export interface EmbeddingsProvider<
    SupportedModels extends string,
    SupportedEmbeddingParameters extends EmbeddingParameters,
> {
    embed(
        modelId: SupportedModels,
        content: EmbeddingsInput[],
        parameters: SupportedEmbeddingParameters
    ): Promise<Embeddings[]>;
}

class VoyageEmbeddingsProvider implements EmbeddingsProvider<VoyageModels, VoyageEmbeddingParameters> {
    private readonly voyage: VoyageProvider;

    constructor({ voyageApiKey }: UserConfig, providedFetch?: typeof fetch) {
        if (!voyageApiKey) {
            throw new Error("The VoyageAI API Key does not exist. This is likely a bug.");
        }

        // We should always use, by default, any enterprise proxy that the user has configured.
        // Direct requests to VoyageAI might get blocked by the network if they don't go through
        // the provided proxy.
        const customFetch: typeof fetch = (providedFetch ??
            createFetch({ useEnvironmentVariableProxies: true })) as unknown as typeof fetch;

        this.voyage = createVoyage({ apiKey: voyageApiKey, fetch: customFetch });
    }

    static isConfiguredIn({ voyageApiKey, previewFeatures }: UserConfig): boolean {
        return previewFeatures.includes("search") && !!voyageApiKey;
    }

    async embed<Model extends VoyageModels>(
        modelId: Model,
        content: EmbeddingsInput[],
        parameters: VoyageEmbeddingParameters
    ): Promise<Embeddings[]> {
        // This ensures that if we receive any random parameter from the outside (agent or us)
        // it's stripped before sending it to Voyage, as Voyage will reject the request on
        // a single unknown parameter.
        const voyage = zVoyageAPIParameters.parse(parameters);
        const model = this.voyage.textEmbeddingModel(modelId);
        const { embeddings } = await embedMany({
            model,
            values: content,
            providerOptions: { voyage },
        });

        return embeddings;
    }
}

export function getEmbeddingsProvider(
    userConfig: UserConfig
): EmbeddingsProvider<VoyageModels, VoyageEmbeddingParameters> | undefined {
    if (VoyageEmbeddingsProvider.isConfiguredIn(userConfig)) {
        return new VoyageEmbeddingsProvider(userConfig);
    }

    return undefined;
}
