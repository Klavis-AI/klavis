import asyncio
import os
import logging
from dotenv import load_dotenv
import snowflake.connector

# Ensure we can import from src
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from mcp_snowflake_server.db_client import SnowflakeDB

# Configure logging to see detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_snowflake_server")

async def test_connection():
    load_dotenv()
    
    print("\n--- Testing Snowflake Connection ---\n")
    
    # 1. Gather connection params
    connection_config = {}
    
    # Map from env vars (supporting multiple common names)
    env_map = {
        "account": ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_ACCOUNT_ID"],
        "user": ["SNOWFLAKE_USER", "SNOWFLAKE_USERNAME", "USER"], 
        "role": ["SNOWFLAKE_ROLE"],
        "warehouse": ["SNOWFLAKE_WAREHOUSE"],
        "database": ["SNOWFLAKE_DATABASE", "SNOWFLAKE_DB"],
        "schema": ["SNOWFLAKE_SCHEMA"],
    }
    
    missing_keys = []
    
    for key, env_vars in env_map.items():
        val = None
        for var in env_vars:
            val = os.getenv(var)
            if val:
                # Mask value for security in logs
                masked = val[:2] + "***" + val[-2:] if len(val) > 4 else "***"
                print(f"✅ Found {key:<10} in {var:<20} : {masked}")
                break
        
        if val:
            connection_config[key] = val
        else:
            print(f"❌ Missing {key:<10} (checked {', '.join(env_vars)})")
            missing_keys.append(key)

    # 2. Handle private key specially
    private_key = os.getenv("SNOWFLAKE_PRIVATE_KEY")
    if private_key:
        print(f"✅ Found private_key in SNOWFLAKE_PRIVATE_KEY (len={len(private_key)})")
        connection_config["private_key_content"] = private_key
    else:
        print("❌ Missing private_key (checked SNOWFLAKE_PRIVATE_KEY)")
        missing_keys.append("private_key")

    if missing_keys:
        print(f"\n❌ Cannot attempt connection due to missing configuration: {missing_keys}")
        return

    print(f"\nAttempting to connect with config keys: {list(connection_config.keys())}")
    
    try:
        # 3. Create DB instance
        db = SnowflakeDB(connection_config)
        
        # 4. Initialize (this handles the private key parsing)
        print("Initializing database connection...")
        await db._init_database()
        print("✅ Connection initialized successfully!")
        
        # 5. Run a test query
        print("Running test query...")
        query = "SELECT CURRENT_VERSION(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
        results, _ = await db.execute_query(query)
        print("\n✅ Query Results:")
        for row in results:
            print(row)
            
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        # print full traceback if needed
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
