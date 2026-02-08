"""
Google BigQuery data warehouse management module
BigQuery operations wrapper for MCP Server
"""

from typing import List, Dict, Any, Optional, Union
from google.cloud import bigquery
from google.api_core import exceptions
from google.oauth2 import service_account
import pandas as pd
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BigQueryManager:
    """BigQuery data warehouse management class"""
    
    def __init__(self, project_id: str, service_account_path: Optional[str] = None):
        """
        Initialize BigQuery manager
        
        Args:
            project_id: GCP project ID
            service_account_path: Path to service account JSON file
        """
        self.project_id = project_id
        
        if service_account_path:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            self.client = bigquery.Client(
                project=project_id,
                credentials=credentials
            )
        else:
            # Use default credentials
            self.client = bigquery.Client(project=project_id)
    
    def run_query(
        self,
        query: str,
        use_legacy_sql: bool = False,
        timeout: Optional[float] = None,
        dry_run: bool = False,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute any SQL query
        
        Args:
            query: SQL query string
            use_legacy_sql: Whether to use legacy SQL
            timeout: Query timeout in seconds
            dry_run: Whether to run in dry-run mode (estimate costs without running)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing:
                - results: List of query results (if not dry_run)
                - total_rows: Total number of rows
                - bytes_processed: Bytes processed
                - bytes_billed: Bytes billed
                - estimated_cost_usd: Estimated cost in USD
                - execution_time_ms: Query execution time in milliseconds
        """
        try:
            # Configure query job
            job_config = bigquery.QueryJobConfig(
                use_legacy_sql=use_legacy_sql,
                dry_run=dry_run
            )
            
            # Execute query
            start_time = datetime.now()
            query_job = self.client.query(query, job_config=job_config)
            
            if dry_run:
                # Return query statistics for dry run
                return {
                    "results": None,
                    "total_rows": None,
                    "bytes_processed": query_job.total_bytes_processed,
                    "bytes_billed": query_job.total_bytes_billed,
                    "estimated_cost_usd": (query_job.total_bytes_billed / (1024**4)) * 5.0,  # $5 per TB
                    "execution_time_ms": 0,
                    "dry_run": True
                }
            
            # Wait for query to complete
            results = query_job.result(timeout=timeout)
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Convert results to list of dictionaries
            rows = []
            for row in results:
                if max_results and len(rows) >= max_results:
                    break
                rows.append(dict(row))
            
            logger.info(f"Query executed successfully, returned {len(rows)} rows")
            
            return {
                "results": rows,
                "total_rows": results.total_rows if hasattr(results, 'total_rows') else len(rows),
                "bytes_processed": query_job.total_bytes_processed,
                "bytes_billed": query_job.total_bytes_billed,
                "estimated_cost_usd": (query_job.total_bytes_billed / (1024**4)) * 5.0 if query_job.total_bytes_billed else 0,
                "execution_time_ms": execution_time_ms,
                "job_id": query_job.job_id,
                "dry_run": False
            }
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def run_query_to_dataframe(
        self,
        query: str,
        use_legacy_sql: bool = False,
        max_results: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a Pandas DataFrame
        
        Args:
            query: SQL query string
            use_legacy_sql: Whether to use legacy SQL
            max_results: Maximum number of results to return
            
        Returns:
            Query results as a DataFrame
        """
        try:
            job_config = bigquery.QueryJobConfig(use_legacy_sql=use_legacy_sql)
            
            # Execute query
            query_job = self.client.query(query, job_config=job_config)
            
            # Convert to DataFrame
            df = query_job.to_dataframe(max_results=max_results)
            
            logger.info(f"Query executed successfully, returned DataFrame with shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def load_data_from_csv(
        self,
        dataset_id: str,
        table_id: str,
        csv_path: str,
        schema: Optional[List[Dict[str, Any]]] = None,
        skip_leading_rows: int = 1,
        write_disposition: str = "WRITE_TRUNCATE",
        autodetect: bool = True
    ) -> Dict[str, Any]:
        """
        Load data from CSV file to a table
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            csv_path: Path to CSV file
            schema: Table schema (optional if autodetect is True)
            skip_leading_rows: Number of rows to skip (usually 1 for header)
            write_disposition: Write disposition (WRITE_TRUNCATE, WRITE_APPEND, WRITE_EMPTY)
            autodetect: Whether to automatically detect schema
            
        Returns:
            Load job information
        """
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.CSV,
                skip_leading_rows=skip_leading_rows,
                write_disposition=write_disposition,
                autodetect=autodetect
            )
            
            # Set schema if provided
            if schema and not autodetect:
                bq_schema = []
                for field in schema:
                    schema_field = bigquery.SchemaField(
                        name=field["name"],
                        field_type=field["type"],
                        mode=field.get("mode", "NULLABLE"),
                        description=field.get("description", None)
                    )
                    bq_schema.append(schema_field)
                job_config.schema = bq_schema
            
            # Load data from file
            with open(csv_path, "rb") as source_file:
                job = self.client.load_table_from_file(
                    source_file,
                    table_ref,
                    job_config=job_config
                )
            
            # Wait for job to complete
            job.result()
            
            logger.info(f"Successfully loaded data from {csv_path} to {dataset_id}.{table_id}")
            
            return {
                "job_id": job.job_id,
                "state": job.state,
                "created": job.created.isoformat() if job.created else None,
                "ended": job.ended.isoformat() if job.ended else None,
                "destination_table": f"{dataset_id}.{table_id}",
                "input_file_bytes": job.input_file_bytes,
                "output_rows": job.output_rows,
                "output_bytes": job.output_bytes
            }
            
        except Exception as e:
            logger.error(f"Failed to load CSV data: {str(e)}")
            raise
    
    def load_dataframe_to_table(
        self,
        dataset_id: str,
        table_id: str,
        dataframe: pd.DataFrame,
        write_disposition: str = "WRITE_TRUNCATE",
        create_table: bool = True
    ) -> Dict[str, Any]:
        """
        Load data from a Pandas DataFrame to a table
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            dataframe: Pandas DataFrame to load
            write_disposition: Write disposition (WRITE_TRUNCATE, WRITE_APPEND, WRITE_EMPTY)
            create_table: Whether to create table if it doesn't exist
            
        Returns:
            Load job information
        """
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=write_disposition,
                create_disposition="CREATE_IF_NEEDED" if create_table else "CREATE_NEVER"
            )
            
            # Load DataFrame
            job = self.client.load_table_from_dataframe(
                dataframe,
                table_ref,
                job_config=job_config
            )
            
            # Wait for job to complete
            job.result()
            
            logger.info(f"Successfully loaded DataFrame to {dataset_id}.{table_id}")
            
            return {
                "job_id": job.job_id,
                "state": job.state,
                "created": job.created.isoformat() if job.created else None,
                "ended": job.ended.isoformat() if job.ended else None,
                "destination_table": f"{dataset_id}.{table_id}",
                "output_rows": job.output_rows,
                "output_bytes": job.output_bytes
            }
            
        except Exception as e:
            logger.error(f"Failed to load DataFrame: {str(e)}")
            raise
    
    def export_table_to_csv(
        self,
        dataset_id: str,
        table_id: str,
        destination_uri: str,
        field_delimiter: str = ",",
        print_header: bool = True
    ) -> Dict[str, Any]:
        """
        Export table to CSV file in Google Cloud Storage
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            destination_uri: GCS URI (e.g., gs://bucket/folder/file.csv)
            field_delimiter: Field delimiter
            print_header: Whether to print header row
            
        Returns:
            Export job information
        """
        try:
            table_ref = self.client.dataset(dataset_id).table(table_id)
            
            job_config = bigquery.ExtractJobConfig(
                destination_format=bigquery.DestinationFormat.CSV,
                field_delimiter=field_delimiter,
                print_header=print_header
            )
            
            # Start export job
            job = self.client.extract_table(
                table_ref,
                destination_uri,
                job_config=job_config
            )
            
            # Wait for job to complete
            job.result()
            
            logger.info(f"Successfully exported {dataset_id}.{table_id} to {destination_uri}")
            
            return {
                "job_id": job.job_id,
                "state": job.state,
                "created": job.created.isoformat() if job.created else None,
                "ended": job.ended.isoformat() if job.ended else None,
                "source_table": f"{dataset_id}.{table_id}",
                "destination_uri": destination_uri
            }
            
        except Exception as e:
            logger.error(f"Failed to export table: {str(e)}")
            raise
    
    def list_jobs(
        self,
        max_results: Optional[int] = 10,
        state_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List recent BigQuery jobs
        
        Args:
            max_results: Maximum number of results
            state_filter: Filter by job state (PENDING, RUNNING, DONE)
            
        Returns:
            List of job information
        """
        try:
            jobs = []
            for job in self.client.list_jobs(max_results=max_results, state_filter=state_filter):
                job_info = {
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "state": job.state,
                    "user_email": job.user_email,
                    "created": job.created.isoformat() if job.created else None,
                    "started": job.started.isoformat() if job.started else None,
                    "ended": job.ended.isoformat() if job.ended else None,
                }
                
                # Add job-specific info
                if job.job_type == "query":
                    job_info["query"] = job.query[:200] + "..." if len(job.query) > 200 else job.query
                    job_info["bytes_processed"] = job.total_bytes_processed
                    job_info["bytes_billed"] = job.total_bytes_billed
                
                jobs.append(job_info)
            
            logger.info(f"Listed {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {str(e)}")
            raise
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: Job ID
            
        Returns:
            True if successfully cancelled
        """
        try:
            job = self.client.get_job(job_id)
            job.cancel()
            
            logger.info(f"Successfully cancelled job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job: {str(e)}")
            raise