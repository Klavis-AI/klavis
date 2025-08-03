# MCP Server for Twilio

This project is a Model Context Protocol (MCP) server for the Twilio API. It allows a Large Language Model (LLM) to interact with Twilio to perform communication tasks.

# Core Functionality

This server provides atomic tools for interacting with the Twilio API. The initial tool implemented is:

*   **`send_sms`**: Sends an SMS message to a specified recipient.

# Setup and Installation

# 1. Prerequisites

*   Python 3.7+
*   A Twilio account with a provisioned phone number.

# 2. Clone the Repository and Install Dependencies

First, set up a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`