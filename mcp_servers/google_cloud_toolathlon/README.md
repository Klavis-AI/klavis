# Google Cloud MCP Server

A comprehensive Model Context Protocol (MCP) server for Google Cloud Platform services. This project provides Python wrapper modules and MCP tools for managing various GCP services including BigQuery, Cloud Logging, Cloud Storage, and Compute Engine.

## 🚀 Features

- **BigQuery**: Data warehouse operations including query execution, data loading/exporting, job management, and cost estimation
- **Cloud Logging**: Comprehensive log management with reading/writing logs, bucket management, sinks, exclusions, and metrics
- **Cloud Storage**: Complete bucket and object management with lifecycle policies and batch operations
- **Compute Engine**: Virtual machine lifecycle management and zone operations
- **MCP Integration**: Full MCP server implementation for AI model interactions
- **Flexible Authentication**: Support for both service account files and default credentials

## 📦 Installation

### From uv tool
```bash
uv tool install google-cloud-mcp
```

### From Source
```bash
git clone https://github.com/lockon-n/google-cloud-mcp.git
cd google-cloud-mcp
pip install -e .
```

## 🔧 Setup

### Authentication

#### Option 1: Service Account (Recommended)
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Place it as `service-account-key.json` in your project root

#### Option 2: Default Credentials
```bash
gcloud auth application-default login
```

### Running the MCP Server
```bash
uv run main.py
```

## 🛠️ Available Tools
<details>
<summary>BigQuery Tools</summary>

#### `google-cloud-bigquery_execute_query`
Execute SQL queries with optional cost estimation.
```json
{
  "query": "SELECT * FROM dataset.table LIMIT 10",
  "dry_run": false,
  "max_results": 1000
}
```

#### `google-cloud-bigquery_create_dataset`
Create a new BigQuery dataset.
```json
{
  "dataset_id": "my_dataset",
  "description": "My dataset description",
  "location": "US"
}
```

#### `google-cloud-bigquery_create_table`
Create a new table with schema.
```json
{
  "dataset_id": "my_dataset",
  "table_id": "my_table",
  "schema": [
    {"name": "id", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "name", "type": "STRING", "mode": "NULLABLE"}
  ]
}
```

#### `google-cloud-bigquery_load_data_from_csv`
Load data from CSV file into BigQuery table.
```json
{
  "dataset_id": "my_dataset",
  "table_id": "my_table",
  "csv_file_path": "/path/to/data.csv",
  "write_disposition": "WRITE_APPEND"
}
```

#### `google-cloud-bigquery_export_to_storage`
Export BigQuery table to Cloud Storage.
```json
{
  "dataset_id": "my_dataset",
  "table_id": "my_table",
  "bucket_name": "my-bucket",
  "file_path": "exports/data.csv"
}
```

#### `google-cloud-bigquery_list_datasets`
List all datasets in the project.

#### `google-cloud-bigquery_list_tables`
List all tables in a dataset.
```json
{
  "dataset_id": "my_dataset"
}
```

#### `google-cloud-bigquery_get_job_status`
Get the status of a BigQuery job.
```json
{
  "job_id": "job_12345"
}
```
</details>

<details>
<summary>Cloud Logging Tools</summary>

#### `google-cloud-logging_write_log`
Write log entries (text or structured).
```json
{
  "log_name": "my-application",
  "message": "Application started successfully",
  "severity": "INFO",
  "labels": {"component": "backend"}
}
```

#### `google-cloud-logging_read_logs`
Read and filter log entries.
```json
{
  "filter_string": "severity>=ERROR",
  "max_results": 100,
  "time_range_hours": 24
}
```

#### `google-cloud-logging_list_logs`
List all log names in the project.

#### `google-cloud-logging_delete_log`
Delete all entries in a specific log.
```json
{
  "log_name": "old-application"
}
```

#### `google-cloud-logging_create_log_bucket`
Create a new log bucket for retention management.
```json
{
  "bucket_id": "my-log-bucket",
  "retention_days": 90,
  "description": "Application logs bucket",
  "locked": false
}
```

#### `google-cloud-logging_update_log_bucket`
Update log bucket configuration.
```json
{
  "bucket_id": "my-log-bucket",
  "retention_days": 120,
  "description": "Updated description"
}
```

#### `google-cloud-logging_delete_log_bucket`
Delete a log bucket.
```json
{
  "bucket_id": "my-log-bucket"
}
```

#### `google-cloud-logging_clear_log_bucket`
Clear all logs from a bucket while keeping the bucket.
```json
{
  "bucket_id": "my-log-bucket"
}
```

#### `google-cloud-logging_list_log_buckets`
List all log buckets in the project.

#### `google-cloud-logging_create_log_sink`
Create a log sink for exporting logs.
```json
{
  "sink_name": "my-sink",
  "destination": "storage.googleapis.com/my-export-bucket",
  "filter_string": "severity>=WARNING"
}
```

#### `google-cloud-logging_list_log_sinks`
List all log sinks in the project.

#### `google-cloud-logging_delete_log_sink`
Delete a log sink.
```json
{
  "sink_name": "my-sink"
}
```

#### `google-cloud-logging_create_exclusion`
Create a log exclusion filter.
```json
{
  "exclusion_name": "debug-exclusion",
  "filter_string": "severity<INFO"
}
```

#### `google-cloud-logging_list_exclusions`
List all log exclusions.

#### `google-cloud-logging_delete_exclusion`
Delete a log exclusion.
```json
{
  "exclusion_name": "debug-exclusion"
}
```

#### `google-cloud-logging_search_logs`
Search logs with simplified parameters.
```json
{
  "search_query": "error occurred",
  "time_range_hours": 12,
  "severity_levels": ["ERROR", "CRITICAL"]
}
```

#### `google-cloud-logging_export_logs_to_storage`
Create a sink to export logs to Cloud Storage.
```json
{
  "sink_name": "storage-export",
  "bucket_name": "my-log-exports"
}
```

#### `google-cloud-logging_export_logs_to_bigquery`
Create a sink to export logs to BigQuery.
```json
{
  "sink_name": "bigquery-export",
  "dataset_id": "log_analysis"
}
```
</details>

<details>
<summary>>Cloud Storage Tools</summary>

#### `google-cloud-storage_create_bucket`
Create a new Cloud Storage bucket.
```json
{
  "bucket_name": "my-new-bucket",
  "location": "US",
  "storage_class": "STANDARD"
}
```

#### `google-cloud-storage_delete_bucket`
Delete a bucket.
```json
{
  "bucket_name": "my-bucket"
}
```

#### `google-cloud-storage_list_buckets`
List all buckets in the project.

#### `google-cloud-storage_upload_file`
Upload a file to a bucket.
```json
{
  "bucket_name": "my-bucket",
  "local_file_path": "/path/to/file.txt",
  "blob_name": "uploads/file.txt"
}
```

#### `google-cloud-storage_download_file`
Download a file from a bucket.
```json
{
  "bucket_name": "my-bucket",
  "blob_name": "uploads/file.txt",
  "local_file_path": "/path/to/download/file.txt"
}
```

#### `google-cloud-storage_delete_file`
Delete a file from a bucket.
```json
{
  "bucket_name": "my-bucket",
  "blob_name": "uploads/file.txt"
}
```

#### `google-cloud-storage_list_files`
List files in a bucket.
```json
{
  "bucket_name": "my-bucket",
  "prefix": "uploads/",
  "max_results": 100
}
```

#### `google-cloud-storage_copy_file`
Copy a file within or between buckets.
```json
{
  "source_bucket": "source-bucket",
  "source_blob": "file.txt",
  "destination_bucket": "dest-bucket",
  "destination_blob": "backup/file.txt"
}
```

#### `google-cloud-storage_move_file`
Move a file within or between buckets.
```json
{
  "source_bucket": "source-bucket",
  "source_blob": "file.txt",
  "destination_bucket": "dest-bucket",
  "destination_blob": "moved/file.txt"
}
```

#### `google-cloud-storage_generate_signed_url`
Generate a signed URL for temporary access.
```json
{
  "bucket_name": "my-bucket",
  "blob_name": "private/file.txt",
  "expiration_hours": 24,
  "method": "GET"
}
```

#### `google-cloud-storage_set_bucket_lifecycle`
Set lifecycle management policies.
```json
{
  "bucket_name": "my-bucket",
  "rules": [
    {
      "action": "Delete",
      "conditions": {"age": 365}
    }
  ]
}
```

#### `google-cloud-storage_batch_upload`
Upload multiple files to a bucket.
```json
{
  "bucket_name": "my-bucket",
  "file_mappings": [
    {
      "local_path": "/path/file1.txt",
      "blob_name": "uploads/file1.txt"
    }
  ]
}
```

#### `google-cloud-storage_batch_download`
Download multiple files from a bucket.
```json
{
  "bucket_name": "my-bucket",
  "file_mappings": [
    {
      "blob_name": "uploads/file1.txt",
      "local_path": "/path/download/file1.txt"
    }
  ]
}
```

#### `google-cloud-storage_search_files`
Search for files using patterns.
```json
{
  "bucket_name": "my-bucket",
  "name_pattern": "*.log",
  "size_range": {"min_bytes": 1024, "max_bytes": 1048576}
}
```
</details>

<details>
<summary>Compute Engine Tools</summary>

#### `google-cloud-compute_create_instance`
Create a new VM instance.
```json
{
  "instance_name": "my-vm",
  "zone": "us-central1-a",
  "machine_type": "e2-medium",
  "image_family": "ubuntu-2004-lts",
  "image_project": "ubuntu-os-cloud"
}
```

#### `google-cloud-compute_delete_instance`
Delete a VM instance.
```json
{
  "instance_name": "my-vm",
  "zone": "us-central1-a"
}
```

#### `google-cloud-compute_start_instance`
Start a stopped VM instance.
```json
{
  "instance_name": "my-vm",
  "zone": "us-central1-a"
}
```

#### `google-cloud-compute_stop_instance`
Stop a running VM instance.
```json
{
  "instance_name": "my-vm",
  "zone": "us-central1-a"
}
```

#### `google-cloud-compute_restart_instance`
Restart a VM instance.
```json
{
  "instance_name": "my-vm",
  "zone": "us-central1-a"
}
```

#### `google-cloud-compute_list_instances`
List all VM instances in a zone.
```json
{
  "zone": "us-central1-a"
}
```

#### `google-cloud-compute_get_instance`
Get detailed information about a VM instance.
```json
{
  "instance_name": "my-vm",
  "zone": "us-central1-a"
}
```

#### `google-cloud-compute_list_zones`
List all available zones in the project.

#### `google-cloud-compute_get_operation_status`
Get the status of a Compute Engine operation.
```json
{
  "operation_name": "operation-123456",
  "zone": "us-central1-a"
}
```
</details>

## 🖥️ Claude Desktop Configuration

Add the following configuration to your Claude Desktop MCP settings file:

```json
{
  "mcpServers": {
    "google-cloud-mcp": {
      "command": "uvx",
      "args": [
        "google-cloud-mcp",
        "--project-id", "your-project-id",
        "--service-account-path", "/path/to/your/service-account-key.json"
        "--allowed-buckets", "bucket1,bucket2,bucket3",
        "--allowed-datasets", "dataset1,dataset2",
        "--allowed-log-buckets", "log-bucket1",
        "--allowed-instances", "vm1,vm2"
      ],
    }
  }
}
```

### Configuration Notes:

1. **Project ID**: Replace `your-project-id` with your actual Google Cloud Project ID
2. **Service Account**: Replace `/path/to/your/service-account-key.json` with the path to your service account JSON file
3. **Access Controls**: Specify comma-separated lists of allowed resources to restrict access

## 🏗️ Architecture

The project follows a modular architecture with separate managers for each GCP service:

- **BigQuery** (`src/big_query.py`): Data warehouse operations including query execution, data loading/exporting, job management, and cost estimation
- **Cloud Logging** (`src/cloud_logging.py`): Log management operations including reading/writing logs, managing buckets, sinks, exclusions, and metrics
- **Cloud Storage** (`src/cloud_storage.py`): Bucket and object management including CRUD operations, lifecycle management, and batch operations
- **Compute Engine** (`src/compute_engine.py`): Virtual machine management including instance lifecycle operations and zone management

Each manager class follows a consistent pattern:
- Constructor takes `project_id` and optional `service_account_path`
- Methods return dictionaries with operation results
- Comprehensive error handling and logging
- Support for both service account and default credential authentication

## 🧪 Testing

Run the test server:
```bash
uv run test_server.py
```

This will test all available MCP tools and verify their functionality.

## 🔧 Development

### Project Structure
```
google-cloud-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── big_query.py       # BigQuery manager
│   ├── cloud_logging.py   # Cloud Logging manager  
│   ├── cloud_storage.py   # Cloud Storage manager
│   └── compute_engine.py  # Compute Engine manager
├── main.py                # Entry point
├── test_server.py         # Test runner
├── pyproject.toml         # Package configuration
├── CLAUDE.md             # Development guidelines
└── README.md             # This file
```

### Key Design Patterns

1. **Consistent Return Types**: All methods return dictionaries for easy JSON serialization
2. **Flexible Authentication**: Support for both service account files and default credentials  
3. **Comprehensive Error Handling**: Specific exception handling for different GCP error types
4. **Extensive Logging**: Detailed logging throughout for debugging and monitoring
5. **MCP Integration**: Full compliance with MCP protocol specifications

## 📋 Requirements

- Python 3.8+
- Google Cloud SDK (optional, for default credentials)
- Required Python packages (automatically installed):
  - `google-cloud-bigquery`
  - `google-cloud-logging` 
  - `google-cloud-storage`
  - `google-cloud-compute`
  - `mcp`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Cloud Platform for comprehensive APIs
- MCP (Model Context Protocol) for the integration framework
- The Python community for excellent cloud libraries

---

**Note**: This project is designed to work seamlessly with AI models through the MCP protocol, providing a comprehensive interface for Google Cloud Platform operations.