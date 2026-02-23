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
            if "private_key_content" in self.connection_config:
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import serialization

                private_key_str = self.connection_config["private_key_content"]
                private_key_pass = self.connection_config.get("private_key_passphrase")

                if "\\n" in private_key_str:
                    private_key_str = private_key_str.replace("\\n", "\n")

                p_key = serialization.load_pem_private_key(
                    private_key_str.encode("utf-8"),
                    password=private_key_pass.encode() if private_key_pass else None,
                    backend=default_backend()
                )

                pkb = p_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                

                # Replace private_key_content with the actual key bytes
                self.connection_config["private_key"] = pkb
                del self.connection_config["private_key_content"]
                if "private_key_passphrase" in self.connection_config:
                    del self.connection_config["private_key_passphrase"]
            
            # Create session without setting specific database and schema
            self.session = Session.builder.configs(self.connection_config).create()

            # Set initial warehouse if provided, but don't set database or schema
            if "warehouse" in self.connection_config:
                self.session.sql(f"USE WAREHOUSE {self.connection_config['warehouse'].upper()}")

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
            result = self.session.sql(query).collect()
            
            result_rows = [row.asDict() for row in result] if result else []
            data_id = str(uuid.uuid4())

            return result_rows, data_id

        except Exception as e:
            logger.error(f'Database error executing "{query}": {e}')
            raise

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

    def close(self):
        """Close the Snowflake session"""
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.warning(f"Error closing Snowflake session: {e}")
            finally:
                self.session = None
