#!/usr/bin/env node
import express from 'express';
import dotenv from 'dotenv';
import { HttpTransport } from './transport/httpTransport.js';
import { SSETransport } from './transport/sseTransport.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

const httpTransport = new HttpTransport();
const sseTransport = new SSETransport();

app.use('/', httpTransport.getRouter());
app.use('/', sseTransport.getRouter());

app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
  });
});

app.listen(PORT, () => {
  console.log(`Intercom MCP server running on port ${PORT}`);
});
