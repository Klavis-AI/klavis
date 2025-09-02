from .auth import ping_mailchimp, get_account_info
from .audiences import (
    get_all_audiences, 
    create_audience, 
    get_audience_info, 
    update_audience, 
    delete_audience
)
from .members import (
    get_audience_members,
    add_member_to_audience,
    get_member_info,
    update_member,
    delete_member,
    add_member_tags,
    remove_member_tags,
    get_member_activity
)
from .campaigns import (
    get_all_campaigns,
    create_campaign,
    get_campaign_info,
    set_campaign_content,
    send_campaign,
    schedule_campaign,
    delete_campaign
)
from .base import mailchimp_token_context

__all__ = [
    # Auth/Account
    "ping_mailchimp",
    "get_account_info",
    
    # Audiences/Lists  
    "get_all_audiences",
    "create_audience", 
    "get_audience_info",
    "update_audience",
    "delete_audience",
    
    # Members/Contacts
    "get_audience_members",
    "add_member_to_audience",
    "get_member_info", 
    "update_member",
    "delete_member",
    "add_member_tags",
    "remove_member_tags",
    "get_member_activity",
    
    # Campaigns
    "get_all_campaigns",
    "create_campaign",
    "get_campaign_info", 
    "set_campaign_content",
    "send_campaign",
    "schedule_campaign",
    "delete_campaign",
    
    # Base
    "mailchimp_token_context",
]