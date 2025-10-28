# Salesforce MCP Server Tools
# This package contains all the tool implementations organized by object type

from .accounts import (
    get_accounts, create_account, update_account, delete_account
)
from .contacts import (
    get_contacts, create_contact, update_contact, delete_contact
)
from .opportunities import (
    get_opportunities, create_opportunity, update_opportunity, delete_opportunity
)
from .leads import (
    get_leads, create_lead, update_lead, delete_lead, convert_lead
)
from .cases import (
    get_cases, create_case, update_case, delete_case
)
from .campaigns import (
    get_campaigns, create_campaign, update_campaign, delete_campaign
)

from .metadata import (
    describe_object, execute_soql_query
)
from .base import access_token_context, instance_url_context

__all__ = [
    # Accounts
    "get_accounts",
    "create_account", 
    "update_account",
    "delete_account",
    
    # Contacts
    "get_contacts",
    "create_contact",
    "update_contact", 
    "delete_contact",
    
    # Opportunities
    "get_opportunities",
    "create_opportunity",
    "update_opportunity",
    "delete_opportunity",
    
    # Leads
    "get_leads",
    "create_lead",
    "update_lead",
    "delete_lead",
    "convert_lead",
    
    # Cases
    "get_cases",
    "create_case",
    "update_case",
    "delete_case",
    
    # Campaigns  
    "get_campaigns",
    "create_campaign",
    "update_campaign",
    "delete_campaign",

    
    # Metadata & Queries
    "describe_object",
    "execute_soql_query",
    
    # Base
    "access_token_context",
    "instance_url_context",
] 