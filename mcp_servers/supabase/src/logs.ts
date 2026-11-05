import { stripIndent } from 'common-tags';

export function getLogQuery(
  service:
    | 'api'
    | 'branch-action'
    | 'postgres'
    | 'edge-function'
    | 'auth'
    | 'storage'
    | 'realtime',
  limit: number = 100
) {
  switch (service) {
    case 'api':
      return stripIndent`
        select
          id,
          log_attributes['identifier'] as identifier,
          timestamp,
          event_message,
          log_attributes['request.method'] as method,
          log_attributes['request.path'] as path,
          toInt32OrZero(log_attributes['response.status_code']) as status_code
        from logs
        where source = 'edge_logs'
        order by timestamp desc
        limit ${limit}
      `;
    case 'branch-action':
      // Action Run (branch/CI) logs are NOT part of Supabase's unified
      // `logs` table/ClickHouse SQL surface - there is no `workflow_run_logs`
      // source in the current unified logs model (verified against
      // https://supabase.com/docs/guides/observability/log-field-reference,
      // which enumerates every valid `source` value and none is named
      // "workflow_run_logs"). Action run logs are served by a dedicated
      // Management API endpoint instead:
      // `GET /v1/projects/{ref}/actions/{run_id}/logs` (see
      // https://supabase.com/docs/reference/api/v1-get-action-run-logs),
      // which takes a specific run_id and returns logs directly - it is not
      // a SQL query at all. That endpoint isn't in this package's
      // generated `management-api/types.ts` yet, and wiring it up needs a
      // `run_id` parameter this tool doesn't currently accept, so it's a
      // real feature addition, not something this SQL-query builder can
      // produce. Failing loudly here (instead of silently returning a SQL
      // string that queries a source that doesn't exist and always
      // returns zero rows) is the correct behavior until that's built.
      throw new Error(
        "branch-action logs are not queryable via the unified logs SQL endpoint (no 'workflow_run_logs' source exists). " +
          'They require GET /v1/projects/{ref}/actions/{run_id}/logs, a separate Management API endpoint not yet supported by this tool.'
      );
    case 'postgres':
      return stripIndent`
        select
          log_attributes['identifier'] as identifier,
          timestamp,
          id,
          event_message,
          log_attributes['parsed.error_severity'] as error_severity
        from logs
        where source = 'postgres_logs'
        order by timestamp desc
        limit ${limit}
      `;
    case 'edge-function':
      return stripIndent`
        select
          id,
          timestamp,
          event_message,
          toInt32OrZero(log_attributes['response.status_code']) as status_code,
          log_attributes['request.method'] as method,
          log_attributes['function_id'] as function_id,
          toFloat64OrZero(log_attributes['execution_time_ms']) as execution_time_ms,
          log_attributes['deployment_id'] as deployment_id,
          log_attributes['version'] as version
        from logs
        where source = 'function_edge_logs'
        order by timestamp desc
        limit ${limit}
      `;
    case 'auth':
      return stripIndent`
        select
          id,
          timestamp,
          event_message,
          log_attributes['level'] as level,
          log_attributes['status'] as status,
          log_attributes['path'] as path,
          log_attributes['msg'] as msg
        from logs
        where source = 'auth_logs'
        order by timestamp desc
        limit ${limit}
      `;
    case 'storage':
      return stripIndent`
        select id, timestamp, event_message
        from logs
        where source = 'storage_logs'
        order by timestamp desc
        limit ${limit}
      `;
    case 'realtime':
      return stripIndent`
        select id, timestamp, event_message
        from logs
        where source = 'realtime_logs'
        order by timestamp desc
        limit ${limit}
      `;
    default:
      throw new Error(`unsupported log service type: ${service}`);
  }
}
