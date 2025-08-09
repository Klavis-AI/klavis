import asyncio
import logging
import time
import uuid
from typing import Any

from snowflake.snowpark import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("mcp_snowflake_server")


class SnowflakeDB:
    AUTH_EXPIRATION_TIME = 1800

    def __init__(self, connection_config: dict):
        self.connection_config = connection_config
        self.session = None
        self.insights: list[str] = []
        self.auth_time = 0
        self.init_task = None  # To store the task reference

    async def _init_database(self):
        """Initialize connection to the Snowflake database"""
        try:
            # Handle private key authentication
            if "private_key_path" in self.connection_config:
                from cryptography.hazmat.primitives import serialization
                with open(self.connection_config["private_key_path"], "rb") as key_file:
                    p_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None  # If your key is password protected, you'll need to provide it
                    )

                pkb = p_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )

                # Replace private_key_path with the actual key content
                self.connection_config["private_key"] = pkb
                del self.connection_config["private_key_path"]

            # Create session without setting specific database and schema
            self.session = Session.builder.configs(
                self.connection_config).create()

            # Set initial warehouse if provided, but don't set database or schema
            if "warehouse" in self.connection_config:
                self.session.sql(
                    f"USE WAREHOUSE {self.connection_config['warehouse'].upper()}")

            self.auth_time = time.time()
        except Exception as e:
            raise ValueError(f"Failed to connect to Snowflake database: {e}")

    def start_init_connection(self):
        """Start database initialization in the background"""
        # Create a task that runs in the background
        loop = asyncio.get_event_loop()
        self.init_task = loop.create_task(self._init_database())
        return self.init_task

    async def execute_query(self, query: str) -> tuple[list[dict[str, Any]], str]:
        """Execute a SQL query and return results as a list of dictionaries"""
        # If init_task exists and isn't done, wait for it to complete
        if self.init_task and not self.init_task.done():
            await self.init_task
        # If session doesn't exist or has expired, initialize it and wait
        elif not self.session or time.time() - self.auth_time > self.AUTH_EXPIRATION_TIME:
            await self._init_database()

        logger.debug(f"Executing query: {query}")
        try:
            result = self.session.sql(query).to_pandas()
            result_rows = result.to_dict(orient="records")
            data_id = str(uuid.uuid4())

            return result_rows, data_id

        except Exception as e:
            error_message = str(e)

            # Enhanced error messages for common issues
            if "does not exist" in error_message.lower():
                if "database" in error_message.lower():
                    raise ValueError(
                        f"Database not found: {error_message}. Use snowflake_list_databases to see available databases.")
                elif "schema" in error_message.lower():
                    raise ValueError(
                        f"Schema not found: {error_message}. Use snowflake_list_schemas to see available schemas.")
                elif "table" in error_message.lower():
                    raise ValueError(
                        f"Table not found: {error_message}. Use snowflake_list_tables to see available tables.")
                else:
                    raise ValueError(f"Object not found: {error_message}")
            elif "permission" in error_message.lower() or "access" in error_message.lower():
                raise ValueError(
                    f"Access denied: {error_message}. Check your Snowflake role and permissions.")
            elif "syntax error" in error_message.lower():
                raise ValueError(
                    f"SQL syntax error: {error_message}. Please check your SQL syntax.")
            else:
                logger.error(f'Database error executing "{query}": {e}')
                raise ValueError(f"Database operation failed: {error_message}")

    def add_insight(self, insight: str) -> None:
        """Add a new insight to the collection"""
        self.insights.append(insight)

    def get_memo(self) -> str:
        """Generate a formatted memo from collected insights"""
        if not self.insights:
            return "No data insights have been discovered yet."

        memo = "📊 Data Intelligence Memo 📊\n\n"
        memo += "Key Insights Discovered:\n\n"
        memo += "\n".join(f"- {insight}" for insight in self.insights)

        if len(self.insights) > 1:
            memo += f"\n\nSummary:\nAnalysis has revealed {len(self.insights)} key data insights that suggest opportunities for strategic optimization and growth."

        return memo
