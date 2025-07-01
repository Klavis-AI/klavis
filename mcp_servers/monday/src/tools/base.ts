import { ApiClient } from '@mondaydotcomorg/api';
import dotenv from 'dotenv';

dotenv.config();

const MONDAY_API_TOKEN = process.env.MONDAY_API_TOKEN;
if (!MONDAY_API_TOKEN) {
  throw new Error('MONDAY_API_TOKEN is not set');
}

export const client = new ApiClient({ token: MONDAY_API_TOKEN });
