# Contributing

Follow the [README.md](README.md) for local development and testing instructions.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

For bigger changes please open an issue first to discuss the proposed changes.

### Project Structure

See this [DeepWiki link](https://deepwiki.com/Flux159/mcp-server-kubernetes) for a more indepth architecture overview created by Devin.

```
├── src/
│   ├── index.ts              # Main server implementation
│   ├── types.ts              # Type re-exports
│   ├── config/               # Configuration files
│   │   ├── container-templates.ts  # Container configurations
│   │   ├── server-config.ts        # Server settings
│   │   ├── deployment-config.ts    # Deployment schemas
│   │   ├── namespace-config.ts     # Namespace schemas
│   │   └── cleanup-config.ts       # Resource cleanup configuration
│   ├── models/               # Data models and schemas
│   │   ├── response-schemas.ts     # API response schemas
│   │   ├── resource-models.ts      # Resource models
│   │   ├── tool-models.ts          # Tool schemas
│   │   ├── helm-models.ts          # Helm operation schemas
│   │   └── kubectl-models.ts       # Kubectl operation schemas
│   ├── utils/                # Utility classes
│   │   └── kubernetes-manager.ts   # K8s management
│   ├── resources/            # Resource handlers
│   │   └── handlers.ts       # Resource implementation
│   └── tools/                # Tool implementations
│       ├── list_pods.ts      # Pod listing operations
│       ├── list_services.ts  # Service listing operations
│       ├── list_deployments.ts # Deployment listing operations
│       ├── list_nodes.ts     # Node listing operations
│       ├── create_pod.ts     # Pod creation operations
│       ├── delete_pod.ts     # Pod deletion operations
│       ├── describe_pod.ts   # Pod description operations
│       ├── get_logs.ts       # Container logs operations
│       ├── get_events.ts     # Kubernetes events operations
│       ├── helm-operations.ts # Helm chart operations
│       └── kubectl-operations.ts # Kubectl utility operations
├── tests/                    # Test files
│   ├── unit.test.ts          # Unit tests for basic operations
│   ├── helm.test.ts          # Helm-specific tests
│   └── kubectl.test.ts       # Kubectl-specific tests
├── .github/                  # GitHub configuration
│   └── workflows/            # CI/CD workflows
│       ├── ci.yml            # Continuous integration
│       └── cd.yml            # Continuous deployment
├── Dockerfile                # Docker container definition
├── LICENSE                   # MIT license
├── README.md                 # Project documentation
├── package.json              # NPM package configuration
├── tsconfig.json             # TypeScript configuration
└── vitest.config.ts          # Test configuration
```
