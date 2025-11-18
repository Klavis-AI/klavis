import logging
from typing import Any, Dict
from datetime import datetime, timedelta
from .base import get_salesforce_conn, handle_salesforce_error, format_success_response

# Configure logging
logger = logging.getLogger(__name__)

async def get_attachments_for_record(
    record_id: str,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get attachments (Files) for a specific record.
    
    Args:
        record_id: The ID of the parent record (Account, Opportunity, Case, etc.)
        limit: Maximum number of attachments to return
    
    Returns:
        Dictionary containing ContentDocuments (Files) metadata
    """
    logger.info(f"Executing tool: get_attachments_for_record with record_id: {record_id}, limit: {limit}")
    try:
        sf = get_salesforce_conn()
        
        # Query ContentDocumentLinks to get Files (modern approach)
        content_query = f"""
            SELECT ContentDocumentId, ContentDocument.Title, ContentDocument.FileType, 
                   ContentDocument.ContentSize, ContentDocument.CreatedDate, 
                   ContentDocument.LastModifiedDate, ContentDocument.Owner.Name,
                   ContentDocument.LatestPublishedVersionId
            FROM ContentDocumentLink 
            WHERE LinkedEntityId = '{record_id}'
            ORDER BY ContentDocument.CreatedDate DESC
            LIMIT {limit}
        """
        
        content_result = sf.query(content_query)
        files = []
        
        for record in content_result.get('records', []):
            version_id = record.get('ContentDocument', {}).get('LatestPublishedVersionId')
            doc_id = record.get('ContentDocumentId')
            
            file_info = {
                'id': doc_id,
                'title': record.get('ContentDocument', {}).get('Title'),
                'file_type': record.get('ContentDocument', {}).get('FileType'),
                'size': record.get('ContentDocument', {}).get('ContentSize'),
                'created_date': record.get('ContentDocument', {}).get('CreatedDate'),
                'last_modified_date': record.get('ContentDocument', {}).get('LastModifiedDate'),
                'owner_name': record.get('ContentDocument', {}).get('Owner', {}).get('Name'),
                'latest_version_id': version_id,
                'type': 'ContentDocument'
            }
            
            files.append(file_info)
        
        return {
            'success': True,
            'record_id': record_id,
            'files': files,
            'total_count': len(files),
        }
        
    except Exception as e:
        logger.exception(f"Error executing tool get_attachments_for_record: {e}")
        return handle_salesforce_error(e, "get attachments for", f"record {record_id}")


async def get_attachment_temporary_download_url(
    attachment_id: str
) -> Dict[str, Any]:
    """
    Get temporary download URL for a specific ContentDocument by ID.
    Creates a public download link that expires in 1 hour.
    
    Args:
        attachment_id: The ID of the ContentDocument
    
    Returns:
        Dictionary containing attachment metadata and temporary download URL
    """
    logger.info(f"Executing tool: get_attachment_temporary_download_url with attachment_id: {attachment_id}")
    try:
        sf = get_salesforce_conn()
        
        # Get ContentDocument metadata
        doc_query = f"""
            SELECT Id, Title, FileType, ContentSize, CreatedDate, 
                   LastModifiedDate, Owner.Name, LatestPublishedVersionId
            FROM ContentDocument 
            WHERE Id = '{attachment_id}'
        """
        
        doc_result = sf.query(doc_query)
        
        if doc_result.get('totalSize', 0) == 0:
            return {
                'success': False,
                'error': f'ContentDocument with ID {attachment_id} not found'
            }
        
        doc_record = doc_result['records'][0]
        version_id = doc_record.get('LatestPublishedVersionId')
        
        if not version_id:
            return {
                'success': False,
                'error': 'No published version found for this document'
            }
        
        # Create temporary ContentDistribution for public download link (expires in 1 hour)
        expiry_date = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
        distribution_data = {
            'ContentVersionId': version_id,
            'Name': f'Temp Download - {doc_record.get("Title")}',
            'PreferencesAllowViewInBrowser': True,
            'PreferencesAllowOriginalDownload': True,
            'PreferencesExpires': True,
            'ExpiryDate': expiry_date
        }
        distribution = sf.ContentDistribution.create(distribution_data)
        
        # Query the created distribution to get the download URL
        dist_query = f"""
            SELECT ContentDownloadUrl, DistributionPublicUrl, ExpiryDate
            FROM ContentDistribution 
            WHERE Id = '{distribution['id']}'
        """
        dist_result = sf.query(dist_query)
        
        if dist_result.get('totalSize', 0) == 0:
            return {
                'success': False,
                'error': 'Failed to create download link'
            }
        
        dist_record = dist_result['records'][0]
        
        return {
            'success': True,
            'id': attachment_id,
            'title': doc_record.get('Title'),
            'file_type': doc_record.get('FileType'),
            'size': doc_record.get('ContentSize'),
            'created_date': doc_record.get('CreatedDate'),
            'last_modified_date': doc_record.get('LastModifiedDate'),
            'owner_name': doc_record.get('Owner', {}).get('Name'),
            'version_id': version_id,
            'download_url': dist_record.get('ContentDownloadUrl'),
            'public_url': dist_record.get('DistributionPublicUrl'),
            'expires_at': dist_record.get('ExpiryDate'),
            'note': 'Public download link expires in 1 hour.'
        }
        
    except Exception as e:
        logger.exception(f"Error executing tool get_attachment_temporary_download_url: {e}")
        return handle_salesforce_error(e, "get download URL for", f"attachment {attachment_id}")


async def search_attachments(
    query: str,
    limit: int = 20,
    search_type: str = "all"
) -> Dict[str, Any]:
    """
    Search for files across Salesforce.
    
    Args:
        query: Search term to find in file names/titles
        limit: Maximum number of results to return
        search_type: Type to search - only "files" is supported
    
    Returns:
        Dictionary containing matching files with download URLs
    """
    logger.info(f"Executing tool: search_attachments with query: {query}, limit: {limit}, type: {search_type}")
    try:
        sf = get_salesforce_conn()
        
        files = []
        
        if search_type in ["files", "all"]:
            # Search ContentDocuments
            content_query = f"""
                SELECT Id, Title, FileType, ContentSize, CreatedDate, 
                       LastModifiedDate, Owner.Name, LatestPublishedVersionId
                FROM ContentDocument 
                WHERE Title LIKE '%{query}%'
                ORDER BY CreatedDate DESC
                LIMIT {limit}
            """
            
            content_result = sf.query(content_query)
            
            for record in content_result.get('records', []):
                version_id = record.get('LatestPublishedVersionId')
                doc_id = record.get('Id')
                
                file_info = {
                    'id': doc_id,
                    'title': record.get('Title'),
                    'file_type': record.get('FileType'),
                    'size': record.get('ContentSize'),
                    'created_date': record.get('CreatedDate'),
                    'last_modified_date': record.get('LastModifiedDate'),
                    'owner_name': record.get('Owner', {}).get('Name'),
                    'version_id': version_id,
                    'type': 'ContentDocument'
                }
                files.append(file_info)
        
        return {
            'success': True,
            'query': query,
            'files': files,
            'total_count': len(files)
        }
        
    except Exception as e:
        logger.exception(f"Error executing tool search_attachments: {e}")
        return handle_salesforce_error(e, "search", f"attachments with query '{query}'")
