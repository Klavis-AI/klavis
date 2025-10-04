"""Utilities for Google Photos MCP server."""

import os
import logging
from typing import Dict, Any, List, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

def get_photos_service(
    access_token: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    token_uri: str
):
    """Returns a Google Photos Library API service client."""
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri=token_uri,
        scopes=[
            "https://www.googleapis.com/auth/photoslibrary.appendonly",
            "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
        ]
    )
    return build("photoslibrary", "v1", credentials=credentials)

def get_picker_service(
    access_token: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    token_uri: str
) -> Any:
    """Returns a Google Photos Picker API service client."""
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri=token_uri,
        scopes=["https://www.googleapis.com/auth/photospicker.mediaitems.readonly"],
    )
    return build(
        "photospicker",
        "v1",
        credentials=credentials,
        discoveryServiceUrl="https://photospicker.googleapis.com/$discovery/rest?version=v1",
    )

def format_picker_media_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Format a picked media item from the Picker API."""
    media_file = item.get('mediaFile', {})
    metadata = media_file.get('mediaFileMetadata', {})
    
    formatted_item = {
        'id': item.get('id'),
        'createTime': item.get('createTime'),
        'type': item.get('type'),
        'filename': media_file.get('filename'),
        'mimeType': media_file.get('mimeType'),
        'baseUrl': media_file.get('baseUrl'),
        'width': metadata.get('width'),
        'height': metadata.get('height'),
        'cameraMake': metadata.get('cameraMake'),
        'cameraModel': metadata.get('cameraModel')
    }
    
    # Add type-specific metadata
    if 'photoMetadata' in metadata:
        photo_meta = metadata['photoMetadata']
        formatted_item['photoMetadata'] = {
            'focalLength': photo_meta.get('focalLength'),
            'apertureFNumber': photo_meta.get('apertureFNumber'),
            'isoEquivalent': photo_meta.get('isoEquivalent'),
            'exposureTime': photo_meta.get('exposureTime')
        }
    elif 'videoMetadata' in metadata:
        video_meta = metadata['videoMetadata']
        formatted_item['videoMetadata'] = {
            'fps': video_meta.get('fps'),
            'processingStatus': video_meta.get('processingStatus')
        }
    
    return formatted_item

def format_album_metadata(album: Dict[str, Any]) -> Dict[str, Any]:
    """Format album metadata for response."""
    return {
        'id': album.get('id'),
        'title': album.get('title'),
        'productUrl': album.get('productUrl'),
        'mediaItemsCount': album.get('mediaItemsCount'),
        'coverPhotoBaseUrl': album.get('coverPhotoBaseUrl'),
        'coverPhotoMediaItemId': album.get('coverPhotoMediaItemId'),
        'isWriteable': album.get('isWriteable', False),
        'shareInfo': album.get('shareInfo', {})
    }