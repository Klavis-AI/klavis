# Repository Guidelines

## Project Structure & Module Organization
- `packages/app`: MCP server plus management web UI. Server code lives in `packages/app/src/server`, UI in `packages/app/src/web`, and tests in `packages/app/test`.
- `packages/mcp`: shared MCP tools/library consumed by the server. Source is in `packages/mcp/src`, with tests in `packages/mcp/test` and a few `*.test.ts` files co-located in `src`.
- `packages/e2e-python`: Python-based end-to-end harnesses and fixtures.
- Root-level docs and support files live in `docs/`, `docs-internal/`, `scripts/`, `spec/`, and `Dockerfile`.

## Build, Test, and Development Commands
- `pnpm install`: install workspace dependencies (Corepack-managed pnpm).
- `pnpm build`: build all workspace packages.
- `pnpm dev`: watch the MCP package and run the server with HMR.
- `pnpm start`: start the production server from `packages/app`.
- `pnpm lint`, `pnpm typecheck`, `pnpm format`, `pnpm test`: run repo-wide checks.
- Package-specific tests: `pnpm -C packages/app test` or `pnpm -C packages/mcp test`.
- Full local pipeline: `pnpm run buildrun` (clean, build, lint, test, start).

## Coding Style & Naming Conventions
- TypeScript ESM across packages.
- Prettier enforces tabs (`useTabs: true`, `tabWidth: 2`), semicolons, single quotes, and `printWidth: 120`.
- ESLint rules are strict in `packages/mcp` and server code (no `any`, consistent type imports, prefer `interface` type definitions).
- Tests use `.test.ts` or `.spec.ts` naming.

## Testing Guidelines
- Unit/integration tests run with Vitest in both `packages/app` and `packages/mcp`.
- Run all tests with `pnpm test` or package-specific commands above.
- No explicit coverage gate is configured; add tests for new tools, transports, or formatting logic.

## Commit & Pull Request Guidelines
- Recent history mixes merge commits and conventional-style messages like `chore: release vX`; no enforced convention.
- Keep commits small and descriptive; add a scope when it clarifies the area (`app`, `mcp`).
- PRs should include a concise summary, test results, linked issue (if applicable), and screenshots for UI changes under `packages/app/src/web`.

## Security & Configuration Tips
- Provide auth via environment variables (`DEFAULT_HF_TOKEN`, `HF_TOKEN`); do not commit secrets.
- `TRANSPORT` controls server mode (`stdio`, `streamableHttp`, `streamableHttpJson`). Document any new env vars in `README.md`.
