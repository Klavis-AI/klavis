"""
Google Compute Engine Virtual Machine Management Module
Compute Engine operations wrapper for MCP Server
"""

from typing import List, Dict, Any, Optional
from google.cloud import compute_v1
from google.api_core import exceptions
from google.oauth2 import service_account
import logging
import os

logger = logging.getLogger(__name__)

class ComputeEngineManager:
    """Compute Engine virtual machine management class"""
    
    def __init__(self, project_id: str, service_account_path: Optional[str] = None):
        """
        Initialize Compute Engine manager
        
        Args:
            project_id: GCP project ID
            service_account_path: Path to service account JSON file (optional)
        """
        self.project_id = project_id
        
        try:
            if service_account_path and os.path.exists(service_account_path):
                # Use service account file
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                self.instances_client = compute_v1.InstancesClient(credentials=credentials)
                self.zones_client = compute_v1.ZonesClient(credentials=credentials)
                self.operations_client = compute_v1.ZoneOperationsClient(credentials=credentials)
            elif os.path.exists("service-account-key.json"):
                # Use default service account file
                self.instances_client = compute_v1.InstancesClient.from_service_account_json("service-account-key.json")
                self.zones_client = compute_v1.ZonesClient.from_service_account_json("service-account-key.json")
                self.operations_client = compute_v1.ZoneOperationsClient.from_service_account_json("service-account-key.json")
            else:
                # Use default credentials
                self.instances_client = compute_v1.InstancesClient()
                self.zones_client = compute_v1.ZonesClient()
                self.operations_client = compute_v1.ZoneOperationsClient()
                
        except Exception as e:
            logger.error(f"Failed to initialize Compute Engine clients: {e}")
            raise
    
    def list_instances(self, zone: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List virtual machine instances
        
        Args:
            zone: Optional zone, if not specified lists instances from all zones
            
        Returns:
            List of instances with name, status, zone and other information
        """
        try:
            instances = []
            
            if zone:
                # List instances in specific zone
                request = compute_v1.ListInstancesRequest(
                    project=self.project_id,
                    zone=zone
                )
                page_result = self.instances_client.list(request=request)
                
                for instance in page_result:
                    instances.append(self._instance_to_dict(instance, zone))
            else:
                # List instances in all zones
                request = compute_v1.AggregatedListInstancesRequest(
                    project=self.project_id
                )
                agg_list = self.instances_client.aggregated_list(request=request)
                
                for zone_name, response in agg_list:
                    if response.instances:
                        zone = zone_name.split('/')[-1]
                        for instance in response.instances:
                            instances.append(self._instance_to_dict(instance, zone))
            
            logger.info(f"Successfully listed {len(instances)} instances")
            return instances
            
        except Exception as e:
            logger.error(f"Failed to list instances: {str(e)}")
            raise
    
    def get_instance(self, instance_name: str, zone: str) -> Dict[str, Any]:
        """
        Get detailed information for a single instance
        
        Args:
            instance_name: Instance name
            zone: Instance zone
            
        Returns:
            Instance detailed information
        """
        try:
            request = compute_v1.GetInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            instance = self.instances_client.get(request=request)
            return self._instance_to_dict(instance, zone)
            
        except exceptions.NotFound:
            logger.error(f"Instance {instance_name} does not exist in zone {zone}")
            raise
        except Exception as e:
            logger.error(f"Failed to get instance information: {str(e)}")
            raise
    
    def start_instance(self, instance_name: str, zone: str) -> str:
        """
        Start virtual machine instance
        
        Args:
            instance_name: Instance name
            zone: Instance zone
            
        Returns:
            Operation ID
        """
        try:
            request = compute_v1.StartInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            operation = self.instances_client.start(request=request)
            
            logger.info(f"Start instance operation submitted: {instance_name}")
            return operation.name
            
        except Exception as e:
            logger.error(f"Failed to start instance: {str(e)}")
            raise
    
    def stop_instance(self, instance_name: str, zone: str) -> str:
        """
        Stop virtual machine instance
        
        Args:
            instance_name: Instance name
            zone: Instance zone
            
        Returns:
            Operation ID
        """
        try:
            request = compute_v1.StopInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            operation = self.instances_client.stop(request=request)
            
            logger.info(f"Stop instance operation submitted: {instance_name}")
            return operation.name
            
        except Exception as e:
            logger.error(f"Failed to stop instance: {str(e)}")
            raise
    
    def restart_instance(self, instance_name: str, zone: str) -> str:
        """
        Restart virtual machine instance
        
        Args:
            instance_name: Instance name
            zone: Instance zone
            
        Returns:
            Operation ID
        """
        try:
            request = compute_v1.ResetInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            operation = self.instances_client.reset(request=request)
            
            logger.info(f"Restart instance operation submitted: {instance_name}")
            return operation.name
            
        except Exception as e:
            logger.error(f"Failed to restart instance: {str(e)}")
            raise
    
    def delete_instance(self, instance_name: str, zone: str) -> str:
        """
        Delete virtual machine instance
        
        Args:
            instance_name: Instance name
            zone: Instance zone
            
        Returns:
            Operation ID
        """
        try:
            request = compute_v1.DeleteInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            operation = self.instances_client.delete(request=request)
            
            logger.info(f"Delete instance operation submitted: {instance_name}")
            return operation.name
            
        except Exception as e:
            logger.error(f"Failed to delete instance: {str(e)}")
            raise
    
    def create_instance(
        self,
        instance_name: str,
        zone: str,
        machine_type: str = "e2-micro",
        source_image: str = "projects/debian-cloud/global/images/family/debian-11",
        disk_size_gb: int = 10,
        network_name: str = "default",
        external_ip: bool = True
    ) -> str:
        """
        Create new virtual machine instance
        
        Args:
            instance_name: Instance name
            zone: Instance zone
            machine_type: Machine type
            source_image: Source image
            disk_size_gb: Boot disk size in GB
            network_name: Network name
            external_ip: Whether to assign external IP
            
        Returns:
            Operation ID
        """
        try:
            # Configure boot disk
            boot_disk = compute_v1.AttachedDisk(
                auto_delete=True,
                boot=True,
                initialize_params=compute_v1.AttachedDiskInitializeParams(
                    source_image=source_image,
                    disk_size_gb=disk_size_gb
                )
            )
            
            # Configure network
            network_interface = compute_v1.NetworkInterface(
                network=f"projects/{self.project_id}/global/networks/{network_name}"
            )
            
            if external_ip:
                access_config = compute_v1.AccessConfig(
                    name="External NAT",
                    type_="ONE_TO_ONE_NAT"
                )
                network_interface.access_configs = [access_config]
            
            # Create instance configuration
            instance = compute_v1.Instance(
                name=instance_name,
                machine_type=f"zones/{zone}/machineTypes/{machine_type}",
                disks=[boot_disk],
                network_interfaces=[network_interface]
            )
            
            # Create request
            request = compute_v1.InsertInstanceRequest(
                project=self.project_id,
                zone=zone,
                instance_resource=instance
            )
            
            operation = self.instances_client.insert(request=request)
            logger.info(f"Create instance operation submitted: {instance_name}")
            return operation.name
            
        except Exception as e:
            logger.error(f"Failed to create instance: {str(e)}")
            raise
    
    def wait_for_operation(self, operation_name: str, zone: str, timeout: int = 300) -> bool:
        """
        Wait for operation to complete
        
        Args:
            operation_name: Operation name
            zone: Zone
            timeout: Timeout in seconds
            
        Returns:
            Whether operation completed successfully
        """
        try:
            request = compute_v1.WaitZoneOperationRequest(
                project=self.project_id,
                zone=zone,
                operation=operation_name
            )
            
            operation = self.operations_client.wait(request=request, timeout=timeout)
            
            if operation.error:
                logger.error(f"Operation failed: {operation.error}")
                return False
                
            logger.info(f"Operation {operation_name} completed")
            return True
            
        except Exception as e:
            logger.error(f"Error waiting for operation completion: {str(e)}")
            return False
    
    def list_zones(self) -> List[str]:
        """
        List all available zones in the project
        
        Returns:
            List of zone names
        """
        try:
            request = compute_v1.ListZonesRequest(project=self.project_id)
            zones = self.zones_client.list(request=request)
            
            zone_names = [zone.name for zone in zones if zone.status == "UP"]
            logger.info(f"Found {len(zone_names)} available zones")
            return zone_names
            
        except Exception as e:
            logger.error(f"Failed to list zones: {str(e)}")
            raise
    
    def _instance_to_dict(self, instance: compute_v1.Instance, zone: str) -> Dict[str, Any]:
        """
        Convert instance object to dictionary
        
        Args:
            instance: Compute Engine instance object
            zone: Instance zone
            
        Returns:
            Dictionary containing instance information
        """
        # Get external IP if available
        external_ip = None
        internal_ip = None
        
        if instance.network_interfaces:
            ni = instance.network_interfaces[0]
            internal_ip = ni.network_i_p
            if ni.access_configs:
                external_ip = ni.access_configs[0].nat_i_p
        
        return {
            "name": instance.name,
            "zone": zone,
            "status": instance.status,
            "machine_type": instance.machine_type.split('/')[-1] if instance.machine_type else None,
            "internal_ip": internal_ip,
            "external_ip": external_ip,
            "creation_timestamp": instance.creation_timestamp,
            "id": str(instance.id) if instance.id else None,
            "labels": dict(instance.labels) if instance.labels else {},
            "disks": len(instance.disks) if instance.disks else 0
        }