# Helm Install Tool

The `install_helm_chart` tool provides flexible Helm chart installation capabilities with support for both standard Helm install and template-based installation.

## Features

- **Standard Helm Install**: Uses `helm install` command for normal installations
- **Template Mode**: Uses `helm template + kubectl apply` to bypass authentication issues and kubeconfig API version mismatches
- **Flexible Values**: Support for both inline values and external values files
- **Namespace Management**: Optional automatic namespace creation

## Parameters

### Required Parameters
- `name`: Release name for the Helm chart
- `chart`: Chart name or path to chart directory
- `namespace`: Kubernetes namespace for the installation

### Optional Parameters
- `repo`: Chart repository URL (optional if using local chart path)
- `values`: Chart values as an object
- `valuesFile`: Path to values.yaml file (alternative to values object)
- `createNamespace`: Whether to create the namespace if it doesn't exist (default: true)
- `useTemplate`: Use helm template + kubectl apply instead of helm install (default: false)

## Usage Examples

### Standard Installation
```json
{
  "name": "my-release",
  "chart": "stable/nginx-ingress",
  "repo": "https://kubernetes-charts.storage.googleapis.com",
  "namespace": "ingress-nginx",
  "values": {
    "replicaCount": 2,
    "service": {
      "type": "LoadBalancer"
    }
  }
}
```

### Template Mode Installation
```json
{
  "name": "my-release",
  "chart": "./local-chart",
  "namespace": "my-namespace",
  "useTemplate": true,
  "valuesFile": "/path/to/values.yaml",
  "createNamespace": false
}
```

### Local Chart with Template Mode
```json
{
  "name": "my-app",
  "chart": "./charts/my-application",
  "namespace": "production",
  "useTemplate": true,
  "values": {
    "environment": "production",
    "replicas": 3
  }
}
```

## When to Use Template Mode

Use template mode (`useTemplate: true`) when you encounter:
- Authentication issues with Helm
- Kubeconfig API version mismatches
- Problems with Helm's direct cluster access
- Need for more control over the installation process

## Template Mode Process

When `useTemplate` is enabled, the tool:

1. Adds the Helm repository (if provided)
2. Creates the namespace (if `createNamespace` is true)
3. Generates YAML using `helm template`
4. Applies the generated YAML using `kubectl apply`
5. Cleans up temporary files

This approach bypasses Helm's direct cluster communication and uses kubectl instead. 