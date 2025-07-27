#!/usr/bin/env python3
"""
Zapier MCP Server - Design Pattern Architecture.

This server implements the Model Context Protocol (MCP) for Zapier
using enterprise-grade design patterns and clean architecture.
"""

import asyncio
import logging
import os
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

import mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# Import our design pattern architecture
from core.interfaces import ILogger, ICache
from core.base_classes import BaseClient, BaseRepository, BaseService, BaseValidator
from core.factories import ComponentFactory
from core.decorators import log_operation, retry, cache
from core.exceptions import ValidationError, ServiceError, AuthenticationError

# Import domain entities
from domain.entities import Workflow, Task, Webhook, App
from domain.value_objects import WorkflowStatus, TaskStatus, WebhookEvent
from domain.exceptions import DomainError, WorkflowNotFoundError

# Import infrastructure components
from infrastructure.clients import ZapierClient
from infrastructure.repositories import WorkflowRepository, TaskRepository, WebhookRepository, AppRepository
from infrastructure.services import WorkflowService, TaskService, WebhookService, AppService
from infrastructure.validators import WorkflowValidator, TaskValidator, WebhookValidator, AppValidator
from infrastructure.config import ZapierConfig
from infrastructure.logging import StructuredLogger
from infrastructure.caching import MemoryCache


# Global context variables
api_key_var: ContextVar[Optional[str]] = ContextVar("api_key", default=None)
logger_var: ContextVar[Optional[ILogger]] = ContextVar("logger", default=None)
cache_var: ContextVar[Optional[ICache]] = ContextVar("cache", default=None)


class ZapierMCPServer:
    """
    Zapier MCP Server implementation using design patterns.
    
    This server implements the Model Context Protocol for Zapier
    using enterprise-grade architecture with design patterns.
    """
    
    def __init__(self):
        """Initialize the Zapier MCP Server."""
        self.config = ZapierConfig()
        self.component_factory = ComponentFactory()
        self._setup_components()
        self._setup_tools()
    
    def _setup_components(self) -> None:
        """Setup all components using the Factory pattern."""
        # Setup logging
        logger = StructuredLogger(
            name="zapier_mcp_server",
            level=self.config.log_level,
            format=self.config.log_format
        )
        logger_var.set(logger)
        
        # Setup caching
        cache = MemoryCache(
            max_size=self.config.cache_max_size,
            ttl=self.config.cache_ttl
        )
        cache_var.set(cache)
        
        # Register components with factory
        self.component_factory.register_component(
            "client", "zapier",
            ZapierClient,
            api_key=self.config.api_key,
            base_url=self.config.api_base_url,
            timeout=self.config.api_timeout
        )
        
        # Register validators
        self.component_factory.register_component("validator", "workflow", WorkflowValidator)
        self.component_factory.register_component("validator", "task", TaskValidator)
        self.component_factory.register_component("validator", "webhook", WebhookValidator)
        self.component_factory.register_component("validator", "app", AppValidator)
        
        # Register repositories
        self.component_factory.register_component(
            "repository", "workflow",
            WorkflowRepository,
            client=self.component_factory.create_component("client", "zapier"),
            logger=logger,
            cache=cache
        )
        
        self.component_factory.register_component(
            "repository", "task",
            TaskRepository,
            client=self.component_factory.create_component("client", "zapier"),
            logger=logger,
            cache=cache
        )
        
        self.component_factory.register_component(
            "repository", "webhook",
            WebhookRepository,
            client=self.component_factory.create_component("client", "zapier"),
            logger=logger,
            cache=cache
        )
        
        self.component_factory.register_component(
            "repository", "app",
            AppRepository,
            client=self.component_factory.create_component("client", "zapier"),
            logger=logger,
            cache=cache
        )
        
        # Register services
        self.component_factory.register_component(
            "service", "workflow",
            WorkflowService,
            repository=self.component_factory.create_component("repository", "workflow"),
            validator=self.component_factory.create_component("validator", "workflow"),
            logger=logger
        )
        
        self.component_factory.register_component(
            "service", "task",
            TaskService,
            repository=self.component_factory.create_component("repository", "task"),
            validator=self.component_factory.create_component("validator", "task"),
            logger=logger
        )
        
        self.component_factory.register_component(
            "service", "webhook",
            WebhookService,
            repository=self.component_factory.create_component("repository", "webhook"),
            validator=self.component_factory.create_component("validator", "webhook"),
            logger=logger
        )
        
        self.component_factory.register_component(
            "service", "app",
            AppService,
            repository=self.component_factory.create_component("repository", "app"),
            validator=self.component_factory.create_component("validator", "app"),
            logger=logger
        )
    
    def _setup_tools(self) -> None:
        """Setup MCP tools using the tools from infrastructure."""
        from infrastructure.tools import (
            list_workflows_tool,
            get_workflow_tool,
            create_workflow_tool,
            update_workflow_tool,
            delete_workflow_tool,
            trigger_workflow_tool,
            list_tasks_tool,
            get_task_tool,
            list_webhooks_tool,
            create_webhook_tool,
            get_webhook_tool,
            list_apps_tool,
            get_app_tool,
            connect_app_tool
        )
        
        self.tools = [
            list_workflows_tool,
            get_workflow_tool,
            create_workflow_tool,
            update_workflow_tool,
            delete_workflow_tool,
            trigger_workflow_tool,
            list_tasks_tool,
            get_task_tool,
            list_webhooks_tool,
            create_webhook_tool,
            get_webhook_tool,
            list_apps_tool,
            get_app_tool,
            connect_app_tool
        ]
    
    @log_operation(level="INFO", include_timing=True)
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name with arguments.
        
        This method implements the tool dispatch pattern using
        the Factory pattern for service creation.
        """
        logger = logger_var.get()
        
        try:
            # Extract service type from tool name
            service_type = self._get_service_type_from_tool(name)
            
            # Get service from factory
            service = self.component_factory.create_component("service", service_type)
            
            # Execute operation
            result = await service.execute_operation(name, arguments)
            
            logger.info(f"Tool '{name}' executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def _get_service_type_from_tool(self, tool_name: str) -> str:
        """Get service type from tool name."""
        tool_service_mapping = {
            # Workflow tools
            "list_workflows": "workflow",
            "get_workflow": "workflow",
            "create_workflow": "workflow",
            "update_workflow": "workflow",
            "delete_workflow": "workflow",
            "trigger_workflow": "workflow",
            
            # Task tools
            "list_tasks": "task",
            "get_task": "task",
            
            # Webhook tools
            "list_webhooks": "webhook",
            "create_webhook": "webhook",
            "get_webhook": "webhook",
            
            # App tools
            "list_apps": "app",
            "get_app": "app",
            "connect_app": "app"
        }
        
        return tool_service_mapping.get(tool_name, "workflow")
    
    def get_tools(self) -> List[Tool]:
        """Get list of available tools."""
        return self.tools


# Global server instance
server_instance = ZapierMCPServer()


async def main():
    """Main function to run the MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Zapier MCP Server with Design Pattern Architecture")
    
    # Create MCP server
    server = Server("zapier")
    
    # Add tools to server
    for tool in server_instance.get_tools():
        server.list_tools().append(tool)
    
    # Add tool call handler
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls using the design pattern architecture."""
        return await server_instance.call_tool(name, arguments)
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.list_tools(),
            server.list_resources(),
        )


if __name__ == "__main__":
    asyncio.run(main()) 