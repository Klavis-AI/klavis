import requests
import os
import random
import string
from typing import Any, Dict, Optional
import base64
from dotenv import load_dotenv


load_dotenv()

FRESHDESK_API_KEY = os.getenv("FRESHDESK_API_KEY")
if not FRESHDESK_API_KEY:
    raise ValueError("FRESHDESK_API_KEY environment variable is required")


FRESHDESK_DOMAIN = os.getenv("FRESHDESK_DOMAIN")
if not FRESHDESK_DOMAIN:
    raise ValueError("FRESHDESK_DOMAIN environment variable is required")


FRESHDESK_API_BASE = f"https://{FRESHDESK_DOMAIN}.freshdesk.com/api/v2"


def gen_random_password(length: int = 10) -> str:
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def make_freshdesk_request(
    method: str, 
    endpoint: str, 
    data: Optional[Dict] = None,
    options: Optional[Dict] = None,
) -> Any:
    """Make an HTTP request to the Freshdesk API.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        endpoint: API endpoint (e.g., '/tickets')
        data: Optional request payload as a dictionary
        options: Optional request options as a dictionary
            timeout: Request timeout in seconds (default: 10)
            use_pwd: Use basic authentication with a random password (default: True)
            query_params: Optional query parameters as a dictionary
            headers: Optional headers as a dictionary
            files: Optional files as a dictionary
        
    Returns:
        Parsed JSON response from the API
        
    Raises:
        ValueError: For invalid input parameters
        requests.exceptions.RequestException: For HTTP and connection errors
        json.JSONDecodeError: If response cannot be parsed as JSON
    """
    if not isinstance(method, str) or not method.strip():
        raise ValueError("HTTP method must be a non-empty string")
    
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ValueError("Endpoint must be a non-empty string")
    
    if data is not None and not isinstance(data, dict):
        raise ValueError("Data must be a dictionary or None")
    
    url = f"{FRESHDESK_API_BASE}{endpoint}"


    timeout = int(options.get("timeout", 10))
    use_pwd = options.get("use_pwd", True)
    query_params = options.get("query_params", {})
    extra_headers = options.get("headers", {})
    
    headers = {
        "Content-Type": "application/json",
        **extra_headers,
    }

    random_password = gen_random_password()

    request_args = {}

    if query_params:
        request_args["params"] = query_params

    if not use_pwd:
        api_key = base64.b64encode(f"{FRESHDESK_API_KEY}:{random_password}").decode("utf-8")
        headers["Authorization"] = f"{api_key}"
    else:
        request_args["auth"] = (FRESHDESK_API_KEY, random_password)
    
    try:
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            timeout=timeout,
            **request_args,
        )
        
        # Log response status for debugging
        print(f"Freshdesk API {method.upper()} {endpoint} - Status: {response.status_code}")
        
        # Raise HTTPError for 4XX/5XX responses
        response.raise_for_status()
        
        # Handle empty responses (e.g., 204 No Content)
        if not response.content:
            return {}
            
        return response.json()
        
    except requests.exceptions.Timeout as e:
        raise requests.exceptions.Timeout(f"Request to Freshdesk API timed out after {timeout} seconds") from e
        
    except requests.exceptions.TooManyRedirects as e:
        raise requests.exceptions.TooManyRedirects("Too many redirects while connecting to Freshdesk API") from e
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to Freshdesk API: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_msg = f"Freshdesk API Error ({e.response.status_code}): {error_details.get('message', 'No error details')}"
            except ValueError:
                error_msg = f"Freshdesk API Error ({e.response.status_code}): {e.response.text or 'No error details'}"
        raise requests.exceptions.RequestException(error_msg) from e
        
    except ValueError as e:
        raise ValueError(f"Failed to parse JSON response from Freshdesk API: {str(e)}") from e


def handle_freshdesk_error(e: Exception, operation: str, object_type: str = "") -> Dict[str, Any]:
    """Handle Freshdesk errors and return a standardized error response.
    
    Args:
        e: The exception that was raised
        operation: The operation being performed (e.g., 'create', 'update', 'delete')
        object_type: The type of object being operated on (e.g., 'ticket', 'contact')
        
    Returns:
        A dictionary containing error details with the following structure:
        {
            'success': False,
            'error': {
                'code': 'error_code',
                'message': 'Human-readable error message',
                'details': [
                    {'field': 'field_name', 'message': 'Error message', 'code': 'error_code'}
                ]
            }
        }
    """
    error_response = {
        'success': False,
        'error': {
            'code': 'unknown_error',
            'message': f"An unexpected error occurred while {operation}ing {object_type}",
            'details': []
        }
    }
    
    # Handle requests.exceptions.RequestException and its subclasses
    if isinstance(e, requests.exceptions.RequestException):
        error_response['error']['code'] = 'request_error'
        
        # Handle HTTP errors (4XX, 5XX)
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            
            # Map status codes to error codes
            status_to_code = {
                400: 'invalid_request',
                401: 'authentication_failed',
                403: 'access_denied',
                404: 'not_found',
                405: 'method_not_allowed',
                406: 'unsupported_accept_header',
                409: 'conflict',
                415: 'unsupported_content_type',
                429: 'rate_limit_exceeded',
                500: 'server_error'
            }
            
            error_code = status_to_code.get(status_code, f'http_error_{status_code}')
            error_response['error']['code'] = error_code
            
            # Try to extract error details from the response
            try:
                if e.response.content:
                    error_data = e.response.json()
                    error_response['error']['message'] = error_data.get('description', 
                        f"Freshdesk API returned status {status_code}")
                    
                    # Add field-level errors if available
                    if 'errors' in error_data and isinstance(error_data['errors'], list):
                        for err in error_data['errors']:
                            error_detail = {
                                'field': err.get('field', ''),
                                'message': err.get('message', 'Validation error'),
                                'code': err.get('code', 'validation_error')
                            }
                            error_response['error']['details'].append(error_detail)
                    
                    # If no field errors but there's a message, use it
                    elif not error_response['error']['details'] and 'message' in error_data:
                        error_response['error']['details'].append({
                            'message': error_data['message'],
                            'code': error_code
                        })
            except ValueError:
                # If we can't parse JSON, use the response text
                error_response['error']['message'] = f"Freshdesk API error: {e.response.text}"
        else:
            # Handle connection errors, timeouts, etc.
            if isinstance(e, requests.exceptions.Timeout):
                error_response['error'].update({
                    'code': 'request_timeout',
                    'message': 'The request to Freshdesk API timed out'
                })
            elif isinstance(e, requests.exceptions.ConnectionError):
                error_response['error'].update({
                    'code': 'connection_error',
                    'message': 'Could not connect to Freshdesk API'
                })
            else:
                error_response['error'].update({
                    'code': 'request_failed',
                    'message': f"Request to Freshdesk API failed: {str(e)}"
                })
    
    # Handle JSON decode errors
    elif isinstance(e, ValueError) and 'JSON' in str(e):
        error_response['error'].update({
            'code': 'invalid_json',
            'message': 'Received invalid JSON response from Freshdesk API'
        })
    
    # Handle other unexpected errors
    else:
        error_response['error'].update({
            'code': 'unexpected_error',
            'message': f"An unexpected error occurred: {str(e)}"
        })
    
    # Add operation and object type context to the error message
    if object_type:
        error_response['error']['message'] = f"Failed to {operation} {object_type}: {error_response['error']['message']}"
    else:
        error_response['error']['message'] = f"Failed to {operation}: {error_response['error']['message']}"
    
    return error_response


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}
    