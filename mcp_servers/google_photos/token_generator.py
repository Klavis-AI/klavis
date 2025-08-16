from google_auth_oauthlib.flow import InstalledAppFlow

# Updated scopes for Google Photos APIs (post-March 2025 changes)
SCOPES = [
    # Legacy Library API scopes (REMOVED - these no longer work after March 2025)
    # 'https://www.googleapis.com/auth/photoslibrary',  # REMOVED
    # 'https://www.googleapis.com/auth/photoslibrary.readonly',  # REMOVED
    # 'https://www.googleapis.com/auth/photoslibrary.sharing',  # REMOVED
    
    # Current working Library API scopes (for app-created content only)
    'https://www.googleapis.com/auth/photoslibrary',
    'https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata',  # Read app-created photos/albums
    'https://www.googleapis.com/auth/photoslibrary.appendonly',               # Upload photos and create albums
    'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata',     # Edit app-created content
    
    # NEW: Google Photos Picker API scope (for accessing user's full library)
    'https://www.googleapis.com/auth/photospicker.mediaitems.readonly'       # Access user-selected photos via Picker API
]

# Use your downloaded credentials.json
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES
)

# Start local OAuth flow
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