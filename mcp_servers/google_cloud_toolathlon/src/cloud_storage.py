"""
Google Cloud Storage bucket management module
Cloud Storage operations wrapper for MCP Server
"""

from typing import List, Dict, Any, Optional, IO, Union
from google.cloud import storage
from google.api_core import exceptions
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

class CloudStorageManager:
    """Cloud Storage bucket management class"""
    
    def __init__(self, project_id: str, service_account_json: str = "service-account-key.json"):
        """
        Initialize Cloud Storage manager
        
        Args:
            project_id: GCP project ID
            service_account_json: Path to service account JSON file
        """
        self.project_id = project_id
        self.client = storage.Client.from_service_account_json(
            json_credentials_path=service_account_json,
            project=project_id
        )
    
    def list_buckets(self) -> List[Dict[str, Any]]:
        """
        List all buckets
        
        Returns:
            List of buckets
        """
        try:
            buckets = []
            for bucket in self.client.list_buckets():
                buckets.append(self._bucket_to_dict(bucket))
            
            logger.info(f"Successfully listed {len(buckets)} buckets")
            return buckets
            
        except Exception as e:
            logger.error(f"Failed to list buckets: {str(e)}")
            raise
    
    def get_bucket_info(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket detailed information
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            Bucket detailed information
        """
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.reload()  # Get latest information
            return self._bucket_to_dict(bucket)
            
        except exceptions.NotFound:
            logger.error(f"Bucket {bucket_name} does not exist")
            raise
        except Exception as e:
            logger.error(f"Failed to get bucket information: {str(e)}")
            raise
    
    def create_bucket(
        self,
        bucket_name: str,
        location: str = "US",
        storage_class: str = "STANDARD"
    ) -> Dict[str, Any]:
        """
        Create a new bucket
        
        Args:
            bucket_name: Bucket name
            location: Storage location
            storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
            
        Returns:
            Created bucket information
        """
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.location = location
            bucket.storage_class = storage_class
            
            new_bucket = self.client.create_bucket(bucket)
            logger.info(f"Successfully created bucket: {bucket_name}")
            return self._bucket_to_dict(new_bucket)
            
        except exceptions.Conflict:
            logger.error(f"Bucket {bucket_name} already exists")
            raise
        except Exception as e:
            logger.error(f"Failed to create bucket: {str(e)}")
            raise
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete bucket
        
        Args:
            bucket_name: Bucket name
            force: Whether to force delete (including all contents)
            
        Returns:
            Whether deletion was successful
        """
        try:
            bucket = self.client.bucket(bucket_name)
            
            if force:
                # Delete all objects first
                self._delete_all_objects(bucket)
            
            bucket.delete()
            logger.info(f"Successfully deleted bucket: {bucket_name}")
            return True
            
        except exceptions.NotFound:
            logger.error(f"Bucket {bucket_name} does not exist")
            raise
        except Exception as e:
            logger.error(f"Failed to delete bucket: {str(e)}")
            raise
    
    def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List objects in bucket
        
        Args:
            bucket_name: Bucket name
            prefix: Prefix filter
            delimiter: Delimiter (for simulating folders)
            max_results: Maximum number of results
            
        Returns:
            List of objects
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(
                prefix=prefix,
                delimiter=delimiter,
                max_results=max_results
            )
            
            objects = []
            for blob in blobs:
                objects.append(self._blob_to_dict(blob))
            
            logger.info(f"Listed {len(objects)} objects")
            return objects
            
        except Exception as e:
            logger.error(f"Failed to list objects: {str(e)}")
            raise
    
    def upload_file(
        self,
        bucket_name: str,
        source_file_path: str,
        destination_blob_name: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload file to bucket
        
        Args:
            bucket_name: Bucket name
            source_file_path: Source file path
            destination_blob_name: Target object name (defaults to filename)
            content_type: Content type
            
        Returns:
            Uploaded object information
        """
        try:
            bucket = self.client.bucket(bucket_name)
            
            if destination_blob_name is None:
                destination_blob_name = os.path.basename(source_file_path)
            
            blob = bucket.blob(destination_blob_name)
            
            if content_type:
                blob.content_type = content_type
            
            blob.upload_from_filename(source_file_path)
            logger.info(f"Successfully uploaded file: {source_file_path} -> {destination_blob_name}")
            
            return self._blob_to_dict(blob)
            
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise
    
    def upload_data(
        self,
        bucket_name: str,
        data: Union[str, bytes],
        destination_blob_name: str,
        content_type: str = "text/plain"
    ) -> Dict[str, Any]:
        """
        Upload data to bucket
        
        Args:
            bucket_name: Bucket name
            data: Data to upload
            destination_blob_name: Target object name
            content_type: Content type
            
        Returns:
            Uploaded object information
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.content_type = content_type
            
            if isinstance(data, str):
                blob.upload_from_string(data, content_type=content_type)
            else:
                blob.upload_from_string(data)
            
            logger.info(f"Successfully uploaded data to: {destination_blob_name}")
            return self._blob_to_dict(blob)
            
        except Exception as e:
            logger.error(f"Failed to upload data: {str(e)}")
            raise
    
    def download_file(
        self,
        bucket_name: str,
        source_blob_name: str,
        destination_file_path: str
    ) -> str:
        """
        Download file from bucket
        
        Args:
            bucket_name: Bucket name
            source_blob_name: Source object name
            destination_file_path: Target file path
            
        Returns:
            Downloaded file path
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
            
            blob.download_to_filename(destination_file_path)
            logger.info(f"Successfully downloaded file: {source_blob_name} -> {destination_file_path}")
            
            return destination_file_path
            
        except exceptions.NotFound:
            logger.error(f"Object {source_blob_name} does not exist")
            raise
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            raise
    
    def download_data(self, bucket_name: str, source_blob_name: str) -> bytes:
        """
        Download data from bucket
        
        Args:
            bucket_name: Bucket name
            source_blob_name: Source object name
            
        Returns:
            Downloaded data
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            
            data = blob.download_as_bytes()
            logger.info(f"Successfully downloaded data: {source_blob_name}")
            
            return data
            
        except exceptions.NotFound:
            logger.error(f"Object {source_blob_name} does not exist")
            raise
        except Exception as e:
            logger.error(f"Failed to download data: {str(e)}")
            raise
    
    def delete_object(self, bucket_name: str, blob_name: str) -> bool:
        """
        Delete object
        
        Args:
            bucket_name: Bucket name
            blob_name: Object name
            
        Returns:
            Whether deletion was successful
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            
            logger.info(f"Successfully deleted object: {blob_name}")
            return True
            
        except exceptions.NotFound:
            logger.warning(f"Object {blob_name} does not exist")
            return False
        except Exception as e:
            logger.error(f"Failed to delete object: {str(e)}")
            raise
    
    def delete_objects(self, bucket_name: str, prefix: str) -> int:
        """
        Batch delete objects
        
        Args:
            bucket_name: Bucket name
            prefix: Object prefix
            
        Returns:
            Number of deleted objects
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            
            count = 0
            for blob in blobs:
                blob.delete()
                count += 1
            
            logger.info(f"Successfully deleted {count} objects")
            return count
            
        except Exception as e:
            logger.error(f"Failed to batch delete objects: {str(e)}")
            raise
    
    def copy_object(
        self,
        source_bucket: str,
        source_object: str,
        destination_bucket: str,
        destination_object: str
    ) -> Dict[str, Any]:
        """
        Copy object
        
        Args:
            source_bucket: Source bucket
            source_object: Source object name
            destination_bucket: Destination bucket
            destination_object: Destination object name
            
        Returns:
            New object information
        """
        try:
            source_bucket_obj = self.client.bucket(source_bucket)
            source_blob = source_bucket_obj.blob(source_object)
            
            destination_bucket_obj = self.client.bucket(destination_bucket)
            destination_blob = source_bucket_obj.copy_blob(
                source_blob,
                destination_bucket_obj,
                destination_object
            )
            
            logger.info(f"Successfully copied object: {source_object} -> {destination_object}")
            return self._blob_to_dict(destination_blob)
            
        except Exception as e:
            logger.error(f"Failed to copy object: {str(e)}")
            raise
    
    def generate_signed_url(
        self,
        bucket_name: str,
        blob_name: str,
        expiration_minutes: int = 60,
        method: str = "GET"
    ) -> str:
        """
        Generate signed URL
        
        Args:
            bucket_name: Bucket name
            blob_name: Object name
            expiration_minutes: Expiration time in minutes
            method: HTTP method
            
        Returns:
            Signed URL
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method=method
            )
            
            logger.info(f"Generated signed URL: {blob_name}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {str(e)}")
            raise
    
    def _bucket_to_dict(self, bucket: storage.Bucket) -> Dict[str, Any]:
        """Convert bucket object to dictionary"""
        try:
            # Convert lifecycle_rules generator to list to get length
            lifecycle_rules = list(bucket.lifecycle_rules) if bucket.lifecycle_rules else []
            lifecycle_count = len(lifecycle_rules)
        except Exception:
            lifecycle_count = 0
            
        return {
            "name": bucket.name,
            "location": bucket.location,
            "storage_class": bucket.storage_class,
            "created": bucket.time_created.isoformat() if bucket.time_created else None,
            "labels": dict(bucket.labels) if bucket.labels else {},
            "versioning_enabled": bucket.versioning_enabled,
            "lifecycle_rules": lifecycle_count
        }
    
    def _blob_to_dict(self, blob: storage.Blob) -> Dict[str, Any]:
        """Convert blob object to dictionary"""
        return {
            "name": blob.name,
            "size": blob.size,
            "content_type": blob.content_type,
            "created": blob.time_created.isoformat() if blob.time_created else None,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "md5_hash": blob.md5_hash,
            "crc32c": blob.crc32c,
            "storage_class": blob.storage_class,
            "metadata": dict(blob.metadata) if blob.metadata else {}
        }
    
    def _delete_all_objects(self, bucket: storage.Bucket):
        """Delete all objects in bucket"""
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()
        logger.info(f"Deleted all objects in bucket {bucket.name}")
    
    def set_bucket_lifecycle(
        self,
        bucket_name: str,
        age_days: Optional[int] = None,
        storage_class: Optional[str] = None,
        action: str = "Delete"
    ) -> Dict[str, Any]:
        """
        Set bucket lifecycle rules
        
        Args:
            bucket_name: Bucket name
            age_days: Object age in days
            storage_class: Storage class to transition to
            action: Action type (Delete or SetStorageClass)
            
        Returns:
            Updated bucket information
        """
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.reload()
            
            rule = {
                "action": {"type": action},
                "condition": {}
            }
            
            if age_days is not None:
                rule["condition"]["age"] = age_days
            
            if action == "SetStorageClass" and storage_class:
                rule["action"]["storageClass"] = storage_class
            
            # Add rule to existing rules list
            lifecycle_rules = list(bucket.lifecycle_rules)
            lifecycle_rules.append(rule)
            bucket.lifecycle_rules = lifecycle_rules
            
            bucket.patch()
            logger.info(f"Successfully set lifecycle rules for bucket {bucket_name}")
            
            return self._bucket_to_dict(bucket)
            
        except Exception as e:
            logger.error(f"Failed to set lifecycle rules: {str(e)}")
            raise
    
    def enable_versioning(self, bucket_name: str, enabled: bool = True) -> Dict[str, Any]:
        """
        Enable or disable bucket versioning
        
        Args:
            bucket_name: Bucket name
            enabled: Whether to enable versioning
            
        Returns:
            Updated bucket information
        """
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.versioning_enabled = enabled
            bucket.patch()
            
            status = "enabled" if enabled else "disabled"
            logger.info(f"Successfully {status} versioning for bucket {bucket_name}")
            
            return self._bucket_to_dict(bucket)
            
        except Exception as e:
            logger.error(f"Failed to set versioning: {str(e)}")
            raise
    
    def set_bucket_labels(self, bucket_name: str, labels: Dict[str, str]) -> Dict[str, Any]:
        """
        Set bucket labels
        
        Args:
            bucket_name: Bucket name
            labels: Labels dictionary
            
        Returns:
            Updated bucket information
        """
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.labels = labels
            bucket.patch()
            
            logger.info(f"Successfully set labels for bucket {bucket_name}")
            return self._bucket_to_dict(bucket)
            
        except Exception as e:
            logger.error(f"Failed to set labels: {str(e)}")
            raise
    
    def get_bucket_size(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket size statistics
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            Dictionary containing size statistics
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs()
            
            total_size = 0
            total_count = 0
            size_by_class = {}
            
            for blob in blobs:
                total_size += blob.size or 0
                total_count += 1
                
                storage_class = blob.storage_class or "STANDARD"
                if storage_class not in size_by_class:
                    size_by_class[storage_class] = {"count": 0, "size": 0}
                
                size_by_class[storage_class]["count"] += 1
                size_by_class[storage_class]["size"] += blob.size or 0
            
            return {
                "bucket_name": bucket_name,
                "total_objects": total_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
                "size_by_storage_class": size_by_class
            }
            
        except Exception as e:
            logger.error(f"Failed to get bucket size: {str(e)}")
            raise
    
    def upload_directory(
        self,
        bucket_name: str,
        source_directory: str,
        destination_prefix: str = "",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Upload entire directory to bucket
        
        Args:
            bucket_name: Bucket name
            source_directory: Source directory path
            destination_prefix: Destination prefix
            recursive: Whether to recursively upload subdirectories
            
        Returns:
            List of uploaded objects
        """
        try:
            uploaded_objects = []
            
            if recursive:
                # Recursively traverse directory
                for root, dirs, files in os.walk(source_directory):
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        # Calculate relative path
                        relative_path = os.path.relpath(file_path, source_directory)
                        blob_name = os.path.join(destination_prefix, relative_path).replace("\\", "/")
                        
                        obj_info = self.upload_file(bucket_name, file_path, blob_name)
                        uploaded_objects.append(obj_info)
            else:
                # Only upload files in current directory
                for file_name in os.listdir(source_directory):
                    file_path = os.path.join(source_directory, file_name)
                    if os.path.isfile(file_path):
                        blob_name = os.path.join(destination_prefix, file_name).replace("\\", "/")
                        obj_info = self.upload_file(bucket_name, file_path, blob_name)
                        uploaded_objects.append(obj_info)
            
            logger.info(f"Successfully uploaded {len(uploaded_objects)} files")
            return uploaded_objects
            
        except Exception as e:
            logger.error(f"Failed to upload directory: {str(e)}")
            raise
    
    def download_directory(
        self,
        bucket_name: str,
        prefix: str,
        destination_directory: str
    ) -> List[str]:
        """
        Download directory from bucket
        
        Args:
            bucket_name: Bucket name
            prefix: Object prefix
            destination_directory: Destination directory
            
        Returns:
            List of downloaded file paths
        """
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            
            downloaded_files = []
            
            for blob in blobs:
                # Build local file path
                relative_path = blob.name[len(prefix):].lstrip("/")
                local_file_path = os.path.join(destination_directory, relative_path)
                
                # Create directory
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Download file
                blob.download_to_filename(local_file_path)
                downloaded_files.append(local_file_path)
                logger.info(f"Downloaded: {blob.name} -> {local_file_path}")
            
            logger.info(f"Successfully downloaded {len(downloaded_files)} files")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Failed to download directory: {str(e)}")
            raise
    
    def move_object(
        self,
        source_bucket: str,
        source_object: str,
        destination_bucket: str,
        destination_object: str
    ) -> Dict[str, Any]:
        """
        Move object (copy then delete source object)
        
        Args:
            source_bucket: Source bucket
            source_object: Source object name
            destination_bucket: Destination bucket
            destination_object: Destination object name
            
        Returns:
            New object information
        """
        try:
            # Copy first
            new_object = self.copy_object(
                source_bucket,
                source_object,
                destination_bucket,
                destination_object
            )
            
            # Then delete source object
            self.delete_object(source_bucket, source_object)
            
            logger.info(f"Successfully moved object: {source_object} -> {destination_object}")
            return new_object
            
        except Exception as e:
            logger.error(f"Failed to move object: {str(e)}")
            raise
    
    def search_objects(
        self,
        bucket_name: str,
        pattern: str,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for objects matching pattern
        
        Args:
            bucket_name: Bucket name
            pattern: Search pattern (supports wildcards)
            max_results: Maximum number of results
            
        Returns:
            List of matching objects
        """
        try:
            import fnmatch
            
            bucket = self.client.bucket(bucket_name)
            all_blobs = bucket.list_blobs()
            
            matched_objects = []
            count = 0
            
            for blob in all_blobs:
                if fnmatch.fnmatch(blob.name, pattern):
                    matched_objects.append(self._blob_to_dict(blob))
                    count += 1
                    
                    if max_results and count >= max_results:
                        break
            
            logger.info(f"Found {len(matched_objects)} matching objects")
            return matched_objects
            
        except Exception as e:
            logger.error(f"Failed to search objects: {str(e)}")
            raise