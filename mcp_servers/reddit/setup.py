#!/usr/bin/env python3
"""
Setup script for Reddit MCP Server
Helps with installation and configuration
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✓ Created .env file from template")
        print("⚠️  Please edit .env file with your Reddit API credentials")
        return True
    elif env_file.exists():
        print("✓ .env file already exists")
        return False
    else:
        print("✗ .env.example file not found")
        return False


def install_dependencies():
    """Install required dependencies."""
    try:
        print("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def validate_env_file():
    """Check if .env file has required variables."""
    env_file = Path(".env")
    if not env_file.exists():
        return False
    
    content = env_file.read_text()
    required_vars = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
    
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=your_" in content:
            print(f"⚠️  {var} not configured in .env file")
            return False
    
    print("✓ Environment variables configured")
    return True


def test_server():
    """Test if the server can start."""
    try:
        print("Testing server startup...")
        # Import here to avoid issues if dependencies aren't installed
        from main import RedditConfig
        config = RedditConfig()
        print("✓ Server configuration valid")
        return True
    except Exception as e:
        print(f"✗ Server test failed: {e}")
        return False


def main():
    """Main setup process."""
    print("Reddit MCP Server Setup")
    print("=" * 30)
    
    # Check Python version
    check_python_version()
    
    # Create .env file
    env_created = create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # If we created a new .env file, remind user to configure it
    if env_created:
        print("\nNext steps:")
        print("1. Edit the .env file with your Reddit API credentials")
        print("2. Get Reddit API credentials from https://www.reddit.com/prefs/apps")
        print("3. Run 'python main.py' to start the server")
        print("\nTo get Reddit credentials:")
        print("- Go to https://www.reddit.com/prefs/apps")
        print("- Click 'Create App' or 'Create Another App'")
        print("- Choose 'script' type")
        print("- Copy the client ID and secret")
    else:
        # Validate existing configuration
        if validate_env_file():
            # Test server
            if test_server():
                print("\n✅ Setup complete! You can now run:")
                print("   python main.py")
            else:
                print("\n⚠️  Setup complete but server test failed")
                print("   Please check your .env configuration")
        else:
            print("\n⚠️  Please configure your .env file with Reddit API credentials")
    
    print("\nFor more help, see README.md")


if __name__ == "__main__":
    main()