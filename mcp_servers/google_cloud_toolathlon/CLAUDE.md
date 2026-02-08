# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Google Cloud MCP (Model Context Protocol) server project that provides Python wrapper modules for managing various Google Cloud Platform services. The project is designed to be a comprehensive interface for GCP operations through MCP.

## Architecture

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

## Development Commands

### Setup
```bash
# Install dependencies (when pyproject.toml is configured)
pip install -e .

# Or install Google Cloud libraries manually
pip install google-cloud-bigquery google-cloud-logging google-cloud-storage google-cloud-compute
```

### Authentication
- Place service account JSON file as `service-account-key.json` in project root
- Or use default credentials with `gcloud auth application-default login`

### Running
```bash
python main.py
```

## Key Design Patterns

### Manager Classes
Each GCP service has a dedicated manager class that:
- Handles authentication via service account or default credentials
- Provides high-level methods that wrap GCP client operations
- Returns structured dictionaries for easy MCP integration
- Includes comprehensive error handling and logging

### Error Handling
- All methods include try/catch blocks with specific exception handling
- Google Cloud exceptions (NotFound, Conflict, etc.) are caught specifically
- Logging is used consistently throughout for debugging

### Data Structures
- Methods return dictionaries rather than native GCP objects for better serialization
- Helper methods like `_bucket_to_dict()` and `_blob_to_dict()` standardize return formats
- Optional parameters use sensible defaults

## Authentication Patterns

The codebase supports two authentication patterns:
1. **Service Account File**: Pass path to JSON key file in constructor
2. **Default Credentials**: Omit service account parameter to use ambient credentials

## Common Operations

### BigQuery
- Query execution with cost estimation via dry-run mode
- Data loading from CSV files and DataFrames
- Export to Cloud Storage
- Job management and monitoring

### Cloud Logging
- Structured and text log writing
- Advanced log filtering and searching
- Log bucket and sink management
- Export to BigQuery and Cloud Storage

### Cloud Storage
- Bucket lifecycle management
- Batch upload/download operations
- Signed URL generation
- Object search and metadata management

### Compute Engine
- VM instance lifecycle operations
- Zone listing and management
- Operation status monitoring