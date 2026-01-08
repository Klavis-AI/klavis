from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/photoslibrary',
    'https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata',
    'https://www.googleapis.com/auth/photoslibrary.appendonly',
    'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata',
    'https://www.googleapis.com/auth/photospicker.mediaitems.readonly'
]


flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES
)

creds = flow.run_local_server(port=0)

print("\n=== COPY THESE FIELDS INTO YOUR .env or config ===")
print("ACCESS_TOKEN:", creds.token)
print("REFRESH_TOKEN:", creds.refresh_token)
print("CLIENT_ID:", creds.client_id)
print("CLIENT_SECRET:", creds.client_secret)
print("TOKEN_URI:", creds.token_uri)
print("\n=== IMPORTANT NOTES ===")
print("1. The old 'photoslibrary' scope no longer works after March 2025")
print("2. Library API now only accesses app-created photos/albums")
print("3. Use Picker API for accessing user's full photo library")
print("4. You'll need to re-authorize to get the new Picker API permissions")