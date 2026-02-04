import { randomBytes } from "crypto";
import { promisify } from "util";

const randomBytesAsync = promisify(randomBytes);

export async function generateSecurePassword(): Promise<string> {
    const buf = await randomBytesAsync(16);
    const pass = buf.toString("base64url");
    return pass;
}
