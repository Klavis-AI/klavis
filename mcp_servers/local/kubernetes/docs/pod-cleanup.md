### Pod Cleanup with Existing Tools

Pod cleanup can be achieved using the existing `kubectl_get` and `kubectl_delete` tools with field selectors. This approach leverages standard Kubernetes functionality without requiring dedicated cleanup tools.

#### Identifying Problematic Pods

Use `kubectl_get` with field selectors to identify pods in problematic states:

**Get failed pods:**

```json
{
  "name": "kubectl_get",
  "arguments": {
    "resourceType": "pods",
    "namespace": "default",
    "fieldSelector": "status.phase=Failed"
  }
}
```

**Get completed pods:**

```json
{
  "name": "kubectl_get",
  "arguments": {
    "resourceType": "pods",
    "namespace": "default",
    "fieldSelector": "status.phase=Succeeded"
  }
}
```

**Get pods with specific conditions:**

```json
{
  "name": "kubectl_get",
  "arguments": {
    "resourceType": "pods",
    "namespace": "default",
    "fieldSelector": "status.conditions[?(@.type=='Ready')].status=False"
  }
}
```

#### Deleting Problematic Pods

Use `kubectl_delete` with field selectors to delete pods in problematic states:

**Delete failed pods:**

```json
{
  "name": "kubectl_delete",
  "arguments": {
    "resourceType": "pods",
    "namespace": "default",
    "fieldSelector": "status.phase=Failed",
    "force": true,
    "gracePeriodSeconds": 0
  }
}
```

**Delete completed pods:**

```json
{
  "name": "kubectl_delete",
  "arguments": {
    "resourceType": "pods",
    "namespace": "default",
    "fieldSelector": "status.phase=Succeeded",
    "force": true,
    "gracePeriodSeconds": 0
  }
}
```

#### Workflow

1. **First, identify problematic pods** using `kubectl_get` with appropriate field selectors
2. **Review the list** of pods in the response
3. **Delete the pods** using `kubectl_delete` with the same field selectors

#### Available Field Selectors

- `status.phase=Failed` - Pods that have failed
- `status.phase=Succeeded` - Pods that have completed successfully
- `status.phase=Pending` - Pods that are pending
- `status.conditions[?(@.type=='Ready')].status=False` - Pods that are not ready

#### Safety Features

- **Field selectors**: Target specific pod states precisely
- **Force deletion**: Use `force=true` and `gracePeriodSeconds=0` for immediate deletion
- **Namespace isolation**: Target specific namespaces or use `allNamespaces=true`
- **Standard kubectl**: Uses well-established Kubernetes patterns
