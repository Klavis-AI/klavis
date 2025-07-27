"""
Test fixtures for Zapier MCP Server.

This module contains reusable test data and fixtures
for all test scenarios.
"""

from typing import Dict, Any, List
from datetime import datetime

# Sample workflow data
SAMPLE_WORKFLOW_DATA = {
    "id": "workflow_123",
    "title": "Test Workflow",
    "description": "A test workflow for automation",
    "status": "draft",
    "trigger_app": "gmail",
    "trigger_event": "new_email",
    "action_app": "slack",
    "action_event": "send_message",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "execution_count": 0,
    "success_rate": 0.0
}

# Sample task data
SAMPLE_TASK_DATA = {
    "id": "task_123",
    "workflow_id": "workflow_123",
    "status": "pending",
    "input_data": {"email": "test@example.com"},
    "output_data": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}

# Sample webhook data
SAMPLE_WEBHOOK_DATA = {
    "id": "webhook_123",
    "name": "Test Webhook",
    "url": "https://example.com/webhook",
    "secret": "webhook_secret",
    "events": ["workflow.triggered"],
    "is_active": True,
    "retry_count": 3,
    "timeout_seconds": 30,
    "call_count": 0,
    "success_count": 0,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}

# Sample app data
SAMPLE_APP_DATA = {
    "id": "app_123",
    "name": "Gmail",
    "description": "Gmail integration",
    "api_key": "gmail_api_key",
    "is_connected": True,
    "connection_status": "connected",
    "supported_triggers": ["new_email", "email_received"],
    "supported_actions": ["send_email", "create_draft"],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}

# API response fixtures
API_RESPONSES = {
    "workflow_list": {
        "objects": [SAMPLE_WORKFLOW_DATA],
        "meta": {
            "total_count": 1,
            "limit": 10,
            "offset": 0
        }
    },
    "workflow_detail": SAMPLE_WORKFLOW_DATA,
    "task_list": {
        "objects": [SAMPLE_TASK_DATA],
        "meta": {
            "total_count": 1,
            "limit": 10,
            "offset": 0
        }
    },
    "task_detail": SAMPLE_TASK_DATA,
    "webhook_list": {
        "objects": [SAMPLE_WEBHOOK_DATA],
        "meta": {
            "total_count": 1,
            "limit": 10,
            "offset": 0
        }
    },
    "webhook_detail": SAMPLE_WEBHOOK_DATA,
    "app_list": {
        "objects": [SAMPLE_APP_DATA],
        "meta": {
            "total_count": 1,
            "limit": 10,
            "offset": 0
        }
    },
    "app_detail": SAMPLE_APP_DATA
}

# Error response fixtures
ERROR_RESPONSES = {
    "not_found": {
        "error": "Resource not found",
        "error_code": "NOT_FOUND_ERROR",
        "status_code": 404
    },
    "validation_error": {
        "error": "Validation failed",
        "error_code": "VALIDATION_ERROR",
        "status_code": 400
    },
    "authentication_error": {
        "error": "Authentication failed",
        "error_code": "AUTHENTICATION_ERROR",
        "status_code": 401
    },
    "rate_limit_error": {
        "error": "Rate limit exceeded",
        "error_code": "RATE_LIMIT_ERROR",
        "status_code": 429
    }
}

# Test configuration
TEST_CONFIG = {
    "api_key": "test_api_key",
    "api_base_url": "https://api.zapier.com/v1",
    "api_timeout": 30,
    "log_level": "DEBUG",
    "cache_max_size": 100,
    "cache_ttl": 60,
    "rate_limit_max_calls": 10,
    "rate_limit_window": 60
} 