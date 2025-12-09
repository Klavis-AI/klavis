import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { KubernetesManager } from "../types.js";
import { ListPromptsRequestSchema, GetPromptRequestSchema } from "@modelcontextprotocol/sdk/types.js";

export function registerPromptHandlers(server: Server, k8sManager: KubernetesManager) {
  // Register prompts list handler
  server.setRequestHandler(ListPromptsRequestSchema, async () => {
    return {
      prompts: [
        {
          name: "k8s-diagnose",
          description: "Diagnose Kubernetes Resources.",
          arguments: [
            {
              name: "keyword",
              description: "A keyword to search pod/node names.",
              required: true,
            },
            {
              name: "namespace",
              description: "Optional: Specify a namespace to narrow down the search.",
              required: false,
              default: "all"
            },
          ],
        },
      ],
    };
  });

  // Register prompt handler
  server.setRequestHandler(GetPromptRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    if (name === "k8s-diagnose") {
      const keyword = args?.keyword as string;
      const namespace = args?.namespace as string;

      if (!keyword) {
        throw new Error("Keyword parameter is required for k8s-diagnose prompt");
      }

      const actualNamespace = namespace || "all";
      const message = `Diagnose Kubernetes resources (pods, nodes, etc.) containing keyword "${keyword}" in their names within namespace "${actualNamespace}" (or across all namespaces if specified) for this investigation:

**Autonomous Kubernetes Diagnosis Flow**

0. **Perform Quick Health Checks / Golden Signals Analysis**
   - Assess latency, errors, and resource utilization. If a clear issue is identified (e.g., node not ready, network partition), streamline or deprioritize subsequent detailed steps.

1. **Identify Resource Type and Scope**
   - Determine the specific resource type (e.g., Pod, Node, Deployment, Service, Customresourcedefination) by analyzing labels, controller relationships, and initial observations.
   - If needed we can use kubectl_explain tool to get list of resource type
   - Note when you need customresourcedefinitions please use kubectl_explain

2. **Assess Current State**
   - Check resource status (e.g., ready state, desired vs. current replicas for deployments).
   - Identify any non-running or unhealthy states (e.g., CrashLoopBackOff, NotReady, Pending, Evicted).
   - Review placement and distribution patterns across nodes.

3. **Analyze Operational History**
   - Review recent events and warnings related to the resource.
   - Check rollout history and update strategies for controllers (e.g., Deployments).
   - Examine recent configuration changes or applied manifests.

4. **Inspect Runtime Behavior**
   - Collect logs from current and previous instances for errors or anomalies (e.g., container logs for pods, system logs for nodes).
   - Test intra-cluster networking and DNS resolution.
   - Verify storage mounts, secret accessibility, and configuration usage.

5. **Evaluate Dependencies**
   - Validate references to ConfigMaps, Secrets, and other dependent resources.
   - Check associated service account permissions and RBAC rules.
   - Confirm initContainers and sidecar containers have completed successfully or are running as expected.

6. **Audit Resource Constraints**
   - Analyze CPU, memory, and storage usage trends against defined requests and limits.
   - Check node allocatable resources and capacity.
   - Review pod disruption budgets and quotas affecting the resource.

7. **Validate Cluster Context & Environment**
   - Inspect node readiness, taints, and tolerations.
   - Verify the current Kubernetes context and namespace.
   - Confirm API server availability and connectivity.
   - Check Kubernetes version compatibility (if applicable).

8. **Compare Against Patterns**
   - Benchmark against workload-specific best practices and known healthy configurations.
   - Verify liveness, readiness, and startup probe configurations.
   - Audit security context settings and network policies.

---

**Instructions:**
- For each finding, clearly state the observation, its severity (e.g., \`CRITICAL\`, \`WARNING\`, \`INFO\`), and the evidence (e.g., \`kubectl output\`, error message in POD_NAME, timestamp). Also, print which object they found symptoms, e.g., error message in POD_NAME.
- If there are more than 4 relevant resources (e.g., pods, nodes), pick up to 3 resources which are exhibiting the most severe or illustrative symptoms.
- If there's a typo in user input and a closest matching object name exists, consider an auto-correction or suggest the correct name.
- Summarize the root cause clearly and concisely at the end of the investigation, along with clear, actionable steps for remediation, including specific \`kubectl\` commands or configuration changes required.
- If there is a node-level issue, thoroughly analyze it and explicitly post the findings.
- **Keep the output crisp, to the point, professional, direct, and systematic, avoiding verbose descriptions. Focus on actionable insights for engineers.**`;

      return {
        messages: [
          {
            role: "user" as const,
            content: {
              type: "text" as const,
              text: message,
            },
          },
        ],
      };
    }

    throw new Error(`Unknown prompt: ${name}`);
  });
}