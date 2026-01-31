import { google } from 'googleapis';
import { authenticate } from '@google-cloud/local-auth';
import { writeFileSync } from 'fs';
import { join } from 'path';

const SCOPES = [
  'https://www.googleapis.com/auth/gmail.modify',
  'https://www.googleapis.com/auth/calendar',
  'https://www.googleapis.com/auth/gmail.send'
];

async function getRefreshToken() {
  try {
    // Authenticate using local OAuth client
    const auth = await authenticate({
      scopes: SCOPES,
      keyfilePath: join(process.cwd(), 'credentials.json')
    });

    // Get credentials including refresh token
    const credentials = auth.credentials;
    
    console.log('\nRefresh Token:', credentials.refresh_token);
    console.log('\nClient ID:', credentials.client_id);
    console.log('\nClient Secret:', credentials.client_secret);

    // Save credentials to a file
    writeFileSync('token.json', JSON.stringify(credentials, null, 2));
    console.log('\nCredentials saved to token.json');
    
  } catch (error) {
    console.error('Error getting refresh token:', error);
  }
}

getRefreshToken();
