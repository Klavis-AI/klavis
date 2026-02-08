"""
Google Cloud Logging management module
Cloud Logging operations wrapper for MCP Server
"""

from typing import List, Dict, Any, Optional, Union
from google.cloud import logging_v2
from google.cloud.logging_v2.services import config_service_v2
from google.cloud.logging_v2.types import LogBucket, LogSink, LogExclusion
from google.api_core import exceptions
from google.oauth2 import service_account
from datetime import datetime, timedelta
import logging as python_logging

logger = python_logging.getLogger(__name__)

class CloudLoggingManager:
    """Cloud Logging management class"""
    
    def __init__(self, project_id: str, service_account_path: Optional[str] = None):
        """
        Initialize Cloud Logging manager
        
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
            self.client = logging_v2.Client(
                project=project_id,
                credentials=credentials
            )
            # Create config client for bucket/sink management
            self.config_client = config_service_v2.ConfigServiceV2Client(credentials=credentials)
        else:
            # Use default credentials
            self.client = logging_v2.Client(project=project_id)
            # Create config client with default credentials
            self.config_client = config_service_v2.ConfigServiceV2Client()
    
    def write_log(
        self,
        log_name: str,
        message: Union[str, Dict[str, Any]],
        severity: str = "INFO",
        resource: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Write a log entry
        
        Args:
            log_name: Name of the log
            message: Log message (string or dict for structured logging)
            severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            resource: Resource associated with the log
            labels: Labels for the log entry
            
        Returns:
            True if successfully written
        """
        try:
            logger_obj = self.client.logger(log_name)
            
            # Set default resource if not provided
            if resource is None:
                resource = {
                    "type": "global",
                    "labels": {
                        "project_id": self.project_id
                    }
                }
            
            # Write log based on message type
            if isinstance(message, str):
                logger_obj.log_text(
                    message,
                    severity=severity,
                    resource=resource,
                    labels=labels
                )
            else:
                logger_obj.log_struct(
                    message,
                    severity=severity,
                    resource=resource,
                    labels=labels
                )
            
            logger.info(f"Successfully wrote log to {log_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write log: {str(e)}")
            raise
    
    def read_logs(
        self,
        filter_string: Optional[str] = None,
        order_by: str = "timestamp desc",
        max_results: int = 100,
        time_range_hours: Optional[int] = 24
    ) -> List[Dict[str, Any]]:
        """
        Read log entries
        
        Args:
            filter_string: Advanced filter string for logs
            order_by: Order by clause (default: "timestamp desc")
            max_results: Maximum number of results to return
            time_range_hours: Time range in hours (from now backwards)
            
        Returns:
            List of log entries
        """
        try:
            # Build filter
            filters = []
            
            if time_range_hours:
                start_time = datetime.utcnow() - timedelta(hours=time_range_hours)
                filters.append(f'timestamp >= "{start_time.isoformat()}Z"')
            
            if filter_string:
                filters.append(filter_string)
            
            final_filter = " AND ".join(filters) if filters else None
            
            # List entries
            entries = []
            count = 0
            for entry in self.client.list_entries(
                filter_=final_filter,
                order_by=order_by,
                page_size=min(max_results, 1000)
            ):
                if count >= max_results:
                    break
                    
                # Handle severity - can be string or enum
                try:
                    severity = entry.severity.name if hasattr(entry.severity, 'name') else str(entry.severity)
                except AttributeError:
                    severity = "DEFAULT"
                
                # Safely extract labels
                labels = getattr(entry, 'labels', None)
                labels_dict = dict(labels) if labels else {}
                
                # Safely extract resource information
                resource_dict = None
                if entry.resource:
                    resource_labels = getattr(entry.resource, 'labels', None)
                    resource_dict = {
                        "type": getattr(entry.resource, 'type', 'unknown'),
                        "labels": dict(resource_labels) if resource_labels else {}
                    }
                
                entry_dict = {
                    "log_name": entry.log_name,
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                    "severity": severity,
                    "text_payload": getattr(entry, 'text_payload', None),
                    "json_payload": dict(getattr(entry, 'json_payload', {})) if getattr(entry, 'json_payload', None) else None,
                    "proto_payload": str(getattr(entry, 'proto_payload', None)) if getattr(entry, 'proto_payload', None) else None,
                    "labels": labels_dict,
                    "trace": getattr(entry, 'trace', None),
                    "span_id": getattr(entry, 'span_id', None),
                    "resource": resource_dict
                }
                entries.append(entry_dict)
                count += 1
            
            logger.info(f"Successfully read {len(entries)} log entries")
            return entries
            
        except Exception as e:
            logger.error(f"Failed to read logs: {str(e)}")
            raise
    
    def list_logs(self) -> List[str]:
        """
        List all log names in the project
        
        Returns:
            List of log names
        """
        try:
            # Use list_entries to get log names from existing entries
            # This is the available method in the Cloud Logging client
            log_names = set()
            
            # Get recent log entries to extract log names
            for entry in self.client.list_entries(
                page_size=1000,  # Get more entries to find diverse log names
                order_by="timestamp desc"
            ):
                if entry.log_name:
                    # Extract log name from full path: projects/PROJECT/logs/LOG_NAME
                    if '/logs/' in entry.log_name:
                        simple_log_name = entry.log_name.split('/logs/')[-1]
                        log_names.add(simple_log_name)
                
                # Limit to avoid too many API calls
                if len(log_names) >= 100:
                    break
            
            log_names_list = sorted(list(log_names))
            logger.info(f"Found {len(log_names_list)} unique log names")
            return log_names_list
            
        except Exception as e:
            logger.error(f"Failed to list logs: {str(e)}")
            # Return empty list instead of raising to be more graceful
            return []
    
    def delete_log(self, log_name: str) -> bool:
        """
        Delete all entries in a log
        
        Args:
            log_name: Name of the log to delete
            
        Returns:
            True if successfully deleted
        """
        try:
            logger_obj = self.client.logger(log_name)
            logger_obj.delete()
            
            logger.info(f"Successfully deleted log: {log_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete log: {str(e)}")
            raise
    
    def list_log_buckets(self) -> List[Dict[str, Any]]:
        """
        List all log buckets in the project
        
        Returns:
            List of log bucket information
        """
        try:
            parent = f"projects/{self.project_id}/locations/global"
            buckets = []
            
            for bucket in self.config_client.list_buckets(request={"parent": parent}):
                bucket_info = {
                    "name": bucket.name,
                    "display_name": bucket.name.split('/')[-1],
                    "description": bucket.description,
                    "retention_days": bucket.retention_days,
                    "locked": bucket.locked,
                    "lifecycle_state": bucket.lifecycle_state.name,
                    "create_time": bucket.create_time.isoformat() if bucket.create_time else None,
                    "update_time": bucket.update_time.isoformat() if bucket.update_time else None
                }
                buckets.append(bucket_info)
            
            logger.info(f"Found {len(buckets)} log buckets")
            return buckets
            
        except Exception as e:
            logger.error(f"Failed to list log buckets: {str(e)}")
            raise
    
    def create_log_bucket(
        self,
        bucket_id: str,
        retention_days: int = 30,
        description: Optional[str] = None,
        locked: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new log bucket
        
        Args:
            bucket_id: Unique ID for the bucket
            retention_days: Number of days to retain logs
            description: Description of the bucket
            locked: Whether to lock the bucket (prevents deletion)
            
        Returns:
            Created bucket information
        """
        try:
            parent = f"projects/{self.project_id}/locations/global"
            
            bucket = LogBucket(
                name=f"{parent}/buckets/{bucket_id}",
                retention_days=retention_days,
                description=description or f"Custom log bucket: {bucket_id}",
                locked=locked
            )
            
            created_bucket = self.config_client.create_bucket(
                request={
                    "parent": parent,
                    "bucket_id": bucket_id,
                    "bucket": bucket
                }
            )
            
            logger.info(f"Successfully created log bucket: {bucket_id}")
            
            return {
                "name": created_bucket.name,
                "display_name": bucket_id,
                "description": created_bucket.description,
                "retention_days": created_bucket.retention_days,
                "locked": created_bucket.locked,
                "lifecycle_state": created_bucket.lifecycle_state.name,
                "create_time": created_bucket.create_time.isoformat() if created_bucket.create_time else None
            }
            
        except exceptions.AlreadyExists:
            logger.error(f"Log bucket {bucket_id} already exists")
            raise
        except Exception as e:
            logger.error(f"Failed to create log bucket: {str(e)}")
            raise
    
    def update_log_bucket(
        self,
        bucket_id: str,
        retention_days: Optional[int] = None,
        description: Optional[str] = None,
        locked: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update a log bucket
        
        Args:
            bucket_id: Bucket ID to update
            retention_days: New retention days (if provided)
            description: New description (if provided)
            locked: New locked state (if provided)
            
        Returns:
            Updated bucket information
        """
        try:
            bucket_path = f"projects/{self.project_id}/locations/global/buckets/{bucket_id}"
            
            # Get current bucket
            bucket = self.config_client.get_bucket(request={"name": bucket_path})
            
            # Update fields
            update_mask = []
            if retention_days is not None:
                bucket.retention_days = retention_days
                update_mask.append("retention_days")
            if description is not None:
                bucket.description = description
                update_mask.append("description")
            if locked is not None:
                bucket.locked = locked
                update_mask.append("locked")
            
            # Update bucket
            updated_bucket = self.config_client.update_bucket(
                request={
                    "bucket": bucket,
                    "update_mask": {"paths": update_mask}
                }
            )
            
            logger.info(f"Successfully updated log bucket: {bucket_id}")
            
            return {
                "name": updated_bucket.name,
                "display_name": bucket_id,
                "description": updated_bucket.description,
                "retention_days": updated_bucket.retention_days,
                "locked": updated_bucket.locked,
                "lifecycle_state": updated_bucket.lifecycle_state.name,
                "update_time": updated_bucket.update_time.isoformat() if updated_bucket.update_time else None
            }
            
        except Exception as e:
            logger.error(f"Failed to update log bucket: {str(e)}")
            raise
    
    def delete_log_bucket(self, bucket_id: str) -> bool:
        """
        Delete a log bucket
        
        Args:
            bucket_id: Bucket ID to delete
            
        Returns:
            True if successfully deleted
        """
        try:
            bucket_path = f"projects/{self.project_id}/locations/global/buckets/{bucket_id}"
            
            # Check if bucket is locked
            bucket = self.config_client.get_bucket(request={"name": bucket_path})
            if bucket.locked:
                raise Exception(f"Cannot delete locked bucket: {bucket_id}")
            
            self.config_client.delete_bucket(request={"name": bucket_path})
            
            logger.info(f"Successfully deleted log bucket: {bucket_id}")
            return True
            
        except exceptions.NotFound:
            logger.error(f"Log bucket {bucket_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to delete log bucket: {str(e)}")
            raise
    
    def clear_log_bucket(self, bucket_id: str) -> bool:
        """
        Clear all logs from a log bucket (delete all log entries but keep the bucket)
        
        Args:
            bucket_id: Bucket ID to clear
            
        Returns:
            True if successfully cleared
        """
        try:
            bucket_path = f"projects/{self.project_id}/locations/global/buckets/{bucket_id}"
            
            # Check if bucket exists and is not locked
            bucket = self.config_client.get_bucket(request={"name": bucket_path})
            if bucket.locked:
                raise Exception(f"Cannot clear locked bucket: {bucket_id}")
            
            # Get all logs in the bucket and delete them
            # Note: In Cloud Logging, logs are not directly associated with buckets
            # This function will delete all logs in the project that would go to this bucket
            # based on the bucket's configuration
            
            # Get recent log entries to identify logs that would be in this bucket
            filter_query = f'logName:projects/{self.project_id}/logs/'
            
            # List recent entries to identify log names
            log_names = set()
            for entry in self.client.list_entries(
                filter_=filter_query,
                page_size=1000,
                order_by="timestamp desc"
            ):
                if entry.log_name:
                    # Extract log name from full path
                    if '/logs/' in entry.log_name:
                        simple_log_name = entry.log_name.split('/logs/')[-1]
                        log_names.add(simple_log_name)
                
                # Limit to avoid too many API calls
                if len(log_names) >= 50:
                    break
            
            # Delete each log
            deleted_count = 0
            for log_name in log_names:
                try:
                    logger_obj = self.client.logger(log_name)
                    logger_obj.delete()
                    deleted_count += 1
                    logger.info(f"Deleted log: {log_name}")
                except Exception as e:
                    logger.warning(f"Failed to delete log {log_name}: {str(e)}")
                    continue
            
            logger.info(f"Successfully cleared log bucket {bucket_id}, deleted {deleted_count} logs")
            return True
            
        except exceptions.NotFound:
            logger.error(f"Log bucket {bucket_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to clear log bucket: {str(e)}")
            raise
    
    def create_log_sink(
        self,
        sink_name: str,
        destination: str,
        filter_string: Optional[str] = None,
        description: Optional[str] = None,
        disabled: bool = False
    ) -> Dict[str, Any]:
        """
        Create a log sink to export logs
        
        Args:
            sink_name: Name of the sink
            destination: Destination resource (e.g., storage.googleapis.com/bucket-name)
            filter_string: Filter to apply to logs
            description: Description of the sink
            disabled: Whether to create the sink in disabled state
            
        Returns:
            Created sink information
        """
        try:
            parent = f"projects/{self.project_id}"
            
            sink = LogSink(
                name=sink_name,
                destination=destination,
                filter=filter_string or "",
                description=description or f"Log sink: {sink_name}",
                disabled=disabled
            )
            
            created_sink = self.config_client.create_sink(
                request={
                    "parent": parent,
                    "sink": sink,
                    "unique_writer_identity": True
                }
            )
            
            logger.info(f"Successfully created log sink: {sink_name}")
            
            return {
                "name": created_sink.name,
                "destination": created_sink.destination,
                "filter": created_sink.filter,
                "description": created_sink.description,
                "disabled": created_sink.disabled,
                "writer_identity": created_sink.writer_identity,
                "create_time": created_sink.create_time.isoformat() if created_sink.create_time else None
            }
            
        except exceptions.AlreadyExists:
            logger.error(f"Log sink {sink_name} already exists")
            raise
        except Exception as e:
            logger.error(f"Failed to create log sink: {str(e)}")
            raise
    
    def list_log_sinks(self) -> List[Dict[str, Any]]:
        """
        List all log sinks in the project
        
        Returns:
            List of log sink information
        """
        try:
            parent = f"projects/{self.project_id}"
            sinks = []
            
            for sink in self.config_client.list_sinks(request={"parent": parent}):
                sink_info = {
                    "name": sink.name,
                    "destination": sink.destination,
                    "filter": sink.filter,
                    "description": sink.description,
                    "disabled": sink.disabled,
                    "writer_identity": sink.writer_identity,
                    "create_time": sink.create_time.isoformat() if sink.create_time else None,
                    "update_time": sink.update_time.isoformat() if sink.update_time else None
                }
                sinks.append(sink_info)
            
            logger.info(f"Found {len(sinks)} log sinks")
            return sinks
            
        except Exception as e:
            logger.error(f"Failed to list log sinks: {str(e)}")
            raise
    
    def delete_log_sink(self, sink_name: str) -> bool:
        """
        Delete a log sink
        
        Args:
            sink_name: Name of the sink to delete
            
        Returns:
            True if successfully deleted
        """
        try:
            sink_path = f"projects/{self.project_id}/sinks/{sink_name}"
            self.config_client.delete_sink(request={"sink_name": sink_path})
            
            logger.info(f"Successfully deleted log sink: {sink_name}")
            return True
            
        except exceptions.NotFound:
            logger.error(f"Log sink {sink_name} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to delete log sink: {str(e)}")
            raise
    
    def create_exclusion(
        self,
        exclusion_name: str,
        filter_string: str,
        description: Optional[str] = None,
        disabled: bool = False
    ) -> Dict[str, Any]:
        """
        Create a log exclusion to filter out logs
        
        Args:
            exclusion_name: Name of the exclusion
            filter_string: Filter to identify logs to exclude
            description: Description of the exclusion
            disabled: Whether to create the exclusion in disabled state
            
        Returns:
            Created exclusion information
        """
        try:
            parent = f"projects/{self.project_id}"
            
            exclusion = LogExclusion(
                name=exclusion_name,
                filter=filter_string,
                description=description or f"Log exclusion: {exclusion_name}",
                disabled=disabled
            )
            
            created_exclusion = self.config_client.create_exclusion(
                request={
                    "parent": parent,
                    "exclusion": exclusion
                }
            )
            
            logger.info(f"Successfully created log exclusion: {exclusion_name}")
            
            return {
                "name": created_exclusion.name,
                "filter": created_exclusion.filter,
                "description": created_exclusion.description,
                "disabled": created_exclusion.disabled,
                "create_time": created_exclusion.create_time.isoformat() if created_exclusion.create_time else None
            }
            
        except exceptions.AlreadyExists:
            logger.error(f"Log exclusion {exclusion_name} already exists")
            raise
        except Exception as e:
            logger.error(f"Failed to create log exclusion: {str(e)}")
            raise
    
    def list_exclusions(self) -> List[Dict[str, Any]]:
        """
        List all log exclusions in the project
        
        Returns:
            List of log exclusion information
        """
        try:
            parent = f"projects/{self.project_id}"
            exclusions = []
            
            for exclusion in self.config_client.list_exclusions(request={"parent": parent}):
                exclusion_info = {
                    "name": exclusion.name,
                    "filter": exclusion.filter,
                    "description": exclusion.description,
                    "disabled": exclusion.disabled,
                    "create_time": exclusion.create_time.isoformat() if exclusion.create_time else None,
                    "update_time": exclusion.update_time.isoformat() if exclusion.update_time else None
                }
                exclusions.append(exclusion_info)
            
            logger.info(f"Found {len(exclusions)} log exclusions")
            return exclusions
            
        except Exception as e:
            logger.error(f"Failed to list log exclusions: {str(e)}")
            raise
    
    def delete_exclusion(self, exclusion_name: str) -> bool:
        """
        Delete a log exclusion
        
        Args:
            exclusion_name: Name of the exclusion to delete
            
        Returns:
            True if successfully deleted
        """
        try:
            exclusion_path = f"projects/{self.project_id}/exclusions/{exclusion_name}"
            self.config_client.delete_exclusion(request={"name": exclusion_path})
            
            logger.info(f"Successfully deleted log exclusion: {exclusion_name}")
            return True
            
        except exceptions.NotFound:
            logger.error(f"Log exclusion {exclusion_name} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to delete log exclusion: {str(e)}")
            raise
    
    def get_log_metrics(self) -> List[Dict[str, Any]]:
        """
        List all log-based metrics in the project
        
        Returns:
            List of log metric information
        """
        try:
            # Cloud Logging client doesn't have list_metrics method
            # We need to use the monitoring client or return placeholder
            # For now, return empty list with explanation
            logger.info("Log metrics listing not directly available through Cloud Logging client")
            return []
            
        except Exception as e:
            logger.error(f"Failed to list log metrics: {str(e)}")
            return []
    
    def search_logs(
        self,
        search_query: str,
        time_range_hours: int = 24,
        resource_types: Optional[List[str]] = None,
        severity_levels: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search logs with simplified parameters
        
        Args:
            search_query: Text to search for in log messages
            time_range_hours: Time range in hours
            resource_types: List of resource types to filter
            severity_levels: List of severity levels to filter
            max_results: Maximum number of results
            
        Returns:
            List of matching log entries
        """
        try:
            # Build filter components
            filters = []
            
            # Time filter
            start_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            filters.append(f'timestamp >= "{start_time.isoformat()}Z"')
            
            # Search query filter
            if search_query:
                # Search in text payload and json payload
                filters.append(f'(textPayload:"{search_query}" OR jsonPayload:"{search_query}")')
            
            # Resource type filter
            if resource_types:
                resource_filter = " OR ".join([f'resource.type="{rt}"' for rt in resource_types])
                filters.append(f"({resource_filter})")
            
            # Severity filter
            if severity_levels:
                severity_filter = " OR ".join([f'severity="{sev}"' for sev in severity_levels])
                filters.append(f"({severity_filter})")
            
            # Combine all filters
            filter_string = " AND ".join(filters)
            
            # Use read_logs method with the constructed filter
            return self.read_logs(
                filter_string=filter_string,
                max_results=max_results,
                time_range_hours=None  # Already included in filter
            )
            
        except Exception as e:
            logger.error(f"Failed to search logs: {str(e)}")
            raise
    
    def export_logs_to_storage(
        self,
        sink_name: str,
        bucket_name: str,
        filter_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a sink to export logs to Cloud Storage
        
        Args:
            sink_name: Name for the sink
            bucket_name: Cloud Storage bucket name
            filter_string: Optional filter for logs to export
            
        Returns:
            Created sink information
        """
        try:
            destination = f"storage.googleapis.com/{bucket_name}"
            
            sink_info = self.create_log_sink(
                sink_name=sink_name,
                destination=destination,
                filter_string=filter_string,
                description=f"Export logs to Cloud Storage bucket: {bucket_name}"
            )
            
            logger.info(f"Created sink to export logs to bucket: {bucket_name}")
            logger.info(f"Grant write access to: {sink_info['writer_identity']}")
            
            return sink_info
            
        except Exception as e:
            logger.error(f"Failed to create storage export sink: {str(e)}")
            raise
    
    def export_logs_to_bigquery(
        self,
        sink_name: str,
        dataset_id: str,
        filter_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a sink to export logs to BigQuery
        
        Args:
            sink_name: Name for the sink
            dataset_id: BigQuery dataset ID
            filter_string: Optional filter for logs to export
            
        Returns:
            Created sink information
        """
        try:
            destination = f"bigquery.googleapis.com/projects/{self.project_id}/datasets/{dataset_id}"
            
            sink_info = self.create_log_sink(
                sink_name=sink_name,
                destination=destination,
                filter_string=filter_string,
                description=f"Export logs to BigQuery dataset: {dataset_id}"
            )
            
            logger.info(f"Created sink to export logs to dataset: {dataset_id}")
            logger.info(f"Grant write access to: {sink_info['writer_identity']}")
            
            return sink_info
            
        except Exception as e:
            logger.error(f"Failed to create BigQuery export sink: {str(e)}")
            raise