# Freshdesk MCP Server Tools
# This package contains all the tool implementations organized by object type


from .base import make_freshdesk_request
from .tickets import (
    create_ticket,
    get_ticket,
    update_ticket,
    delete_ticket,
    delete_multiple_tickets,
    list_tickets,
    add_note_to_ticket,
    search_tickets,
    merge_tickets,
    restore_ticket,
    watch_ticket,
    unwatch_ticket,
    delete_attachment,
    create_ticket_with_attachments,
    forward_ticket,
    get_archived_ticket,
    delete_archived_ticket,
)

__all__ = [

    # Tickets
    'create_ticket',
    'get_ticket',
    'update_ticket',
    'delete_ticket',
    'delete_multiple_tickets',
    'list_tickets',
    'add_note_to_ticket',
    'search_tickets',
    'merge_tickets',
    'restore_ticket',
    'watch_ticket',
    'unwatch_ticket',
    'forward_ticket',
    'get_archived_ticket',
    'delete_archived_ticket',

    # Attachments
    'delete_attachment',
    'create_ticket_with_attachments'
] 