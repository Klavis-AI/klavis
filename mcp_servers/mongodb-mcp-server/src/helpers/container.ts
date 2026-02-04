import fs from "fs/promises";

let containerEnv: boolean | undefined;

export async function detectContainerEnv(): Promise<boolean> {
    if (containerEnv !== undefined) {
        return containerEnv;
    }

    const detect = async function (): Promise<boolean> {
        if (process.platform !== "linux") {
            return false; // we only support linux containers for now
        }

        if (process.env.container) {
            return true;
        }

        const exists = await Promise.all(
            ["/.dockerenv", "/run/.containerenv", "/var/run/.containerenv"].map(async (file) => {
                try {
                    await fs.access(file);
                    return true;
                } catch {
                    return false;
                }
            })
        );

        return exists.includes(true);
    };

    containerEnv = await detect();
    return containerEnv;
}
