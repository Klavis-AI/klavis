# Import necessary Python standard libraries
import os          
import json        
import subprocess  
import sys         
import shutil     
import platform

def check_prerequisites():
    """
    Check if necessary prerequisites are installed
    
    Returns:
        tuple: (python_ok, uv_installed, uvx_installed, word_server_installed)
    """
    # Check Python version
    python_version = sys.version_info
    python_ok = python_version.major >= 3 and python_version.minor >= 8
    
    # Check if uv/uvx is installed
    uv_installed = shutil.which("uv") is not None
    uvx_installed = shutil.which("uvx") is not None
    
    # Check if word-document-server is already installed via pip
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "word-document-server"],
            capture_output=True,
            text=True,
            check=False
        )
        word_server_installed = result.returncode == 0
    except Exception:
        word_server_installed = False
        
    return (python_ok, uv_installed, uvx_installed, word_server_installed)

def get_transport_choice():
    """
    Ask user to choose transport type
    
    Returns:
        dict: Transport configuration
    """
    print("\nTransport Configuration:")
    print("1. STDIO (default, local execution)")
    print("2. Streamable HTTP (modern, recommended for web deployment)")
    print("3. SSE (Server-Sent Events, for compatibility)")
    
    choice = input("\nSelect transport type (1-3, default: 1): ").strip()
    
    if choice == "2":
        host = input("Host (default: 127.0.0.1): ").strip() or "127.0.0.1"
        port = input("Port (default: 8000): ").strip() or "8000"
        path = input("Path (default: /mcp): ").strip() or "/mcp"
        
        return {
            "transport": "streamable-http",
            "host": host,
            "port": port,
            "path": path
        }
    elif choice == "3":
        host = input("Host (default: 127.0.0.1): ").strip() or "127.0.0.1"
        port = input("Port (default: 8000): ").strip() or "8000"
        sse_path = input("SSE Path (default: /sse): ").strip() or "/sse"
        
        return {
            "transport": "sse",
            "host": host,
            "port": port,
            "sse_path": sse_path
        }
    else:
        # Default to stdio
        return {
            "transport": "stdio"
        }

def setup_venv():
    """
    Function to set up Python virtual environment
    
    Features:
    - Checks if Python version meets requirements (3.8+)
    - Creates Python virtual environment (if it doesn't exist)
    - Installs required dependencies in the newly created virtual environment
    
    No parameters required
    
    Returns: Path to Python interpreter in the virtual environment
    """
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    
    # Get absolute path of the directory containing the current script
    base_path = os.path.abspath(os.path.dirname(__file__))
    # Set virtual environment directory path
    venv_path = os.path.join(base_path, '.venv')
    
    # Determine pip and python executable paths based on operating system
    is_windows = platform.system() == "Windows"
    if is_windows:
        pip_path = os.path.join(venv_path, 'Scripts', 'pip.exe')
        python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
    else:
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        python_path = os.path.join(venv_path, 'bin', 'python')
    
    # Check if virtual environment already exists and is valid
    venv_exists = os.path.exists(venv_path)
    pip_exists = os.path.exists(pip_path)
    
    if not venv_exists or not pip_exists:
        print("Creating new virtual environment...")
        # Remove existing venv if it's invalid
        if venv_exists and not pip_exists:
            print("Existing virtual environment is incomplete, recreating it...")
            try:
                shutil.rmtree(venv_path)
            except Exception as e:
                print(f"Warning: Could not remove existing virtual environment: {e}")
                print("Please delete the .venv directory manually and try again.")
                sys.exit(1)
        
        # Create virtual environment
        try:
            subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)
            print("Virtual environment created successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}")
            sys.exit(1)
    else:
        print("Valid virtual environment already exists.")
    
    # Double-check that pip exists after creating venv
    if not os.path.exists(pip_path):
        print(f"Error: pip executable not found at {pip_path}")
        print("Try creating the virtual environment manually with: python -m venv .venv")
        sys.exit(1)
    
    # Install or update dependencies
    print("\nInstalling requirements...")
    try:
        # Install FastMCP package (standalone library)
        subprocess.run([pip_path, 'install', 'fastmcp'], check=True)
        # Install python-docx package
        subprocess.run([pip_path, 'install', 'python-docx'], check=True)
        
        # Also install dependencies from requirements.txt if it exists
        requirements_path = os.path.join(base_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            subprocess.run([pip_path, 'install', '-r', requirements_path], check=True)
        
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Could not execute {pip_path}")
        print("Try activating the virtual environment manually and installing requirements:")
        if is_windows:
            print(f".venv\\Scripts\\activate")
        else:
            print("source .venv/bin/activate")
        print("pip install mcp[cli] python-docx")
        sys.exit(1)
    
    return python_path

def generate_mcp_config_local(python_path, transport_config):
    """
    Generate MCP configuration for locally installed word-document-server
    
    Parameters:
    - python_path: Path to Python interpreter in the virtual environment
    - transport_config: Transport configuration dictionary
    
    Returns: Path to the generated config file
    """
    # Get absolute path of the directory containing the current script
    base_path = os.path.abspath(os.path.dirname(__file__))
    
    # Path to Word Document Server script
    server_script_path = os.path.join(base_path, 'word_mcp_server.py')
    
    # Build environment variables
    env = {
        "PYTHONPATH": base_path,
        "MCP_TRANSPORT": transport_config["transport"]
    }
    
    # Add transport-specific environment variables
    if transport_config["transport"] == "streamable-http":
        env.update({
            "MCP_HOST": transport_config["host"],
            "MCP_PORT": transport_config["port"],
            "MCP_PATH": transport_config["path"]
        })
    elif transport_config["transport"] == "sse":
        env.update({
            "MCP_HOST": transport_config["host"],
            "MCP_PORT": transport_config["port"],
            "MCP_SSE_PATH": transport_config["sse_path"]
        })
    # For stdio transport, no additional environment variables needed
    
    # Create MCP configuration dictionary
    config = {
        "mcpServers": {
            "word-document-server": {
                "command": python_path,
                "args": [server_script_path],
                "env": env
            }
        }
    }
    
    # Save configuration to JSON file
    config_path = os.path.join(base_path, 'mcp-config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def generate_mcp_config_uvx(transport_config):
    """
    Generate MCP configuration for PyPI-installed word-document-server using UVX
    
    Parameters:
    - transport_config: Transport configuration dictionary
    
    Returns: Path to the generated config file
    """
    # Get absolute path of the directory containing the current script
    base_path = os.path.abspath(os.path.dirname(__file__))
    
    # Build environment variables
    env = {
        "MCP_TRANSPORT": transport_config["transport"]
    }
    
    # Add transport-specific environment variables
    if transport_config["transport"] == "streamable-http":
        env.update({
            "MCP_HOST": transport_config["host"],
            "MCP_PORT": transport_config["port"],
            "MCP_PATH": transport_config["path"]
        })
    elif transport_config["transport"] == "sse":
        env.update({
            "MCP_HOST": transport_config["host"],
            "MCP_PORT": transport_config["port"],
            "MCP_SSE_PATH": transport_config["sse_path"]
        })
    # For stdio transport, no additional environment variables needed
    
    # Create MCP configuration dictionary
    config = {
        "mcpServers": {
            "word-document-server": {
                "command": "uvx",
                "args": ["--from", "word-mcp-server", "word_mcp_server"],
                "env": env
            }
        }
    }
    
    # Save configuration to JSON file
    config_path = os.path.join(base_path, 'mcp-config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def generate_mcp_config_module(transport_config):
    """
    Generate MCP configuration for PyPI-installed word-document-server using Python module
    
    Parameters:
    - transport_config: Transport configuration dictionary
    
    Returns: Path to the generated config file
    """
    # Get absolute path of the directory containing the current script
    base_path = os.path.abspath(os.path.dirname(__file__))
    
    # Build environment variables
    env = {
        "MCP_TRANSPORT": transport_config["transport"]
    }
    
    # Add transport-specific environment variables
    if transport_config["transport"] == "streamable-http":
        env.update({
            "MCP_HOST": transport_config["host"],
            "MCP_PORT": transport_config["port"],
            "MCP_PATH": transport_config["path"]
        })
    elif transport_config["transport"] == "sse":
        env.update({
            "MCP_HOST": transport_config["host"],
            "MCP_PORT": transport_config["port"],
            "MCP_SSE_PATH": transport_config["sse_path"]
        })

    
    # Create MCP configuration dictionary
    config = {
        "mcpServers": {
            "word-document-server": {
                "command": sys.executable,
                "args": ["-m", "word_document_server"],
                "env": env
            }
        }
    }
    
    # Save configuration to JSON file
    config_path = os.path.join(base_path, 'mcp-config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def install_from_pypi():
    """
    Install word-document-server from PyPI
    
    Returns: True if successful, False otherwise
    """
    print("\nInstalling word-document-server from PyPI...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "word-mcp-server"], check=True)
        print("word-mcp-server successfully installed from PyPI!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install word-mcp-server from PyPI.")
        return False

def print_config_instructions(config_path, transport_config):
    """
    Print instructions for using the generated config
    
    Parameters:
    - config_path: Path to the generated config file
    - transport_config: Transport configuration dictionary
    """
    print(f"\nMCP configuration has been written to: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("\nMCP configuration for Claude Desktop:")
    print(json.dumps(config, indent=2))
    
    # Print transport-specific instructions
    if transport_config["transport"] == "streamable-http":
        print(f"\n📡 Streamable HTTP Transport Configuration:")
        print(f"   Server will be accessible at: http://{transport_config['host']}:{transport_config['port']}{transport_config['path']}")
        print(f"   \n   To test the server manually:")
        print(f"   curl -X POST http://{transport_config['host']}:{transport_config['port']}{transport_config['path']}")
        
    elif transport_config["transport"] == "sse":
        print(f"\n📡 SSE Transport Configuration:")
        print(f"   Server will be accessible at: http://{transport_config['host']}:{transport_config['port']}{transport_config['sse_path']}")
        print(f"   \n   To test the server manually:")
        print(f"   curl http://{transport_config['host']}:{transport_config['port']}{transport_config['sse_path']}")
        
    else:  # stdio
        print(f"\n💻 STDIO Transport Configuration:")
        print(f"   Server runs locally with standard input/output")
    
    # Provide instructions for adding configuration to Claude Desktop configuration file
    if platform.system() == "Windows":
        claude_config_path = os.path.expandvars("%APPDATA%\\Claude\\claude_desktop_config.json")
    else:  # macOS
        claude_config_path = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    
    print(f"\nTo use with Claude Desktop, merge this configuration into: {claude_config_path}")

def create_package_structure():
    """
    Create necessary package structure and environment files
    """
    # Get absolute path of the directory containing the current script
    base_path = os.path.abspath(os.path.dirname(__file__))
    
    # Create __init__.py file
    init_path = os.path.join(base_path, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('# Word Document MCP Server')
        print(f"Created __init__.py at: {init_path}")
    
    # Create requirements.txt file
    requirements_path = os.path.join(base_path, 'requirements.txt')
    if not os.path.exists(requirements_path):
        with open(requirements_path, 'w') as f:
            f.write('fastmcp\npython-docx\nmsoffcrypto-tool\ndocx2pdf\nhttpx\ncryptography\n')
        print(f"Created requirements.txt at: {requirements_path}")
    
    # Create .env.example file
    env_example_path = os.path.join(base_path, '.env.example')
    if not os.path.exists(env_example_path):
        with open(env_example_path, 'w') as f:
            f.write("""# Transport Configuration
# Valid options: stdio, streamable-http, sse
MCP_TRANSPORT=stdio

# HTTP/SSE Configuration (when not using stdio)
MCP_HOST=127.0.0.1
MCP_PORT=8000

# Streamable HTTP specific
MCP_PATH=/mcp

# SSE specific  
MCP_SSE_PATH=/sse

""")
        print(f"Created .env.example at: {env_example_path}")

# Main execution entry point
if __name__ == '__main__':
    # Check prerequisites
    python_ok, uv_installed, uvx_installed, word_server_installed = check_prerequisites()
    
    if not python_ok:
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    
    print("Word Document MCP Server Setup (Multi-Transport)")
    print("===============================================\n")
    
    # Create necessary files
    create_package_structure()
    
    # Get transport configuration
    transport_config = get_transport_choice()
    
    # If word-document-server is already installed, offer config options
    if word_server_installed:
        print("word-document-server is already installed via pip.")
        
        if uvx_installed:
            print("\nOptions:")
            print("1. Generate MCP config for UVX (recommended)")
            print("2. Generate MCP config for Python module")
            print("3. Set up local development environment")
            
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                config_path = generate_mcp_config_uvx(transport_config)
                print_config_instructions(config_path, transport_config)
            elif choice == "2":
                config_path = generate_mcp_config_module(transport_config)
                print_config_instructions(config_path, transport_config)
            elif choice == "3":
                python_path = setup_venv()
                config_path = generate_mcp_config_local(python_path, transport_config)
                print_config_instructions(config_path, transport_config)
            else:
                print("Invalid choice. Exiting.")
                sys.exit(1)
        else:
            print("\nOptions:")
            print("1. Generate MCP config for Python module")
            print("2. Set up local development environment")
            
            choice = input("\nEnter your choice (1-2): ")
            
            if choice == "1":
                config_path = generate_mcp_config_module(transport_config)
                print_config_instructions(config_path, transport_config)
            elif choice == "2":
                python_path = setup_venv()
                config_path = generate_mcp_config_local(python_path, transport_config)
                print_config_instructions(config_path, transport_config)
            else:
                print("Invalid choice. Exiting.")
                sys.exit(1)
    
    # If word-document-server is not installed, offer installation options
    else:
        print("word-document-server is not installed.")
        
        print("\nOptions:")
        print("1. Install from PyPI (recommended)")
        print("2. Set up local development environment")
        
        choice = input("\nEnter your choice (1-2): ")
        
        if choice == "1":
            if install_from_pypi():
                if uvx_installed:
                    print("\nNow generating MCP config for UVX...")
                    config_path = generate_mcp_config_uvx(transport_config)
                else:
                    print("\nUVX not found. Generating MCP config for Python module...")
                    config_path = generate_mcp_config_module(transport_config)
                print_config_instructions(config_path, transport_config)
        elif choice == "2":
            python_path = setup_venv()
            config_path = generate_mcp_config_local(python_path, transport_config)
            print_config_instructions(config_path, transport_config)
        else:
            print("Invalid choice. Exiting.")
            sys.exit(1)
    
    print("\nSetup complete! You can now use the Word Document MCP server with compatible clients like Claude Desktop.")
    print("\nTransport Summary:")
    print(f"  - Transport: {transport_config['transport']}")
    if transport_config['transport'] != 'stdio':
        print(f"  - Host: {transport_config.get('host', 'N/A')}")
        print(f"  - Port: {transport_config.get('port', 'N/A')}")
        if transport_config['transport'] == 'streamable-http':
            print(f"  - Path: {transport_config.get('path', 'N/A')}")
        elif transport_config['transport'] == 'sse':
            print(f"  - SSE Path: {transport_config.get('sse_path', 'N/A')}")