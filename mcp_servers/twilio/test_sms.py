#!/usr/bin/env python3
"""
Simple test script for Twilio MCP Server
"""

import requests
import json
import sys

def test_list_phone_numbers():
    """Test listing phone numbers"""
    url = "http://localhost:5001/http"
    headers = {
        "Content-Type": "application/json",
        "x-auth-token": "env"
    }
    
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "twilio_list_phone_numbers",
            "arguments": {}
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print("✅ List Phone Numbers Response:")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ Error testing list phone numbers: {e}")
        return False

def test_send_sms(to_number, message):
    """Test sending an SMS"""
    url = "http://localhost:5001/http"
    headers = {
        "Content-Type": "application/json",
        "x-auth-token": "env"
    }
    
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "twilio_send_sms",
            "arguments": {
                "to": to_number,
                "body": message
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print("✅ Send SMS Response:")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ Error testing send SMS: {e}")
        return False

def test_list_messages():
    """Test listing messages"""
    url = "http://localhost:5001/http"
    headers = {
        "Content-Type": "application/json",
        "x-auth-token": "env"
    }
    
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "twilio_list_messages",
            "arguments": {
                "limit": 5
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print("✅ List Messages Response:")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ Error testing list messages: {e}")
        return False

def main():
    print("🚀 Testing Twilio MCP Server")
    print("=" * 50)
    
    # Test 1: List phone numbers
    print("\n1. Testing list phone numbers...")
    if not test_list_phone_numbers():
        print("❌ Server might not be running or there's an issue")
        sys.exit(1)
    
    # Test 2: List messages
    print("\n2. Testing list messages...")
    test_list_messages()
    
    # Test 3: Send SMS (if number provided)
    if len(sys.argv) > 2:
        to_number = sys.argv[1]
        message = sys.argv[2]
        print(f"\n3. Testing send SMS to {to_number}...")
        test_send_sms(to_number, message)
    else:
        print("\n3. Skipping SMS test (provide phone number and message as arguments)")
        print("   Usage: python3 test_sms.py +1234567890 'Test message'")
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    main() 