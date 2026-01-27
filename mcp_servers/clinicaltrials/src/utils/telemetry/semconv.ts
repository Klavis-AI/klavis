/**
 * @fileoverview Defines local OpenTelemetry semantic convention constants to ensure
 * stability and avoid dependency conflicts with different versions of
 * `@opentelemetry/semantic-conventions`.
 *
 * This module provides both standard OTEL conventions (aligned with 1.37+) and
 * custom MCP-specific attributes for tool execution and resource monitoring.
 *
 * @module src/utils/telemetry/semconv
 */

// ============================================================================
// Standard OpenTelemetry Semantic Conventions (Stable)
// ============================================================================

/**
 * Service attributes for identifying the application.
 * @see https://opentelemetry.io/docs/specs/semconv/resource/#service
 */
export const ATTR_SERVICE_NAME = 'service.name';
export const ATTR_SERVICE_VERSION = 'service.version';
export const ATTR_SERVICE_INSTANCE_ID = 'service.instance.id';

/**
 * Deployment environment attributes.
 * @see https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/
 */
export const ATTR_DEPLOYMENT_ENVIRONMENT_NAME = 'deployment.environment.name';

/**
 * Cloud provider and platform attributes.
 * @see https://opentelemetry.io/docs/specs/semconv/resource/cloud/
 */
export const ATTR_CLOUD_PROVIDER = 'cloud.provider';
export const ATTR_CLOUD_PLATFORM = 'cloud.platform';
export const ATTR_CLOUD_REGION = 'cloud.region';
export const ATTR_CLOUD_AVAILABILITY_ZONE = 'cloud.availability_zone';
export const ATTR_CLOUD_ACCOUNT_ID = 'cloud.account.id';

/**
 * HTTP request and response attributes.
 * @see https://opentelemetry.io/docs/specs/semconv/http/
 */
export const ATTR_HTTP_REQUEST_METHOD = 'http.request.method';
export const ATTR_HTTP_RESPONSE_STATUS_CODE = 'http.response.status_code';
export const ATTR_HTTP_ROUTE = 'http.route';
export const ATTR_HTTP_REQUEST_BODY_SIZE = 'http.request.body.size';
export const ATTR_HTTP_RESPONSE_BODY_SIZE = 'http.response.body.size';
export const ATTR_URL_FULL = 'url.full';
export const ATTR_URL_PATH = 'url.path';
export const ATTR_URL_QUERY = 'url.query';
export const ATTR_URL_SCHEME = 'url.scheme';

/**
 * Error and exception attributes.
 * @see https://opentelemetry.io/docs/specs/semconv/exceptions/
 */
export const ATTR_ERROR_TYPE = 'error.type';
export const ATTR_EXCEPTION_TYPE = 'exception.type';
export const ATTR_EXCEPTION_MESSAGE = 'exception.message';
export const ATTR_EXCEPTION_STACKTRACE = 'exception.stacktrace';

/**
 * Code execution attributes (for custom spans).
 * @see https://opentelemetry.io/docs/specs/semconv/general/attributes/
 */
export const ATTR_CODE_FUNCTION = 'code.function';
export const ATTR_CODE_NAMESPACE = 'code.namespace';
export const ATTR_CODE_FILEPATH = 'code.filepath';
export const ATTR_CODE_LINENO = 'code.lineno';

/**
 * Network attributes.
 * @see https://opentelemetry.io/docs/specs/semconv/general/attributes/
 */
export const ATTR_NETWORK_PEER_ADDRESS = 'network.peer.address';
export const ATTR_NETWORK_PEER_PORT = 'network.peer.port';
export const ATTR_NETWORK_PROTOCOL_NAME = 'network.protocol.name';
export const ATTR_NETWORK_PROTOCOL_VERSION = 'network.protocol.version';

/**
 * User agent attributes.
 */
export const ATTR_USER_AGENT_ORIGINAL = 'user_agent.original';

// ============================================================================
// Custom MCP Tool Execution Attributes
// ============================================================================

/**
 * MCP tool execution metrics and performance attributes.
 * These are custom attributes specific to MCP tool invocations.
 */
export const ATTR_MCP_TOOL_NAME = 'mcp.tool.name';
export const ATTR_MCP_TOOL_INPUT_BYTES = 'mcp.tool.input_bytes';
export const ATTR_MCP_TOOL_OUTPUT_BYTES = 'mcp.tool.output_bytes';
export const ATTR_MCP_TOOL_DURATION_MS = 'mcp.tool.duration_ms';
export const ATTR_MCP_TOOL_SUCCESS = 'mcp.tool.success';
export const ATTR_MCP_TOOL_ERROR_CODE = 'mcp.tool.error_code';

/**
 * MCP tool memory usage tracking (RSS - Resident Set Size).
 */
export const ATTR_MCP_TOOL_MEMORY_RSS_BEFORE =
  'mcp.tool.memory_rss_bytes.before';
export const ATTR_MCP_TOOL_MEMORY_RSS_AFTER = 'mcp.tool.memory_rss_bytes.after';
export const ATTR_MCP_TOOL_MEMORY_RSS_DELTA = 'mcp.tool.memory_rss_bytes.delta';

/**
 * MCP tool memory usage tracking (Heap Used).
 */
export const ATTR_MCP_TOOL_MEMORY_HEAP_USED_BEFORE =
  'mcp.tool.memory_heap_used_bytes.before';
export const ATTR_MCP_TOOL_MEMORY_HEAP_USED_AFTER =
  'mcp.tool.memory_heap_used_bytes.after';
export const ATTR_MCP_TOOL_MEMORY_HEAP_USED_DELTA =
  'mcp.tool.memory_heap_used_bytes.delta';

// ============================================================================
// Custom MCP Resource Attributes
// ============================================================================

/**
 * MCP resource execution attributes.
 */
export const ATTR_MCP_RESOURCE_URI = 'mcp.resource.uri';
export const ATTR_MCP_RESOURCE_MIME_TYPE = 'mcp.resource.mime_type';
export const ATTR_MCP_RESOURCE_SIZE_BYTES = 'mcp.resource.size_bytes';

// ============================================================================
// Custom MCP Request Context Attributes
// ============================================================================

/**
 * MCP request and operation context attributes.
 */
export const ATTR_MCP_REQUEST_ID = 'mcp.request.id';
export const ATTR_MCP_OPERATION_NAME = 'mcp.operation.name';
export const ATTR_MCP_TENANT_ID = 'mcp.tenant.id';
export const ATTR_MCP_CLIENT_ID = 'mcp.client.id';
export const ATTR_MCP_SESSION_ID = 'mcp.session.id';
