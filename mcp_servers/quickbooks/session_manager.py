"""
Session-based QuickBooks configuration management for MCP server.
Allows clients to provide QB credentials via headers or initialization.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

from tools.http_client import QuickBooksHTTPClient
from tools.accounts import AccountManager
from tools.invoices import InvoiceManager
from tools.customers import CustomerManager
from tools.payments import PaymentManager
from tools.vendors import VendorManager

logger = logging.getLogger(__name__)


class QuickBooksSession:
    """Represents a QuickBooks session with specific credentials."""
    
    def __init__(self, access_token: str = None, realm_id: str = None, environment: str = None):
        self.client = QuickBooksHTTPClient(
            access_token=access_token,
            company_id=realm_id,
            environment=environment
        )
        
        if not self.client.is_configured():
            raise ValueError("QuickBooks session not properly configured")
        
        # Initialize managers
        self.account_manager = AccountManager(self.client)
        self.invoice_manager = InvoiceManager(self.client)
        self.customer_manager = CustomerManager(self.client)
        self.payment_manager = PaymentManager(self.client)
        self.vendor_manager = VendorManager(self.client)
        
        logger.info(f"QuickBooks session created for realm: {realm_id or 'env'}")
    
    async def close(self):
        """Close the session and cleanup resources."""
        await self.client.close()


class SessionManager:
    """Manages QuickBooks sessions and routes requests to appropriate sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, QuickBooksSession] = {}
        self.default_session: Optional[QuickBooksSession] = None
        
        # Try to create a default session from environment variables
        try:
            self.default_session = QuickBooksSession()
            logger.info("Default QuickBooks session created from environment variables")
        except ValueError:
            logger.warning("No default QuickBooks session available. Clients must provide credentials.")
    
    def create_session_key(self, access_token: str = None, realm_id: str = None, environment: str = None) -> str:
        """Create a unique key for session caching."""
        return f"{access_token or 'env'}_{realm_id or 'env'}_{environment or 'env'}"
    
    def get_session(self, access_token: str = None, realm_id: str = None, environment: str = None) -> QuickBooksSession:
        """Get or create a session for the given credentials."""
        # If no credentials provided, use default session
        if not any([access_token, realm_id, environment]):
            if self.default_session:
                return self.default_session
            raise ValueError("No credentials provided and no default session available")
        
        # Check cache
        session_key = self.create_session_key(access_token, realm_id, environment)
        if session_key in self.sessions:
            return self.sessions[session_key]
        
        # Create new session
        try:
            session = QuickBooksSession(access_token, realm_id, environment)
            self.sessions[session_key] = session
            return session
        except ValueError as e:
            raise ValueError(f"Failed to create QuickBooks session: {str(e)}")
    
    def extract_credentials_from_headers(self, headers: Dict[str, str]) -> Tuple[str, str, str]:
        """Extract QuickBooks credentials from HTTP headers."""
        access_token = headers.get('x-qb-access-token') or headers.get('qb-access-token')
        realm_id = headers.get('x-qb-realm-id') or headers.get('qb-realm-id')
        environment = headers.get('x-qb-environment') or headers.get('qb-environment')
        
        return access_token, realm_id, environment
    
    async def cleanup(self):
        """Cleanup all sessions."""
        if self.default_session:
            await self.default_session.close()
        
        for session in self.sessions.values():
            await session.close()
        
        self.sessions.clear()
        logger.info("All QuickBooks sessions cleaned up")
