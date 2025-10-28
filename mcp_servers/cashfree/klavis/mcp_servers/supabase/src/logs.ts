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
        select id, identifier, timestamp, event_message, request.method, request.path, response.status_code
        from edge_logs
        cross join unnest(metadata) as m
        cross join unnest(m.request) as request
        cross join unnest(m.response) as response
        order by timestamp desc
        limit ${limit}
      `;
    case 'branch-action':
      return stripIndent`
        select workflow_run, workflow_run_logs.timestamp, id, event_message from workflow_run_logs
        order by timestamp desc
        limit ${limit}
      `;
    case 'postgres':
      return stripIndent`
        select identifier, postgres_logs.timestamp, id, event_message, parsed.error_severity from postgres_logs
        cross join unnest(metadata) as m
        cross join unnest(m.parsed) as parsed
        order by timestamp desc
        limit ${limit}
      `;
    case 'edge-function':
      return stripIndent`
        select id, function_edge_logs.timestamp, event_message, response.status_code, request.method, m.function_id, m.execution_time_ms, m.deployment_id, m.version from function_edge_logs
        cross join unnest(metadata) as m
        cross join unnest(m.response) as response
        cross join unnest(m.request) as request
        order by timestamp desc
        limit ${limit}
      `;
    case 'auth':
      return stripIndent`
        select id, auth_logs.timestamp, event_message, metadata.level, metadata.status, metadata.path, metadata.msg as msg, metadata.error from auth_logs
        cross join unnest(metadata) as metadata
        order by timestamp desc
        limit ${limit}
      `;
    case 'storage':
      return stripIndent`
        select id, storage_logs.timestamp, event_message from storage_logs
        order by timestamp desc
        limit ${limit}
      `;
    case 'realtime':
      return stripIndent`
        select id, realtime_logs.timestamp, event_message from realtime_logs
        order by timestamp desc
        limit ${limit}
      `;
    default:
      throw new Error(`unsupported log service type: ${service}`);
  }
}
