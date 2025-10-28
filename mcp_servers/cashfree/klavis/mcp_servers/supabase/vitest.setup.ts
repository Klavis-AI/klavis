import { config } from 'dotenv';
import { statSync } from 'fs';
import './test/extensions.js';

if (!process.env.CI) {
  const envPath = '.env.local';
  statSync(envPath);
  config({ path: envPath });
}
