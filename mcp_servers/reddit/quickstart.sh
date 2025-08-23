#!/bin/bash

# Reddit MCP Server - Quick Start Script
# This script automates the setup process

set -e

echo "🚀 Reddit MCP Server Quick Start"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python $python_version detected"
}

# Check if we're in the right directory
check_directory() {
    if [[ ! -f "main.py" || ! -f "requirements.txt" ]]; then
        print_error "Please run this script from the reddit MCP server directory"
        print_info "Expected files: main.py, requirements.txt"
        exit 1
    fi
    print_status "Correct directory confirmed"
}

# Create virtual environment
setup_venv() {
    if [[ ! -d "venv" ]]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated"
}

# Install dependencies
install_deps() {
    print_info "Installing dependencies..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    print_status "Dependencies installed"
}

# Setup environment file
setup_env() {
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            print_status "Environment file created from template"
            return 1  # Indicates new file created
        else
            print_error ".env.example file not found"
            exit 1
        fi
    else
        print_status "Environment file already exists"
        return 0  # Indicates file already exists
    fi
}

# Get Reddit credentials from user
get_credentials() {
    echo ""
    print_info "Reddit API Credentials Setup"
    echo "============================================"
    echo ""
    echo "To get Reddit API credentials:"
    echo "1. Go to: https://www.reddit.com/prefs/apps"
    echo "2. Click 'Create App' or 'Create Another App'"
    echo "3. Choose 'script' as the app type"
    echo "4. Fill in the required fields"
    echo "5. Copy the client ID and secret"
    echo ""
    
    read -p "Enter your Reddit Client ID: " client_id
    read -p "Enter your Reddit Client Secret: " client_secret
    read -p "Enter your Reddit Username (optional, for posting): " username
    read -s -p "Enter your Reddit Password (optional, for posting): " password
    echo ""
    
    # Update .env file
    if [[ -n "$client_id" ]]; then
        sed -i.bak "s/REDDIT_CLIENT_ID=.*/REDDIT_CLIENT_ID=$client_id/" .env
    fi
    
    if [[ -n "$client_secret" ]]; then
        sed -i.bak "s/REDDIT_CLIENT_SECRET=.*/REDDIT_CLIENT_SECRET=$client_secret/" .env
    fi
    
    if [[ -n "$username" ]]; then
        sed -i.bak "s/REDDIT_USERNAME=.*/REDDIT_USERNAME=$username/" .env
    fi
    
    if [[ -n "$password" ]]; then
        sed -i.bak "s/REDDIT_PASSWORD=.*/REDDIT_PASSWORD=$password/" .env
    fi
    
    # Remove backup file
    rm -f .env.bak
    
    print_status "Credentials saved to .env file"
}

# Test the configuration
test_config() {
    print_info "Testing configuration..."
    
    # Check if required variables are set
    if ! grep -q "REDDIT_CLIENT_ID=your_" .env && ! grep -q "REDDIT_CLIENT_SECRET=your_" .env; then
        print_status "Configuration appears to be set up"
        
        # Test import
        if python3 -c "from main import RedditConfig; RedditConfig()" > /dev/null 2>&1; then
            print_status "Configuration test passed"
            return 0
        else
            print_error "Configuration test failed"
            return 1
        fi
    else
        print_warning "Configuration contains placeholder values"
        return 1
    fi
}

# Start the server
start_server() {
    echo ""
    print_info "Starting Reddit MCP Server..."
    print_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Activate venv and start server
    source venv/bin/activate
    python3 main.py
}

# Docker setup option
setup_docker() {
    echo ""
    print_info "Docker Setup Option"
    echo "=================="
    echo ""
    
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. Skipping Docker setup."
        return 1
    fi
    
    read -p "Do you want to build and run with Docker? (y/n): " use_docker
    
    if [[ $use_docker == "y" || $use_docker == "Y" ]]; then
        print_info "Building Docker image..."
        docker build -t reddit-mcp . > /dev/null 2>&1
        print_status "Docker image built successfully"
        
        # Get credentials for Docker
        source .env 2>/dev/null || true
        
        if [[ -n "$REDDIT_CLIENT_ID" && -n "$REDDIT_CLIENT_SECRET" ]]; then
            print_info "Starting Docker container..."
            docker run -d -p 5000:5000 \
                -e REDDIT_CLIENT_ID="$REDDIT_CLIENT_ID" \
                -e REDDIT_CLIENT_SECRET="$REDDIT_CLIENT_SECRET" \
                -e REDDIT_USERNAME="$REDDIT_USERNAME" \
                -e REDDIT_PASSWORD="$REDDIT_PASSWORD" \
                --name reddit-mcp-server \
                reddit-mcp
            
            print_status "Docker container started"
            print_info "Container name: reddit-mcp-server"
            print_info "Server running on: http://localhost:5000"
            
            echo ""
            echo "Docker commands:"
            echo "  View logs: docker logs reddit-mcp-server"
            echo "  Stop container: docker stop reddit-mcp-server"
            echo "  Remove container: docker rm reddit-mcp-server"
            
            return 0
        else
            print_error "Credentials not found in .env file"
            return 1
        fi
    fi
    
    return 1
}

# Main execution flow
main() {
    echo ""
    
    # Step 1: Basic checks
    check_python
    check_directory
    
    # Step 2: Setup virtual environment
    setup_venv
    
    # Step 3: Install dependencies
    install_deps
    
    # Step 4: Setup environment
    if setup_env; then
        # .env already exists, test it
        if ! test_config; then
            print_warning "Existing configuration may need updates"
            read -p "Do you want to update your credentials? (y/n): " update_creds
            if [[ $update_creds == "y" || $update_creds == "Y" ]]; then
                get_credentials
            fi
        fi
    else
        # New .env file created, get credentials
        get_credentials
    fi
    
    # Step 5: Final configuration test
    if test_config; then
        echo ""
        print_status "Setup completed successfully!"
        echo ""
        
        # Offer Docker option
        if ! setup_docker; then
            # If not using Docker, start normally
            read -p "Do you want to start the server now? (y/n): " start_now
            if [[ $start_now == "y" || $start_now == "Y" ]]; then
                start_server
            else
                echo ""
                print_info "To start the server later, run:"
                echo "  source venv/bin/activate"
                echo "  python3 main.py"
            fi
        fi
    else
        print_error "Setup completed but configuration test failed"
        print_info "Please check your .env file and try again"
        exit 1
    fi
}

# Handle script interruption
trap 'echo ""; print_info "Setup interrupted by user"; exit 1' INT

# Run main function
main "$@"