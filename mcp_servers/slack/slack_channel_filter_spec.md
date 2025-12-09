# Specification: Enhanced List Filtering for Slack MCP Server

**Date**: 2025-12-09
**Components**:
- `mcp_servers/slack/user_tools/channels.py` - Tool: `slack_user_list_channels`
- `mcp_servers/slack/user_tools/users.py` - Tool: `slack_list_users`

## Overview

Enhance the `slack_user_list_channels` and `slack_list_users` tools to support client-side filtering and provide flexible response formats (concise vs detailed) with user-friendly result summaries.

## Motivation

Currently, `slack_user_list_channels` and `slack_list_users` return all items without filtering capabilities. Users need to:
1. Filter channels by name (partial match, case-insensitive) or DMs by user ID
2. Filter users by name (partial match, case-insensitive) or user ID
3. Choose between concise (minimal fields) and detailed (full object) response formats
4. Receive clear feedback about search results and pagination status

## API Design

### New Parameters

```typescript
interface ListChannelsParams {
  // Existing parameters
  limit?: number;           // Default: 100, Max: 200
  cursor?: string;          // Pagination cursor from previous response
  types?: string;           // Default: "public_channel"

  // New filtering parameters
  channel_name?: string;    // Filter by channel name (case-insensitive partial match)
  user_id?: string;         // Filter DMs by user ID (only applies when types includes "im")

  // New response format parameter
  response_format?: "concise" | "detailed";  // Default: "concise"
}
```

### Parameter Validation Rules

1. **channel_name**:
   - Optional string
   - Case-insensitive partial matching against `name` or `name_normalized` fields
   - Applies to: `public_channel`, `private_channel`, `mpim`
   - Ignored for `im` type (DMs don't have channel names)

2. **user_id**:
   - Optional string
   - Exact match against `user` field in DM objects
   - Only applies when `types` includes `"im"`
   - Ignored for non-DM types

3. **response_format**:
   - Optional enum: `"concise"` (default) or `"detailed"`
   - `"concise"`: Returns minimal fields (see below)
   - `"detailed"`: Returns full channel objects from Slack API

### Response Format

#### Concise Format (Default)

For channels (public_channel, private_channel, mpim):
```json
{
  "id": "C012AB3CD",
  "name": "general"
}
```

For DMs (im):
```json
{
  "id": "D0C0F7S8Y",
  "user": "U0BS9U4SV"
}
```

#### Detailed Format

Returns the complete channel object as received from Slack API (no modification).

### Response Structure

```typescript
interface ListChannelsResponse {
  ok: boolean;
  channels: Array<ConciseChannel | DetailedChannel>;
  response_metadata?: {
    next_cursor?: string;
  };
  summary: {
    total_returned: number;
    message: string;
  };
}
```

### Summary Message Logic

```typescript
function generateSummary(
  totalReturned: number,
  hasNextCursor: boolean
): string {
  if (hasNextCursor) {
    return `Found ${totalReturned} channels. More results available - please specify the cursor parameter to continue.`;
  }
  return `Found ${totalReturned} channels.`;
}
```

## Implementation Details

### Filtering Logic

```python
def filter_channels(
    channels: List[Dict[str, Any]],
    channel_name: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Client-side filtering of channels.

    Args:
        channels: Raw channel list from Slack API
        channel_name: Optional channel name filter (case-insensitive partial match)
        user_id: Optional user ID filter for DMs (exact match)

    Returns:
        Filtered list of channels
    """
    filtered = channels

    # Filter by channel name (for non-DM types)
    if channel_name:
        channel_name_lower = channel_name.lower()
        filtered = [
            ch for ch in filtered
            if not ch.get("is_im", False) and (
                channel_name_lower in ch.get("name", "").lower() or
                channel_name_lower in ch.get("name_normalized", "").lower()
            )
        ]

    # Filter by user ID (for DM type only)
    if user_id:
        filtered = [
            ch for ch in filtered
            if ch.get("is_im", False) and ch.get("user") == user_id
        ]

    return filtered
```

### Response Formatting Logic

```python
def format_channel_response(
    channel: Dict[str, Any],
    response_format: str = "concise"
) -> Dict[str, Any]:
    """
    Format a single channel object based on response_format.

    Args:
        channel: Raw channel object from Slack API
        response_format: "concise" or "detailed"

    Returns:
        Formatted channel object
    """
    if response_format == "detailed":
        return channel

    # Concise format
    if channel.get("is_im", False):
        # DM: return id and user
        return {
            "id": channel["id"],
            "user": channel.get("user")
        }
    else:
        # Channel/Group/MPIM: return id and name
        return {
            "id": channel["id"],
            "name": channel.get("name")
        }
```

### Updated Function Signature

```python
async def list_channels(
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    types: Optional[str] = None,
    channel_name: Optional[str] = None,
    user_id: Optional[str] = None,
    response_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all channels the authenticated user has access to with optional filtering.

    This uses the user token to list channels, which means it can access:
    - Public channels in the workspace
    - Private channels the user is a member of
    - Direct messages (DMs)
    - Multi-party direct messages (group DMs)

    Args:
        limit: Maximum number of channels to return from API (default 100, max 200)
        cursor: Pagination cursor for next page of results
        types: Channel types to include (public_channel, private_channel, mpim, im)
        channel_name: Filter by channel name (case-insensitive partial match)
        user_id: Filter DMs by user ID (exact match, only for im type)
        response_format: Response format - "concise" (default) or "detailed"

    Returns:
        Dictionary containing:
        - ok: boolean
        - channels: filtered and formatted channel list
        - response_metadata: pagination info (if available)
        - summary: result summary with total count and helpful message
    """
```

## MCP Tool Schema Update

```python
types.Tool(
    name="slack_user_list_channels",
    description="List all channels the authenticated user has access to. Supports filtering by channel name or DM user ID, and flexible response formats.",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "number",
                "description": "Maximum number of channels to return from API (default 100, max 200)",
                "default": 100,
            },
            "cursor": {
                "type": "string",
                "description": "Pagination cursor for next page of results. Use the value from response_metadata.next_cursor in the previous response.",
            },
            "types": {
                "type": "string",
                "description": "Mix and match channel types by providing a comma-separated list of any combination of public_channel, private_channel, mpim, im",
                "default": "public_channel",
            },
            "channel_name": {
                "type": "string",
                "description": "Filter channels by name (case-insensitive partial match). Applies to public_channel, private_channel, and mpim types. Ignored for im (DM) type.",
            },
            "user_id": {
                "type": "string",
                "description": "Filter DMs by user ID (exact match). Only applies when types includes 'im'. Ignored for other channel types.",
            },
            "response_format": {
                "type": "string",
                "enum": ["concise", "detailed"],
                "description": "Response format. 'concise' (default) returns only id and name/user fields. 'detailed' returns complete channel objects.",
                "default": "concise",
            },
        },
    },
    annotations=types.ToolAnnotations(
        **{"category": "SLACK_CHANNEL", "readOnlyHint": True}
    ),
)
```

## Implementation Steps

1. **Update `channels.py`**:
   - Add new parameters to `list_channels()` function
   - Implement `filter_channels()` helper function
   - Implement `format_channel_response()` helper function
   - Implement `generate_summary()` helper function
   - Update response structure to include `summary` field

2. **Update `server.py`**:
   - Update tool schema with new parameters
   - Update tool handler to pass new parameters to `list_channels()`

3. **Testing**:
   - Test channel name filtering (partial match, case-insensitive)
   - Test user ID filtering for DMs
   - Test concise vs detailed response formats
   - Test summary messages with/without results
   - Test summary messages with/without pagination
   - Test edge cases (empty results, single result, multiple pages)

## Example Usage

### Example 1: Find channels matching "announce"
```python
# Request
{
  "channel_name": "announce",
  "types": "public_channel,private_channel",
  "response_format": "concise"
}

# Response
{
  "ok": true,
  "channels": [
    {"id": "C123", "name": "announcements"},
    {"id": "C456", "name": "team-announce"}
  ],
  "response_metadata": {
    "next_cursor": ""
  },
  "summary": {
    "total_returned": 2,
    "message": "Found 2 channels. More results available - please specify the cursor parameter to continue."
  }
}
```

### Example 2: Find DM with specific user
```python
# Request
{
  "user_id": "U0BS9U4SV",
  "types": "im",
  "response_format": "concise"
}

# Response
{
  "ok": true,
  "channels": [
    {"id": "D0C0F7S8Y", "user": "U0BS9U4SV"}
  ],
  "response_metadata": {
    "next_cursor": ""
  },
  "summary": {
    "total_returned": 1,
    "message": "Found 1 channels. More results available - please specify the cursor parameter to continue."
  }
}
```

### Example 3: No results with pagination available
```python
# Request
{
  "channel_name": "nonexistent",
  "types": "public_channel"
}

# Response
{
  "ok": true,
  "channels": [],
  "response_metadata": {
    "next_cursor": "dGVhbTpDMDYxRkE1UEI="
  },
  "summary": {
    "total_returned": 0,
    "message": "Found 0 channels. More results available - please specify the cursor parameter to continue."
  }
}
```

## Backward Compatibility

All new parameters are optional. Existing code calling `slack_user_list_channels` without the new parameters will continue to work with default behavior:
- No filtering applied
- Concise response format
- Summary included in response

## Performance Considerations

- Filtering is performed client-side after receiving results from Slack API
- For large workspaces, users may need to paginate through multiple pages to find all matching channels
- The `limit` parameter controls API page size, not the number of filtered results
- Consider caching channel lists if frequent lookups are needed

## Security Considerations

- User ID filtering only works for DMs the authenticated user has access to
- Channel name filtering respects Slack's access control (only shows channels user can see)
- No additional API scopes required beyond existing: `channels:read`, `groups:read`, `im:read`, `mpim:read`
