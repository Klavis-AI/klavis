# Node Management Tool

The `node_management` tool provides comprehensive node operations for Kubernetes cluster management, including cordoning, draining, and uncordoning nodes.

## Features

- **Node Cordon**: Mark nodes as unschedulable to prevent new pods
- **Node Drain**: Safely evict pods from nodes before maintenance
- **Node Uncordon**: Re-enable scheduling on previously cordoned nodes
- **Node Listing**: List all nodes with their current status
- **Safety Controls**: Multiple safety options for destructive operations

## Parameters

### Required Parameters
- `operation`: The operation to perform (`cordon`, `drain`, `uncordon`, `list`)

### Optional Parameters
- `nodeName`: Specific node name to target (required for cordon/drain/uncordon)
- `force`: Force the operation even if there are warnings (default: false)
- `gracePeriod`: Grace period for pod termination in seconds (default: 30)
- `deleteLocalData`: Delete local data when draining (default: false)
- `ignoreDaemonsets`: Ignore DaemonSet pods when draining (default: false)
- `timeout`: Timeout for the drain operation (default: "0" - no timeout)
- `dryRun`: Preview the operation without executing (default: false)
- `confirmDrain`: Explicit confirmation for drain operations (default: false)

## Operations

### List Nodes
Lists all nodes in the cluster with their status.

```json
{
  "operation": "list"
}
```

### Cordon Node
Marks a node as unschedulable to prevent new pods from being scheduled.

```json
{
  "operation": "cordon",
  "nodeName": "worker-node-1",
  "dryRun": false
}
```

### Drain Node
Safely evicts all pods from a node, making it ready for maintenance.

```json
{
  "operation": "drain",
  "nodeName": "worker-node-1",
  "force": true,
  "gracePeriod": 60,
  "deleteLocalData": false,
  "ignoreDaemonsets": true,
  "timeout": "300s",
  "confirmDrain": true
}
```

### Uncordon Node
Re-enables scheduling on a previously cordoned node.

```json
{
  "operation": "uncordon",
  "nodeName": "worker-node-1"
}
```

## Usage Examples

### Preview Drain Operation
```json
{
  "operation": "drain",
  "nodeName": "worker-node-1",
  "dryRun": true,
  "gracePeriod": 30,
  "ignoreDaemonsets": true
}
```

### Force Drain with Extended Grace Period
```json
{
  "operation": "drain",
  "nodeName": "worker-node-1",
  "force": true,
  "gracePeriod": 120,
  "deleteLocalData": true,
  "ignoreDaemonsets": true,
  "timeout": "600s",
  "confirmDrain": true
}
```

### Cordon Multiple Nodes
```json
{
  "operation": "cordon",
  "nodeName": "worker-node-1"
}
```

## Safety Features

1. **Dry Run Mode**: Preview operations without executing them
2. **Confirmation Required**: Drain operations require explicit confirmation
3. **Graceful Termination**: Configurable grace period for pod termination
4. **DaemonSet Protection**: Option to ignore DaemonSet pods during drain
5. **Timeout Protection**: Configurable timeout to prevent hanging operations

## Best Practices

1. **Always Preview**: Use `dryRun: true` before executing drain operations
2. **Check Node Status**: Use `operation: "list"` to verify node states
3. **Plan Maintenance**: Cordon nodes before maintenance, drain before shutdown
4. **Monitor Pods**: Ensure critical pods are rescheduled before draining
5. **Use Appropriate Timeouts**: Set reasonable timeouts for drain operations

## Node States

- **Ready**: Node is healthy and accepting pods
- **NotReady**: Node is not healthy
- **SchedulingDisabled**: Node is cordoned (not accepting new pods)
- **Unknown**: Node status is unknown

## Output Format

The tool returns detailed information about:
- Current node status
- Pods that would be/were evicted
- Any warnings or errors encountered
- Confirmation of completed operations 