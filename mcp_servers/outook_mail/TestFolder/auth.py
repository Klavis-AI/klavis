import os
import webbrowser
import msal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

APPLICATION_ID = os.getenv("APPLICATION_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = ['Mail.Read', 'Mail.ReadWrite', 'MailboxSettings.Read', 'MailboxSettings.ReadWrite','Mail.Send']
REDIRECT_URI = 'http://localhost:8000/'

MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

authorization_code = None  # global to store the code

class AuthorizationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_code
        query = urlparse(self.path).query
        params = parse_qs(query)
        if 'code' in params:
            authorization_code = params['code'][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Authorization code received. You can close this window.')
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Authorization code not found in the URL.')

def get_access_token(application_id, client_secret, scopes):
    client = msal.ConfidentialClientApplication(
        client_id=application_id,
        client_credential=client_secret,
        authority='https://login.microsoftonline.com/consumers/'
    )

    # Get auth URL
    auth_request_url = client.get_authorization_request_url(scopes, redirect_uri=REDIRECT_URI)

    # Open browser
    webbrowser.open(auth_request_url)

    # Start HTTP server to catch the code
    print("Waiting for authorization code...")
    httpd = HTTPServer(('localhost', 8000), AuthorizationHandler)
    while not authorization_code:
        httpd.handle_request()  # handle one request at a time until code received

    # Exchange code for token
    token_response = client.acquire_token_by_authorization_code(
        code=authorization_code,
        scopes=scopes,
        redirect_uri=REDIRECT_URI
    )

    if 'access_token' in token_response:
        return token_response['access_token']
    else:
        raise Exception('Failed to acquire access token: ' + str(token_response))

def main():
    try:
        access_token = get_access_token(
            application_id=APPLICATION_ID,
            client_secret=CLIENT_SECRET,
            scopes=SCOPES
        )

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        print("Access token acquired!")
        print(headers)

    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    main()