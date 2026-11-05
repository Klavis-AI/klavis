import { describe, expect, it } from 'vitest';
import { getLogQuery } from './logs.js';

// Regression coverage for the logs.all -> unified `logs` table migration.
// Every source/field name asserted here is verified against Supabase's
// current log field reference
// (https://supabase.com/docs/guides/observability/log-field-reference).

describe('getLogQuery', () => {
  it('queries the unified logs table with a source filter for every supported service', () => {
    const services = [
      'api',
      'postgres',
      'edge-function',
      'auth',
      'storage',
      'realtime',
    ] as const;

    for (const service of services) {
      const sql = getLogQuery(service);
      expect(sql).toContain('from logs');
      expect(sql).not.toMatch(/cross join unnest/i);
    }
  });

  it('api: selects from edge_logs using request.path (not request.pathname)', () => {
    const sql = getLogQuery('api');
    expect(sql).toContain("where source = 'edge_logs'");
    expect(sql).toContain("log_attributes['request.method']");
    expect(sql).toContain("log_attributes['request.path']");
    expect(sql).not.toContain('request.pathname');
    expect(sql).toContain("log_attributes['response.status_code']");
  });

  it('postgres: selects from postgres_logs and accesses error_severity via log_attributes', () => {
    const sql = getLogQuery('postgres');
    expect(sql).toContain("where source = 'postgres_logs'");
    expect(sql).toContain("log_attributes['parsed.error_severity']");
  });

  it('edge-function: selects from function_edge_logs using request.pathname-scoped fields', () => {
    const sql = getLogQuery('edge-function');
    expect(sql).toContain("where source = 'function_edge_logs'");
    expect(sql).toContain("log_attributes['function_id']");
    expect(sql).toContain("log_attributes['execution_time_ms']");
    expect(sql).toContain("log_attributes['deployment_id']");
    expect(sql).toContain("log_attributes['version']");
  });

  it('auth: selects from auth_logs and never selects a non-existent "error" attribute', () => {
    const sql = getLogQuery('auth');
    expect(sql).toContain("where source = 'auth_logs'");
    expect(sql).toContain("log_attributes['level']");
    expect(sql).toContain("log_attributes['status']");
    expect(sql).toContain("log_attributes['path']");
    expect(sql).toContain("log_attributes['msg']");
    expect(sql).not.toContain("log_attributes['error']");
  });

  it('storage: selects base columns from storage_logs', () => {
    const sql = getLogQuery('storage');
    expect(sql).toContain("where source = 'storage_logs'");
  });

  it('realtime: selects base columns from realtime_logs', () => {
    const sql = getLogQuery('realtime');
    expect(sql).toContain("where source = 'realtime_logs'");
  });

  it('respects the limit parameter', () => {
    const sql = getLogQuery('api', 42);
    expect(sql).toContain('limit 42');
  });

  it('branch-action: throws rather than querying the non-existent workflow_run_logs source', () => {
    // Action Run logs require a dedicated Management API endpoint
    // (GET /v1/projects/{ref}/actions/{run_id}/logs), not the unified
    // logs SQL surface - there is no 'workflow_run_logs' source.
    expect(() => getLogQuery('branch-action')).toThrow(
      'branch-action logs are not queryable via the unified logs SQL endpoint'
    );
  });
});
