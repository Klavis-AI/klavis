# MCP Server Kubernetes - Helm Installation Guide

Complete guide for installing and configuring the MCP Server Kubernetes using Helm.

## Quick Start

```bash
# Basic installation with default settings
helm install mcp-server ./helm-chart

# Install in specific namespace
helm install mcp-server ./helm-chart -n mcp-system --create-namespace
```

## Installation Examples

### AWS EKS Multi-Cluster

```bash
helm install mcp-server-k8s ./helm-chart \
  --set kubeconfig.provider=aws \
  --set kubeconfig.aws.clusters[0].name=prod-us-east \
  --set kubeconfig.aws.clusters[0].clusterName=prod-cluster \
  --set kubeconfig.aws.clusters[0].region=us-east-1 \
  --set kubeconfig.aws.clusters[0].roleArn="arn:aws:iam::123456789:role/EKSAdminRole" \
  --set kubeconfig.aws.clusters[1].name=staging-us-west \
  --set kubeconfig.aws.clusters[1].clusterName=staging-cluster \
  --set kubeconfig.aws.clusters[1].region=us-west-2 \
  --set kubeconfig.aws.defaultContext=prod-us-east
```

### GCP GKE Multi-Cluster

```bash
helm install mcp-server-k8s ./helm-chart \
  --set kubeconfig.provider=gcp \
  --set kubeconfig.gcp.clusters[0].name=prod-cluster \
  --set kubeconfig.gcp.clusters[0].clusterName=prod-gke \
  --set kubeconfig.gcp.clusters[0].zone=us-central1-a \
  --set kubeconfig.gcp.clusters[0].project=company-prod \
  --set kubeconfig.gcp.clusters[1].name=dev-cluster \
  --set kubeconfig.gcp.clusters[1].clusterName=dev-gke \
  --set kubeconfig.gcp.clusters[1].zone=us-central1-b \
  --set kubeconfig.gcp.clusters[1].project=company-dev
```

### URL-based Kubeconfig

```bash
helm install mcp-server-k8s ./helm-chart \
  --set kubeconfig.provider=url \
  --set kubeconfig.url.configs[0].name=prod-config \
  --set kubeconfig.url.configs[0].url="https://storage.company.com/prod.yaml" \
  --set kubeconfig.url.configs[1].name=staging-config \
  --set kubeconfig.url.configs[1].url="https://storage.company.com/staging.yaml"
```

### Web-Accessible (HTTP Transport)

```bash
# Basic HTTP transport setup
helm install mcp-server-k8s ./helm-chart \
  --set transport.mode=http \
  --set transport.service.type=LoadBalancer \
  --set transport.ingress.enabled=true \
  --set transport.ingress.hosts[0].host=mcp-server.company.com

# AWS with ALB (recommended for MCP streaming)  
helm install mcp-server-k8s ./helm-chart \
  --set transport.mode=http \
  --set transport.service.type=LoadBalancer \
  --set transport.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-type"="alb" \
  --set transport.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-internal"="true"
  
# NGINX Ingress with streaming support
helm install mcp-server-k8s ./helm-chart \
  --set transport.mode=http \
  --set transport.ingress.enabled=true \
  --set transport.ingress.className="nginx" \
  --set transport.ingress.annotations."nginx\.ingress\.kubernetes\.io/proxy-read-timeout"="3600" \
  --set transport.ingress.annotations."nginx\.ingress\.kubernetes\.io/proxy-buffering"="off"
```

#### ⚠️ MCP Streaming Compatibility Warning

Model Context Protocol uses streaming connections that may not work with all ingress controllers:

**Known Issues:**
- **AWS Classic ELB**: Does not support streaming - use NLB instead
- **NGINX + ELB**: May timeout - configure proxy timeouts  
- **CloudFlare**: May buffer responses - disable buffering
- **API Gateways**: May not support Server-Sent Events properly

**Recommended Solutions:**
- Use Network Load Balancer (NLB) on AWS
- Configure NGINX proxy timeouts and disable buffering
- Test MCP streaming thoroughly with your setup

## Cloud Provider IAM Integration

### AWS IRSA (IAM Roles for Service Accounts)
```bash
helm install mcp-server-k8s ./helm-chart \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"="arn:aws:iam::123456789012:role/mcp-server-role" \
  --set serviceAccount.annotations."eks\.amazonaws\.com/sts-regional-endpoints"="true"
```

### GCP Workload Identity
```bash
helm install mcp-server-k8s ./helm-chart \
  --set serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="mcp-server@my-project.iam.gserviceaccount.com"
```

## Security Configuration

### Non-Destructive Mode (Safe Operations Only)

```bash
helm install mcp-server-k8s ./helm-chart \
  --set security.allowOnlyNonDestructive=true
```

### Network Policy (Default Deny - Security Best Practice)

```bash
# Enable NetworkPolicy with default deny and minimal required access
helm install mcp-server-k8s ./helm-chart \
  --set networkPolicy.enabled=true \
  --set networkPolicy.ingress[0].from[0].namespaceSelector.matchLabels.name=ingress-nginx \
  --set networkPolicy.ingress[0].ports[0].protocol=TCP \
  --set networkPolicy.ingress[0].ports[0].port=3001 \
  --set networkPolicy.egress[0].to[0].namespaceSelector.matchLabels.name=kube-system \
  --set networkPolicy.egress[0].ports[0].protocol=UDP \
  --set networkPolicy.egress[0].ports[0].port=53

# ⚠️  WARNING: NetworkPolicy uses default deny - you MUST define egress rules 
# for DNS, Kubernetes API, and cloud provider APIs or the pod won't function!
```

### Horizontal Pod Autoscaler (Auto-scaling)

```bash
# Enable HPA with CPU and memory scaling
helm install mcp-server-k8s ./helm-chart \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=20 \
  --set autoscaling.targetCPUUtilizationPercentage=70 \
  --set autoscaling.targetMemoryUtilizationPercentage=80
```

## Advanced Configuration

### Custom Environment Variables

```yaml
kubeconfig:
  env:
    AWS_PROFILE: "production"
    GOOGLE_APPLICATION_CREDENTIALS: "/var/secrets/gcp-key.json"
    CUSTOM_TOKEN: "my-auth-token"
```

### Extra Arguments for Cloud Providers

```yaml
kubeconfig:
  aws:
    clusters:
      - name: "prod"
        clusterName: "prod-cluster"
        region: "us-east-1"
        extraArgs:
          - "--profile=production"
          - "--external-id=unique-id"
          - "--session-name=mcp-session"
```

### Custom RBAC

```yaml
rbac:
  rules:
    - apiGroups: [""]
      resources: ["pods", "services"]
      verbs: ["get", "list"]
    - apiGroups: ["apps"]
      resources: ["deployments"]
      verbs: ["get", "list", "patch"]
```

### Network Policy (Default Deny)

```yaml
# ⚠️  NetworkPolicy implements DEFAULT DENY for security best practices
# You MUST explicitly allow all required traffic or the pod will not function!

networkPolicy:
  enabled: true
  
  # Ingress rules - explicitly allow inbound traffic
  ingress:
    # Allow ingress controller access
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
          podSelector:
            matchLabels:
              app.kubernetes.io/name: ingress-nginx
      ports:
        - protocol: TCP
          port: 3001
    
    # Allow specific CIDR blocks
    - from:
        - ipBlock:
            cidr: 10.0.0.0/8
            except:
              - 10.0.1.0/24
      ports:
        - protocol: TCP
          port: 3001
  
  # Egress rules - explicitly allow outbound traffic (REQUIRED)
  egress:
    # REQUIRED: Allow DNS resolution
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    
    # REQUIRED: Allow Kubernetes API access
    - to:
        - ipBlock:
            cidr: 10.96.0.0/12  # Service CIDR (adjust for your cluster)
      ports:
        - protocol: TCP
          port: 443
    
    # REQUIRED for cloud providers: Allow cloud provider API access
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0  # Restrict this CIDR for better security
      ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 80  # For metadata services
```

### Horizontal Pod Autoscaler

```yaml
# Enable HPA with advanced scaling configuration
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 50
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
  
  # Custom metrics scaling
  customMetrics:
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
  
  # Scaling behavior
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

## Values Validation

The chart includes a JSON Schema (`values.schema.json`) that validates your configuration. Most Helm clients will automatically validate values against this schema.

To manually validate your values file:
```bash
# Using helm plugin (if available)
helm plugin install https://github.com/losisin/helm-values-schema-json
helm schema validate ./helm-chart/values.yaml ./helm-chart/values.schema.json

# Using online JSON Schema validators
# Copy your values and the schema to https://www.jsonschemavalidator.net/
```

## Configuration Values

### Core Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `image.repository` | string | `"flux159/mcp-server-kubernetes"` | Container image repository |
| `image.tag` | string | `"latest"` | Image tag |
| `transport.mode` | string | `"http"` | Transport mode: stdio, sse, http |
| `transport.service.type` | string | `"ClusterIP"` | Service type for http/sse modes |
| `kubeconfig.provider` | string | `"serviceaccount"` | Kubeconfig provider type |

### Security Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `security.allowOnlyNonDestructive` | bool | `false` | Disable destructive operations (kubectl_delete, uninstall_helm_chart, cleanup, kubectl_generic) |
| `security.allowOnlyReadonly` | bool | `false` | Enable read-only mode (kubectl_get, kubectl_describe, kubectl_logs, kubectl_context, explain_resource, list_api_resources, ping) |
| `security.allowedTools` | string | `""` | Comma-separated list of specific tools to allow |

### Scaling and Resources

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `autoscaling.enabled` | bool | `false` | Enable HorizontalPodAutoscaler |
| `autoscaling.minReplicas` | int | `1` | Minimum number of replicas |
| `autoscaling.maxReplicas` | int | `10` | Maximum number of replicas |
| `networkPolicy.enabled` | bool | `false` | Enable NetworkPolicy |
| `resources.limits.memory` | string | `"512Mi"` | Memory limit |
| `resources.limits.cpu` | string | `"500m"` | CPU limit |

### Common Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `commonLabels` | object | `{}` | Common labels for all resources |
| `commonAnnotations` | object | `{}` | Common annotations for all resources |
| `rbac.create` | bool | `true` | Create RBAC resources |
| `serviceAccount.create` | bool | `true` | Create service account |

## Installation from Examples

Use the provided example files for common deployment scenarios:

```bash
# AWS Multi-cluster with role assumption
helm install mcp-server ./helm-chart -f examples/aws-multi-cluster.yaml

# AWS IRSA integration
helm install mcp-server ./helm-chart -f examples/aws-irsa-example.yaml

# GCP Workload Identity  
helm install mcp-server ./helm-chart -f examples/gcp-workload-identity.yaml

# Azure Workload Identity
helm install mcp-server ./helm-chart -f examples/azure-workload-identity.yaml

# Secure NetworkPolicy with default deny
helm install mcp-server ./helm-chart -f examples/secure-networkpolicy.yaml

# Complete production configuration
helm install mcp-server ./helm-chart -f examples/production-complete.yaml
```

## Testing

After installation, validate the deployment using Helm tests:

```bash
# Run all tests
helm test mcp-server

# Run tests with detailed output
helm test mcp-server --logs

# Run specific test
helm test mcp-server --filter name=mcp-server-test-connectivity
```

### Available Tests

The chart includes several test pods to validate functionality:

1. **Kubeconfig Test** (`test-kubeconfig`) - Weight: 5
   - Validates kubeconfig fetching from cloud providers
   - Tests kubectl connectivity to target clusters
   - Verifies API server access and authentication

2. **Connectivity Test** (`test-connectivity`) - Weight: 10
   - Tests HTTP/SSE transport connectivity (if enabled)
   - Validates service discovery and network access
   - Basic health check validation

3. **MCP Tools Test** (`test-mcp-tools`) - Weight: 20
   - Tests MCP protocol functionality
   - Validates available tools and security filtering
   - Confirms tool restrictions (readonly/non-destructive modes)

### Test Examples

```bash
# Test basic installation
helm install mcp-server ./helm-chart
helm test mcp-server

# Test AWS multi-cluster setup
helm install mcp-server ./helm-chart -f examples/aws-multi-cluster.yaml
helm test mcp-server --logs

# Test with security restrictions
helm install mcp-server ./helm-chart --set security.allowOnlyReadonly=true
helm test mcp-server --filter name=mcp-server-test-mcp-tools
```

### Test Troubleshooting

If tests fail, check the test pod logs:

```bash
# Get test pod logs
kubectl logs mcp-server-test-connectivity
kubectl logs mcp-server-test-kubeconfig  
kubectl logs mcp-server-test-mcp-tools

# Describe test pods for more details
kubectl describe pod mcp-server-test-connectivity
```

Common test failure causes:
- **Kubeconfig test**: Cloud provider credentials, network access, RBAC permissions
- **Connectivity test**: Service not ready, network policies, ingress configuration
- **MCP tools test**: Server startup time, security filtering configuration

### NetworkPolicy Considerations

When NetworkPolicy is enabled, the chart automatically creates additional NetworkPolicy rules for test pods:

- **Test Pod Communication**: Allows test pods to communicate with the MCP server
- **DNS Access**: Enables DNS resolution for test pods
- **Cloud Provider APIs**: Permits access to cloud provider APIs for kubeconfig tests
- **Kubernetes API**: Allows kubectl connectivity tests

The test NetworkPolicy (`networkpolicy-tests.yaml`) includes:
- Ingress rules allowing test pod → MCP server communication
- Egress rules for DNS, Kubernetes API, and cloud provider access
- Automatic cleanup after test completion

If tests fail with NetworkPolicy enabled, check:
```bash
# Verify NetworkPolicy rules
kubectl get networkpolicy
kubectl describe networkpolicy mcp-server-networkpolicy-tests

# Check test pod network connectivity
kubectl exec mcp-server-test-connectivity -- nslookup kubernetes.default
kubectl exec mcp-server-test-connectivity -- nc -zv mcp-server 3001
```

## Upgrading

```bash
# Upgrade to latest version
helm upgrade mcp-server ./helm-chart

# Upgrade with new values
helm upgrade mcp-server ./helm-chart --set image.tag=2.8.1

# Upgrade from values file
helm upgrade mcp-server ./helm-chart -f my-values.yaml

# Test after upgrade
helm test mcp-server
```

## Uninstalling

```bash
# Run tests before uninstall (optional)
helm test mcp-server

# Uninstall the release
helm uninstall mcp-server
```

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -l app.kubernetes.io/name=mcp-server-kubernetes
```

### View Logs
```bash
kubectl logs -l app.kubernetes.io/name=mcp-server-kubernetes
```

### Test Init Container
```bash
kubectl describe pod -l app.kubernetes.io/name=mcp-server-kubernetes
```

### Common Issues

1. **Init container fails**: Check cloud provider credentials and permissions
2. **RBAC errors**: Verify ServiceAccount has required cluster permissions  
3. **Transport not accessible**: Check service type and ingress configuration
4. **Kubeconfig issues**: Validate provider configuration and network access
5. **NetworkPolicy blocks traffic**: Verify egress rules for DNS, API, and cloud providers