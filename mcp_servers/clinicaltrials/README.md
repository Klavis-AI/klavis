<div align="center">
  <h1>clinicaltrialsgov-mcp-server</h1>
  <p><b>ClinicalTrials.gov Model Context Protocol (MCP) Server with tools to programmatically search, retrieve, compare, analyze, and find eligible clinical trials. Built for performance and scalability, with native support for serverless deployment (Cloudflare Workers).</b></p>
</div>

<div align="center">

[![Version](https://img.shields.io/badge/Version-1.4.0-blue.svg?style=flat-square)](./CHANGELOG.md) [![MCP Spec](https://img.shields.io/badge/MCP%20Spec-2025--06--18-8A2BE2.svg?style=flat-square)](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-06-18/changelog.mdx) [![MCP SDK](https://img.shields.io/badge/MCP%20SDK-^1.18.2-green.svg?style=flat-square)](https://modelcontextprotocol.io/) [![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg?style=flat-square)](./LICENSE) [![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg?style=flat-square)](https://github.com/cyanheads/clinicaltrialsgov-mcp-server/issues) [![TypeScript](https://img.shields.io/badge/TypeScript-^5.9.3-3178C6.svg?style=flat-square)](https://www.typescriptlang.org/) [![Bun](https://img.shields.io/badge/Bun-v1.2.23-blueviolet.svg?style=flat-square)](https://bun.sh/) [![Code Coverage](https://img.shields.io/badge/Coverage-92.46%25-brightgreen.svg?style=flat-square)](./vitest.config.ts)

</div>

---

## 🛠️ Tools Overview

This server provides five powerful tools for accessing and analyzing clinical trial data from ClinicalTrials.gov:

| Tool Name                              | Description                                                                                                           |
| :------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| `clinicaltrials_search_studies`        | Searches for clinical studies using query terms, filters, pagination, and sorting. Now includes geographic filtering. |
| `clinicaltrials_get_study`             | Fetches one or more clinical studies by their NCT IDs, returning either full data or concise summaries.               |
| `clinicaltrials_analyze_trends`        | Performs statistical analysis on up to 5000 studies, with new time-series analysis by year and month.                 |
| `clinicaltrials_compare_studies`       | Performs a detailed side-by-side comparison of 2-5 clinical studies, highlighting commonalities and differences.      |
| `clinicaltrials_find_eligible_studies` | Matches patient profiles to eligible clinical trials, filtering by age, sex, conditions, and location.                |

### `clinicaltrials_search_studies`

**Search and discover clinical trials** using free-text queries and advanced filters.

**Key Features:**

- Free-text search across all study fields (conditions, interventions, sponsors, titles)
- Advanced filtering with ClinicalTrials.gov's official filter syntax
- Pagination support for large result sets (up to 200 studies per page)
- Sorting by enrollment count, update date, or other fields
- Returns concise summaries with NCT IDs, titles, and recruitment status

**Example Use Cases:**

- "Find all Phase 3 diabetes studies currently recruiting"
- "Show me cancer immunotherapy trials in the United States"
- "List studies by pharmaceutical companies sorted by size"

📖 **[View detailed examples →](./examples/clinicaltrials_search_studies.md)**

---

### `clinicaltrials_get_study`

**Retrieve detailed information** for specific clinical trials by their NCT ID.

**Key Features:**

- Fetch single or multiple studies (up to 5 at once)
- Choice between full data (complete protocol, results, documents) or concise summaries
- Full study data includes: protocol sections, results, adverse events, outcome measures, eligibility criteria, locations, and more
- Automatic error handling for invalid or non-existent NCT IDs
- Partial success reporting when fetching multiple studies

**Example Use Cases:**

- "Get the full details for study NCT03372603"
- "Show me a summary of these three studies: NCT12345678, NCT87654321, NCT11223344"
- "What were the results and adverse events for NCT04280783?"

📖 **[View detailed examples →](./examples/clinicaltrials_get_study.md)**

---

### `clinicaltrials_analyze_trends`

**Perform statistical analysis** across thousands of clinical trials.

**Key Features:**

- Aggregate up to 5,000 studies per analysis
- Multiple analysis types: status distribution, geographic spread, sponsor types, trial phases
- Combine multiple analysis types in a single request
- Advanced filtering to focus analysis on specific subsets
- Returns counts, percentages, and top categories

**Example Use Cases:**

- "What's the status breakdown of all COVID-19 vaccine Phase 3 trials?"
- "Which countries have the most Alzheimer's research studies?"
- "Show me the phase distribution and sponsor types for cancer immunotherapy trials"

📖 **[View detailed examples →](./examples/clinicaltrials_analyze_trends.md)**

---

### `clinicaltrials_compare_studies`

**Compare and contrast multiple studies** to identify key similarities and differences.

**Key Features:**

- Side-by-side comparison of 2-5 studies by NCT ID
- Extracts and contrasts eligibility, design, interventions, outcomes, sponsors, and more
- Generates a summary of commonalities and differences
- Handles partial failures gracefully if some studies cannot be fetched
- Highly configurable to focus on specific fields of interest

**Example Use Cases:**

- "Compare the study design and eligibility criteria for NCT04516746 and NCT04516759"
- "What are the main differences in interventions and outcomes between these three leading Alzheimer's trials?"
- "Show me a side-by-side of sponsor and location data for these competitor studies"

📖 **[View detailed examples →](./examples/clinicaltrials-compare-studies.md)**

---

### `clinicaltrials_find_eligible_studies`

**Find relevant clinical trials** based on a patient's specific medical profile and demographics.

**Key Features:**

- Matches patients using age, sex, and a list of medical conditions
- Filters studies by location (country, state, city) to find nearby trials
- Ranks results by a relevance score based on how well the patient matches the study's criteria
- Provides a clear summary of why a patient is a potential match for a study

**Example Use Cases:**

- "Find recruiting migraine studies in Canada for a 35-year-old female"
- "Are there any local clinical trials for a 68-year-old male with Type 2 Diabetes and Hypertension?"
- "Search for healthy volunteer studies for a 25-year-old in California"

📖 **[View detailed examples →](./examples/clinicaltrials-find-eligible-studies.md)**

## ✨ Features

This server is built on the [`mcp-ts-template`](https://github.com/cyanheads/mcp-ts-template) and inherits its rich feature set:

- **Declarative Tools**: Define agent capabilities in single, self-contained files. The framework handles registration, validation, and execution.
- **Robust Error Handling**: A unified `McpError` system ensures consistent, structured error responses.
- **Pluggable Authentication**: Secure your server with zero-fuss support for `none`, `jwt`, or `oauth` modes.
- **Abstracted Storage**: Swap storage backends (`in-memory`, `filesystem`, `Supabase`, `Cloudflare KV/R2`) without changing business logic.
- **Full-Stack Observability**: Deep insights with structured logging (Pino) and optional, auto-instrumented OpenTelemetry for traces and metrics.
- **Dependency Injection**: Built with `tsyringe` for a clean, decoupled, and testable architecture.
- **Edge-Ready**: Write code once and run it seamlessly on your local machine or at the edge on Cloudflare Workers.

Plus, specialized features for **ClinicalTrials.gov**:

- **Official API Integration**: Type-safe, comprehensive access to the ClinicalTrials.gov v2 API.
- **Advanced Search & Analysis**: Tools for complex queries, filtering, and statistical aggregation of trial data.
- **Optimized Data Handling**: Automatic cleaning and simplification of API responses for efficient agent consumption.

## 🚀 Getting Started

### MCP Client Settings/Configuration

Add the following to your MCP Client configuration file (e.g., `cline_mcp_settings.json`).

```json
{
  "mcpServers": {
    "clinicaltrialsgov-mcp-server": {
      "type": "stdio",
      "command": "bunx",
      "args": ["clinicaltrialsgov-mcp-server@latest"],
      "env": {
        "MCP_TRANSPORT_TYPE": "stdio",
        "MCP_LOG_LEVEL": "info"
      }
    }
  }
}
```

Or for Streamable HTTP:

```bash
MCP_TRANSPORT_TYPE=http
MCP_HTTP_PORT=3015
```

### Prerequisites

- [Bun v1.2.0](https://bun.sh/) or higher.

### Installation

1.  **Clone the repository:**

```sh
git clone https://github.com/cyanheads/clinicaltrialsgov-mcp-server.git
```

2.  **Navigate into the directory:**

```sh
cd clinicaltrialsgov-mcp-server
```

3.  **Install dependencies:**

```sh
bun install
```

## 🛠️ Core Capabilities: ClinicalTrials.gov Tools

This server equips AI agents with specialized tools to interact with the ClinicalTrials.gov database.

## ⚙️ Configuration

All configuration is centralized and validated at startup in `src/config/index.ts`. Key environment variables in your `.env` file include:

| Variable                | Description                                                                    | Default     |
| :---------------------- | :----------------------------------------------------------------------------- | :---------- |
| `MCP_TRANSPORT_TYPE`    | The transport to use: `stdio` or `http`.                                       | `http`      |
| `MCP_HTTP_PORT`         | The port for the HTTP server.                                                  | `3017`      |
| `MCP_AUTH_MODE`         | Authentication mode: `none`, `jwt`, or `oauth`.                                | `none`      |
| `STORAGE_PROVIDER_TYPE` | Storage backend: `in-memory`, `filesystem`, `supabase`, `cloudflare-kv`, `r2`. | `in-memory` |
| `OTEL_ENABLED`          | Set to `true` to enable OpenTelemetry.                                         | `false`     |
| `LOG_LEVEL`             | The minimum level for logging (`debug`, `info`, `warn`, `error`).              | `info`      |
| `MCP_AUTH_SECRET_KEY`   | **Required for `jwt` auth.** A 32+ character secret key.                       | `(none)`    |
| `OAUTH_ISSUER_URL`      | **Required for `oauth` auth.** URL of the OIDC provider.                       | `(none)`    |

## ▶️ Running the Server

### Local Development

- **Build and run the production version**:

  ```sh
  # One-time build
  bun rebuild

  # Run the built server
  bun start:http
  # or
  bun start:stdio
  ```

- **Run checks and tests**:
  ```sh
  bun devcheck # Lints, formats, type-checks, and more
  bun test # Runs the test suite
  ```

### Cloudflare Workers

1.  **Build the Worker bundle**:

```sh
bun build:worker
```

2.  **Run locally with Wrangler**:

```sh
bun deploy:dev
```

3.  **Deploy to Cloudflare**:
    ```sh
    bun deploy:prod
    ```

## 📂 Project Structure

| Directory                   | Purpose & Contents                                                               |
| :-------------------------- | :------------------------------------------------------------------------------- |
| `src/mcp-server/tools`      | Your tool definitions (`*.tool.ts`). This is where you add new capabilities.     |
| `src/mcp-server/resources`  | Your resource definitions (`*.resource.ts`). This is where you add data sources. |
| `src/mcp-server/transports` | Implementations for HTTP and STDIO transports, including auth middleware.        |
| `src/storage`               | `StorageService` abstraction and all storage provider implementations.           |
| `src/services`              | Integrations with external services (ClinicalTrials.gov, LLMs, Speech).          |
| `src/container`             | Dependency injection container registrations and tokens.                         |
| `src/utils`                 | Core utilities for logging, error handling, performance, and security.           |
| `src/config`                | Environment variable parsing and validation with Zod.                            |
| `tests/`                    | Unit and integration tests, mirroring the `src/` directory structure.            |

## 🧑‍💻 Agent Development Guide

For strict rules when using this server with an AI agent, refer to the **`.clinerules`** file in this repository. Key principles include:

- **Logic Throws, Handlers Catch**: Never use `try/catch` in your tool `logic`. Throw an `McpError` instead.
- **Pass the Context**: Always pass the `RequestContext` object through your call stack for logging and tracing.
- **Use the Barrel Exports**: Register new tools and resources only in the `index.ts` barrel files within their respective `definitions` directories.

## 🤝 Contributing

Issues and pull requests are welcome! If you plan to contribute, please run the local checks and tests before submitting your PR.

```sh
bun run devcheck
bun test
```

## 📜 License

This project is licensed under the Apache 2.0 License. See the [LICENSE](./LICENSE) file for details.
