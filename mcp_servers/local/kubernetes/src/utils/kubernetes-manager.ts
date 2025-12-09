import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import * as k8s from "@kubernetes/client-node";

import { ResourceTracker, PortForwardTracker, WatchTracker } from "../types.js";

export class KubernetesManager {
  private resources: ResourceTracker[] = [];
  private portForwards: PortForwardTracker[] = [];
  private watches: WatchTracker[] = [];
  private kc: k8s.KubeConfig;
  private k8sApi: k8s.CoreV1Api;
  private k8sAppsApi: k8s.AppsV1Api;
  private k8sBatchApi: k8s.BatchV1Api;

  constructor() {
    this.kc = new k8s.KubeConfig();

    if (this.hasEnvKubeconfigYaml()) {
      // Priority 1: Full kubeconfig as YAML string
      try {
        this.loadEnvKubeconfigYaml();
        this.createTempKubeconfigFromYaml(process.env.KUBECONFIG_YAML!);
      } catch (error) {
        throw new Error(
          `Failed to parse KUBECONFIG_YAML: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      }
    } else if (this.isRunningInCluster()) {
      // Priority 2: Check if running in cluster
      this.kc.loadFromCluster();
    } else if (this.hasEnvKubeconfigJson()) {
      // Priority 3: Full kubeconfig as JSON string
      try {
        this.loadEnvKubeconfigJson();
        // Create temp kubeconfig file for kubectl commands from JSON
        const yamlConfig = this.kc.exportConfig();
        this.createTempKubeconfigFromYaml(yamlConfig);
      } catch (error) {
        throw new Error(
          `Failed to parse KUBECONFIG_JSON: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      }
    } else if (this.hasEnvMinimalKubeconfig()) {
      // Priority 4: Minimal config with individual environment variables
      try {
        this.loadEnvMinimalKubeconfig();
        // Create temp kubeconfig file for kubectl commands from minimal config
        const yamlConfig = this.kc.exportConfig();
        this.createTempKubeconfigFromYaml(yamlConfig);
      } catch (error) {
        throw new Error(
          `Failed to create kubeconfig from K8S_SERVER and K8S_TOKEN: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      }
    } else if (this.hasEnvKubeconfigPath()) {
      // Priority 5: Custom kubeconfig file path using KUBECONFIG_PATH
      try {
        this.loadEnvKubeconfigPath();
        // Set KUBECONFIG environment variable to the custom path for kubectl commands
        process.env.KUBECONFIG = process.env.KUBECONFIG_PATH;
      } catch (error) {
        throw new Error(
          `Failed to load kubeconfig from KUBECONFIG_PATH: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      }
    } else if (this.hasEnvKubeconfig()) {
      // Load from KUBECONFIG
      this.kc.loadFromFile(process.env.KUBECONFIG!);
    } else {
      // Priority 7: Default file-based configuration (existing fallback)
      this.kc.loadFromDefault();
    }

    // Apply context override if specified
    if (process.env.K8S_CONTEXT) {
      try {
        this.setCurrentContext(process.env.K8S_CONTEXT);
      } catch (error) {
        console.warn(
          `Warning: Could not set context to ${process.env.K8S_CONTEXT}: ${
            error instanceof Error ? error.message : "Unknown error"
          }`
        );
      }
    }

    // Initialize API clients
    this.k8sApi = this.kc.makeApiClient(k8s.CoreV1Api);
    this.k8sAppsApi = this.kc.makeApiClient(k8s.AppsV1Api);
    this.k8sBatchApi = this.kc.makeApiClient(k8s.BatchV1Api);
  }

  /**
   * A very simple test to check if the application is running inside a Kubernetes cluster
   */
  private isRunningInCluster(): boolean {
    const serviceAccountPath =
      "/var/run/secrets/kubernetes.io/serviceaccount/token";
    try {
      return fs.existsSync(serviceAccountPath);
    } catch {
      return false;
    }
  }

  /**
   * Check if KUBECONFIG_YAML environment variable is available
   */
  private hasEnvKubeconfigYaml(): boolean {
    return !!(
      process.env.KUBECONFIG_YAML && process.env.KUBECONFIG_YAML.trim()
    );
  }

  /**
   * Check if KUBECONFIG_JSON environment variable is available
   */
  private hasEnvKubeconfigJson(): boolean {
    return !!(
      process.env.KUBECONFIG_JSON && process.env.KUBECONFIG_JSON.trim()
    );
  }

  /**
   * Check if minimal K8S_SERVER and K8S_TOKEN environment variables are available
   */
  private hasEnvMinimalKubeconfig(): boolean {
    return !!(
      process.env.K8S_SERVER &&
      process.env.K8S_SERVER.trim() &&
      process.env.K8S_TOKEN &&
      process.env.K8S_TOKEN.trim()
    );
  }

  /**
   * Load kubeconfig from KUBECONFIG_PATH environment variable (file path)
   */
  private loadEnvKubeconfigPath(): void {
    this.kc.loadFromFile(process.env.KUBECONFIG_PATH!);
  }

  /**
   * Load kubeconfig from KUBECONFIG_YAML environment variable (YAML format)
   */
  private loadEnvKubeconfigYaml(): void {
    if (!process.env.KUBECONFIG_YAML) {
      throw new Error("KUBECONFIG_YAML environment variable is not set");
    }

    // Load the config into the JavaScript client
    this.kc.loadFromString(process.env.KUBECONFIG_YAML);
  }

  /**
   * Load kubeconfig from KUBECONFIG_JSON environment variable (JSON format)
   */
  private loadEnvKubeconfigJson(): void {
    const configObj = JSON.parse(process.env.KUBECONFIG_JSON!);
    this.kc.loadFromOptions(configObj);
  }

  /**
   * Load kubeconfig from minimal K8S_SERVER and K8S_TOKEN environment variables
   */
  private loadEnvMinimalKubeconfig(): void {
    if (!process.env.K8S_SERVER || !process.env.K8S_TOKEN) {
      throw new Error(
        "K8S_SERVER and K8S_TOKEN environment variables are required"
      );
    }

    const cluster = {
      name: "env-cluster",
      server: process.env.K8S_SERVER,
      skipTLSVerify: process.env.K8S_SKIP_TLS_VERIFY === "true",
    };

    const user = {
      name: "env-user",
      token: process.env.K8S_TOKEN,
    };

    const context = {
      name: "env-context",
      user: user.name,
      cluster: cluster.name,
    };

    const kubeconfigContent = {
      clusters: [cluster],
      users: [user],
      contexts: [context],
      currentContext: context.name,
    };

    this.kc.loadFromOptions(kubeconfigContent);
  }

  /**
   * Check if KUBECONFIG_PATH environment variable is available
   */
  private hasEnvKubeconfigPath(): boolean {
    return !!(
      process.env.KUBECONFIG_PATH && process.env.KUBECONFIG_PATH.trim()
    );
  }

  private hasEnvKubeconfig(): boolean {
    return !!(process.env.KUBECONFIG && process.env.KUBECONFIG.trim());
  }

  /**
   * Set the current context to the desired context name.
   *
   * @param contextName
   */
  public setCurrentContext(contextName: string) {
    // Get all available contexts
    const contexts = this.kc.getContexts();
    const contextNames = contexts.map((context) => context.name);

    // Check if the requested context exists
    if (!contextNames.includes(contextName)) {
      throw new Error(
        `Context '${contextName}' not found. Available contexts: ${contextNames.join(
          ", "
        )}`
      );
    }
    // Set the current context
    this.kc.setCurrentContext(contextName);
    this.k8sApi = this.kc.makeApiClient(k8s.CoreV1Api);
    this.k8sAppsApi = this.kc.makeApiClient(k8s.AppsV1Api);
    this.k8sBatchApi = this.kc.makeApiClient(k8s.BatchV1Api);
  }

  async cleanup() {
    // Stop watches
    for (const watch of this.watches) {
      watch.abort.abort();
    }

    // Delete tracked resources in reverse order
    for (const resource of [...this.resources].reverse()) {
      try {
        await this.deleteResource(
          resource.kind,
          resource.name,
          resource.namespace
        );
      } catch (error) {
        process.stderr.write(
          `Failed to delete ${resource.kind} ${resource.name}: ${error}\n`
        );
      }
    }
  }

  trackResource(kind: string, name: string, namespace: string) {
    this.resources.push({ kind, name, namespace, createdAt: new Date() });
  }

  async deleteResource(kind: string, name: string, namespace: string) {
    switch (kind.toLowerCase()) {
      case "pod":
        await this.k8sApi.deleteNamespacedPod({ name, namespace });
        break;
      case "deployment":
        await this.k8sAppsApi.deleteNamespacedDeployment({ name, namespace });
        break;
      case "service":
        await this.k8sApi.deleteNamespacedService({ name, namespace });
        break;
      case "cronjob":
        await this.k8sBatchApi.deleteNamespacedCronJob({ name, namespace });
        break;
    }
    this.resources = this.resources.filter(
      (r) => !(r.kind === kind && r.name === name && r.namespace === namespace)
    );
  }

  trackPortForward(pf: PortForwardTracker) {
    this.portForwards.push(pf);
  }

  getPortForward(id: string) {
    return this.portForwards.find((p) => p.id === id);
  }

  removePortForward(id: string) {
    this.portForwards = this.portForwards.filter((p) => p.id !== id);
  }

  trackWatch(watch: WatchTracker) {
    this.watches.push(watch);
  }

  getKubeConfig() {
    return this.kc;
  }

  getCoreApi() {
    return this.k8sApi;
  }

  getAppsApi() {
    return this.k8sAppsApi;
  }

  getBatchApi() {
    return this.k8sBatchApi;
  }

  /**
   * Get the default namespace for operations
   * Uses K8S_NAMESPACE environment variable if set, otherwise defaults to "default"
   */
  getDefaultNamespace(): string {
    return process.env.K8S_NAMESPACE || "default";
  }

  /**
   * Create temporary kubeconfig file from YAML content for kubectl commands
   * @param kubeconfigYaml YAML content of the kubeconfig
   */
  private createTempKubeconfigFromYaml(kubeconfigYaml: string): void {
    try {
      if (!kubeconfigYaml || typeof kubeconfigYaml !== "string") {
        throw new Error(`Invalid kubeconfigYaml: ${typeof kubeconfigYaml}`);
      }

      const tempDir = os.tmpdir();
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const randomString = Math.random().toString(36).substring(2);
      const tempKubeconfigPath = path.join(
        tempDir,
        `kubeconfig-${timestamp}-${randomString}`
      );

      // Write temporary kubeconfig file
      fs.writeFileSync(tempKubeconfigPath, kubeconfigYaml, {
        mode: 0o600,
        encoding: "utf8",
      });

      // Set KUBECONFIG environment variable for kubectl commands
      process.env.KUBECONFIG = tempKubeconfigPath;

      // Function to clean up the temporary file
      const cleanupTempFile = () => {
        try {
          if (fs.existsSync(tempKubeconfigPath)) {
            fs.unlinkSync(tempKubeconfigPath);
          }
        } catch (cleanupError) {
          // Ignore cleanup errors
        }
      };

      // Schedule cleanup of temporary file when process exits
      process.on("exit", cleanupTempFile);

      // Also clean up on SIGINT and SIGTERM (common in Docker containers)
      ["SIGINT", "SIGTERM"].forEach((signal) => {
        process.on(signal, () => {
          cleanupTempFile();
          process.exit(0);
        });
      });

      // Additional cleanup for Docker container lifecycle
      ["SIGUSR1", "SIGUSR2"].forEach((signal) => {
        process.on(signal, cleanupTempFile);
      });
    } catch (error) {
      // Continue without temporary file - kubectl commands may fail but JavaScript client will work
      throw error;
    }
  }
}
