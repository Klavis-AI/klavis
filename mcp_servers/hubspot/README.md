# HubSpot MCP Server

A robust server implementation that provides a comprehensive set of tools for interacting with HubSpot CRM through a Modular Control Protocol (MCP) interface. This server enables CRUD operations for HubSpot contacts, companies, deals, tickets, and custom properties.

## Features

- **Full CRM Integration**: Manage HubSpot contacts, companies, deals, and tickets
- **Advanced Search**: Search objects by property with 15+ filter operators
- **Property Management**: List and create custom contact properties
- **Dual Transport Support**: SSE and Streamable HTTP endpoints
- **Detailed Logging**: Configurable logging with rich context
- **Error Handling**: Comprehensive error handling with retry capabilities

## Tools Overview

The server provides the following HubSpot operations:

### Core Functions
- `hubspot_list_properties`: List properties for an object type
- `hubspot_search_by_property`: Search objects with advanced filters

### Contact Operations
- `get_HubSpot_contacts`: List contacts
- `get_HubSpot_contact_by_id`: Get contact by ID
- `hubspot_create_property`: Create custom property
- `hubspot_create_contact`: Create new contact
- `hubspot_update_contact_by_id`: Update contact
- `hubspot_delete_contact_by_id`: Delete contact

### Company Operations
- `hubspot_create_companies`: Create company
- `get_HubSpot_companies`: List companies
- `get_HubSpot_companies_by_id`: Get company by ID
- `hubspot_update_company_by_id`: Update company
- `hubspot_delete_company_by_id`: Delete company

### Deal Operations
- `get_HubSpot_deals`: List deals
- `get_HubSpot_deal_by_id`: Get deal by ID
- `hubspot_create_deal`: Create deal
- `hubspot_update_deal_by_id`: Update deal
- `hubspot_delete_deal_by_id`: Delete deal

### Ticket Operations
- `get_HubSpot_tickets`: List tickets
- `get_HubSpot_ticket_by_id`: Get ticket by ID
- `hubspot_create_ticket`: Create ticket
- `hubspot_update_ticket_by_id`: Update ticket
- `hubspot_delete_ticket_by_id`: Delete ticket

## Search Operators

The `hubspot_search_by_property` tool supports these filter operators:

| Operator | Description | Value Format | Example |
|----------|-------------|--------------|---------|
| `EQ` | Equal | String | `"lifecyclestage" EQ "customer"` |
| `NEQ` | Not equal | String | `"country" NEQ "India"` |
| `GT` | Greater than | String | `"numberofemployees" GT "100"` |
| `GTE` | Greater than or equal | String | `"revenue" GTE "50000"` |
| `LT` | Less than | String | `"score" LT "75"` |
| `LTE` | Less than or equal | String | `"createdate" LTE "2023-01-01T00:00:00Z"` |
| `BETWEEN` | Within range | JSON list | `"createdate" BETWEEN ["start", "end"]` |
| `IN` | One of values | JSON list | `"industry" IN ["Tech", "Healthcare"]` |
| `NOT_IN` | None of values | JSON list | `"state" NOT_IN ["CA", "NY"]` |
| `CONTAINS_TOKEN` | Contains word | String | `"notes" CONTAINS_TOKEN "demo"` |
| `NOT_CONTAINS_TOKEN` | Doesn't contain word | String | `"comments" NOT_CONTAINS_TOKEN "urgent"` |
| `STARTS_WITH` | Starts with substring | String | `"firstname" STARTS_WITH "Jo"` |
| `ENDS_WITH` | Ends with substring | String | `"email" ENDS_WITH "@gmail.com"` |
| `ON_OR_AFTER` | Date same or after | ISO date | `"createdate" ON_OR_AFTER "2024-01-01"` |
| `ON_OR_BEFORE` | Date same or before | ISO date | `"closedate" ON_OR_BEFORE "2024-12-31"` |


## Error Handling

The server uses structured error responses with these components:
- `message`: Human-readable error description
- `additional_prompt_content`: Guidance for resolving the issue
- `retry_after_ms`: Recommended retry delay in milliseconds
- `developer_message`: Technical error details

## Logging

Configure logging level with `--log-level` option:
- `DEBUG`: Detailed operational insights
- `INFO`: General operation tracking (default)
- `WARNING`: Potential issues
- `ERROR`: Operation failures
- `CRITICAL`: Server-critical issues

## Security Note

**Rotate your access token immediately** if you've ever committed it to version control. Always use environment variables for sensitive credentials.

