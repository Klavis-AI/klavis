import os
import logging
from typing import Dict, Any

from quickbooks import QuickBooks

logger = logging.getLogger(__name__)

class QuickBooksClient:
    """Base client for QuickBooks operations."""
    
    def __init__(self):
        self.client = None
        self.sandbox = os.getenv('QB_ENVIRONMENT', 'sandbox').lower() == 'sandbox'
        
    def initialize_with_tokens(
        self, 
        access_token: str, 
        company_id: str
    ):
        """Initialize the QuickBooks client with minimal configuration.
        
        Args:
            access_token: QuickBooks access token
            company_id: QuickBooks company/realm ID
        """
        try:
            # Initialize QuickBooks client directly with minimal params
            self.client = QuickBooks(
                access_token=access_token,
                company_id=company_id,
                sandbox=self.sandbox
            )
            
            logger.info("QuickBooks client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize QuickBooks client: {e}")
            raise
    
    def initialize_from_env(self):
        """Initialize client using only environment variables."""
        access_token = os.getenv('QB_ACCESS_TOKEN')
        company_id = os.getenv('QB_REALM_ID')
        
        if not all([access_token, company_id]):
            return False
            
        try:
            self.initialize_with_tokens(access_token, company_id)
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize from environment: {e}")
            return False
        
    def is_configured(self) -> bool:
        """Check if client is properly configured."""
        return self.client is not None

    def get_client_info(self) -> Dict[str, Any]:
        """Get client configuration info for debugging."""
        return {
            "configured": self.is_configured(),
            "sandbox": self.sandbox,
        }

# Global client instance
qb_client = QuickBooksClient()