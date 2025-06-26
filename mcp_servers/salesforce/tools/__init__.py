# Salesforce MCP Server Tools
# This package contains all the tool implementations organized by object type

from .accounts import (
    get_accounts, get_account_by_id, create_account, update_account, delete_account
)
from .contacts import (
    get_contacts, get_contact_by_id, create_contact, update_contact, delete_contact
)
from .opportunities import (
    get_opportunities, get_opportunity_by_id, create_opportunity, update_opportunity, delete_opportunity
)
from .leads import (
    get_leads, get_lead_by_id, create_lead, update_lead, delete_lead, convert_lead
)
from .cases import (
    get_cases, get_case_by_id, create_case, update_case, delete_case
)
from .campaigns import (
    get_campaigns, get_campaign_by_id, create_campaign, update_campaign, delete_campaign
)
from .activities import (
    get_tasks, get_task_by_id, create_task, update_task, delete_task,
    get_events, get_event_by_id, create_event, update_event, delete_event
)
from .reports import (
    get_reports, run_report, get_report_by_id
)
from .metadata import (
    describe_object, get_component_source, execute_soql_query, execute_tooling_query
)
from .base import access_token_context, instance_url_context

__all__ = [
    # Accounts
    "get_accounts",
    "get_account_by_id",
    "create_account", 
    "update_account",
    "delete_account",
    
    # Contacts
    "get_contacts",
    "get_contact_by_id",
    "create_contact",
    "update_contact", 
    "delete_contact",
    
    # Opportunities
    "get_opportunities",
    "get_opportunity_by_id",
    "create_opportunity",
    "update_opportunity",
    "delete_opportunity",
    
    # Leads
    "get_leads",
    "get_lead_by_id", 
    "create_lead",
    "update_lead",
    "delete_lead",
    "convert_lead",
    
    # Cases
    "get_cases",
    "get_case_by_id",
    "create_case",
    "update_case",
    "delete_case",
    
    # Campaigns  
    "get_campaigns",
    "get_campaign_by_id",
    "create_campaign",
    "update_campaign",
    "delete_campaign",
    
    # Activities
    "get_tasks",
    "get_task_by_id",
    "create_task",
    "update_task", 
    "delete_task",
    "get_events",
    "get_event_by_id",
    "create_event",
    "update_event",
    "delete_event",
    
    # Reports
    "get_reports",
    "run_report",
    "get_report_by_id",
    
    # Metadata & Queries
    "describe_object",
    "get_component_source", 
    "execute_soql_query",
    "execute_tooling_query",
    
    # Base
    "access_token_context",
    "instance_url_context",
] 