# Freshdesk MCP Server Tools
# This package contains all the tool implementations organized by object type


from .base import  auth_token_context, domain_context
from .tickets import (
    create_ticket,
    get_ticket_by_id,
    update_ticket,
    delete_ticket,
    delete_multiple_tickets,
    list_tickets,
    add_note_to_ticket,
    filter_tickets,
    merge_tickets,
    restore_ticket,
    watch_ticket,
    unwatch_ticket,
    delete_attachment,
    create_ticket_with_attachments,
    forward_ticket,
    get_archived_ticket,
    delete_archived_ticket,
    reply_to_a_ticket,
    update_note,
    delete_note,
)

from .contacts import (
    create_contact,
    get_contact_by_id,
    list_contacts,
    update_contact,
    delete_contact,
    make_contact_agent,
    restore_contact,
    send_contact_invite,
    merge_contacts,
    filter_contacts,
    search_contacts_by_name,
)

from .companies import (
    create_company,
    get_company_by_id,
    list_companies,
    update_company,
    delete_company,
    filter_companies,
    search_companies_by_name,
)

from .accounts import (
    get_current_account,
)

from .agents import (
    list_agents,
    get_agent_by_id,
    get_current_agent,
    create_agent,
    update_agent,
    delete_agent,
    search_agents,
    bulk_create_agents,
)

from .thread import (
    create_thread,
    get_thread_by_id,
    update_thread,
    delete_thread,
    create_thread_message,
    get_thread_message_by_id,
    update_thread_message,
    delete_thread_message
)

__all__ = [

    # Context variables
    'auth_token_context',
    'domain_context',

    # Tickets
    'create_ticket',
    'get_ticket_by_id',
    'update_ticket',
    'delete_ticket',
    'delete_multiple_tickets',
    'list_tickets',
    'add_note_to_ticket',
    'filter_tickets',
    'merge_tickets',
    'restore_ticket',
    'watch_ticket',
    'unwatch_ticket',
    'forward_ticket',
    'get_archived_ticket',
    'delete_archived_ticket',
    'reply_to_a_ticket',
    'update_note',
    'delete_note',
    
    # Attachments
    'delete_attachment',
    'create_ticket_with_attachments',

    # Contacts
    'create_contact',
    'get_contact_by_id',
    'list_contacts',
    'update_contact',
    'delete_contact',
    'make_contact_agent',
    'restore_contact',
    'send_contact_invite',
    'merge_contacts',
    'filter_contacts',
    'search_contacts_by_name',

    # Companies
    'create_company',
    'get_company_by_id',
    'list_companies',
    'update_company',
    'delete_company',
    'filter_companies',
    'search_companies_by_name',

    # Accounts
    'get_current_account',
    
    # Agent exports
    'list_agents',
    'get_agent_by_id',
    'get_current_agent',
    'create_agent',
    'update_agent',
    'delete_agent',
    'search_agents',
    'bulk_create_agents',
    
    # Threads
    'create_thread',
    'get_thread_by_id',
    'update_thread',
    'delete_thread',
    'create_thread_message',
    'get_thread_message_by_id',
    'update_thread_message',
    'delete_thread_message'
] 