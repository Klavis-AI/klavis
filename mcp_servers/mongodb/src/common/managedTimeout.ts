export interface ManagedTimeout {
    cancel: () => void;
    restart: () => void;
}

export function setManagedTimeout(callback: () => Promise<void> | void, timeoutMS: number): ManagedTimeout {
    let timeoutId: NodeJS.Timeout | undefined = setTimeout(() => {
        void callback();
    }, timeoutMS);

    function cancel(): void {
        clearTimeout(timeoutId);
        timeoutId = undefined;
    }

    function restart(): void {
        cancel();
        timeoutId = setTimeout(() => {
            void callback();
        }, timeoutMS);
    }

    return {
        cancel,
        restart,
    };
}
