import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import type { JSONRPCMessage } from "@modelcontextprotocol/sdk/types.js";

export class InMemoryTransport implements Transport {
    private outputController: ReadableStreamDefaultController<JSONRPCMessage> | undefined;

    private startPromise: Promise<unknown>;

    public output: ReadableStream<JSONRPCMessage>;
    public input: WritableStream<JSONRPCMessage>;

    constructor() {
        const [inputReady, inputResolve] = InMemoryTransport.getPromise();
        const [outputReady, outputResolve] = InMemoryTransport.getPromise();

        this.output = new ReadableStream<JSONRPCMessage>({
            start: (controller): void => {
                this.outputController = controller;
                outputResolve();
            },
        });

        this.input = new WritableStream<JSONRPCMessage>({
            write: (message): void => this.onmessage?.(message),
            start: (): void => {
                inputResolve();
            },
        });

        this.startPromise = Promise.all([inputReady, outputReady]);
    }

    async start(): Promise<void> {
        await this.startPromise;
    }

    send(message: JSONRPCMessage): Promise<void> {
        this.outputController?.enqueue(message);
        return Promise.resolve();
    }

    // eslint-disable-next-line @typescript-eslint/require-await
    async close(): Promise<void> {
        this.outputController?.close();
        this.onclose?.();
    }
    onclose?: (() => void) | undefined;
    onerror?: ((error: Error) => void) | undefined;
    onmessage?: ((message: JSONRPCMessage) => void) | undefined;
    sessionId?: string | undefined;

    private static getPromise(): [Promise<void>, resolve: () => void] {
        let resolve: () => void = () => {};
        const promise = new Promise<void>((res) => {
            resolve = res;
        });
        return [promise, resolve];
    }
}
