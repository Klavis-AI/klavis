import asyncio
from server import main as server_main 

def main():
    """Main entry point for the package."""
    asyncio.run(server_main())

__all__ = ['main']
