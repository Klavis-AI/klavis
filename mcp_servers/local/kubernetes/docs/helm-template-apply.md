### Helm Template Apply Tool

The `helm_template_apply` tool provides an alternative way to install Helm charts that bypasses authentication issues commonly encountered with certain Kubernetes configurations. This tool is particularly useful when you encounter errors like:

```
WARNING: Kubernetes configuration file is group-readable. This is insecure.
Error: INSTALLATION FAILED: Kubernetes cluster unreachable: exec plugin: invalid apiVersion "client.authentication.k8s.io/v1alpha1"
```

Instead of using `helm install` directly, this tool:

1. Uses `helm template` to generate YAML manifests from the Helm chart
2. Applies the generated YAML using `kubectl apply`
3. Handles namespace creation and cleanup automatically

#### Usage Example

```json
{
  "name": "helm_template_apply",
  "arguments": {
    "name": "events-exporter",
    "chart": ".",
    "namespace": "kube-event-exporter",
    "valuesFile": "values.yaml",
    "createNamespace": true
  }
}
```

This is equivalent to running:

```bash
helm template events-exporter . -f values.yaml > events-exporter.yaml
kubectl create namespace kube-event-exporter
kubectl apply -f events-exporter.yaml -n kube-event-exporter
```

#### Parameters

- `name`: Release name for the Helm chart
- `chart`: Chart name or path to chart directory
- `repo`: Chart repository URL (optional if using local chart path)
- `namespace`: Kubernetes namespace to deploy to
- `values`: Chart values as an object (optional)
- `valuesFile`: Path to values.yaml file (optional, alternative to values object)
- `createNamespace`: Whether to create the namespace if it doesn't exist (default: true)
