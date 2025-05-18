import type { TestEnv } from './vitest.config'

declare module 'cloudflare:test' {
	interface ProvidedEnv extends TestEnv {}
}
