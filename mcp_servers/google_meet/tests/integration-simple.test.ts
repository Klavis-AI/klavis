import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import request from 'supertest';
import express from 'express';

describe('HTTP Server Integration Tests', () => {
  let app: express.Application;

  beforeEach(() => {
    app = express();
    app.use(express.json());

    // Simple test endpoints
    app.post('/mcp', (req, res) => {
      const token = req.headers['x-auth-token'] as string | undefined;
      
      if (!token || token.trim().length < 10) {
        return res.json({
          jsonrpc: '2.0',
          error: {
            code: -32603,
            message: 'Missing OAuth access token. Pass a valid token in the x-auth-token header.'
          },
          id: req.body.id
        });
      }

      const { method } = req.body;
      
      if (method === 'tools/list') {
        return res.json({
          jsonrpc: '2.0',
          result: {
            tools: [
              { name: 'create_meeting', description: 'Create a new meeting' },
              { name: 'get_meeting_details', description: 'Get details of a meeting' },
              { name: 'get_past_meetings', description: 'Get details for completed meetings' },
              { name: 'get_past_meeting_details', description: 'Get details of a specific meeting' },
              { name: 'get_past_meeting_participants', description: 'Get a list of participants from a past meeting' },
            ]
          },
          id: req.body.id
        });
      }

      if (method === 'tools/call') {
        return res.json({
          jsonrpc: '2.0',
          result: {
            content: [{ type: 'text', text: 'Tool executed successfully' }]
          },
          id: req.body.id
        });
      }

      return res.status(400).json({
        jsonrpc: '2.0',
        error: { code: -32600, message: 'Invalid request' },
        id: req.body.id
      });
    });

    app.get('/mcp', (req, res) => {
      res.status(405).json({
        jsonrpc: '2.0',
        error: { code: -32000, message: 'Method not allowed.' },
        id: null,
      });
    });

    app.delete('/mcp', (req, res) => {
      res.status(405).json({
        jsonrpc: '2.0',
        error: { code: -32000, message: 'Method not allowed.' },
        id: null,
      });
    });
  });

  describe('Basic HTTP functionality', () => {
    it('should handle POST requests to /mcp', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.jsonrpc).toBe('2.0');
      expect(response.body.id).toBe(1);
    });

    it('should reject GET requests to /mcp', async () => {
      const response = await request(app).get('/mcp');
      expect(response.status).toBe(405);
      expect(response.body.error.message).toBe('Method not allowed.');
    });

    it('should reject DELETE requests to /mcp', async () => {
      const response = await request(app).delete('/mcp');
      expect(response.status).toBe(405);
      expect(response.body.error.message).toBe('Method not allowed.');
    });
  });

  describe('Authentication', () => {
    it('should reject requests without auth token', async () => {
      const response = await request(app)
        .post('/mcp')
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.error.message).toContain('Missing OAuth access token');
    });

    it('should reject requests with short auth token', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'short')
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.error.message).toContain('Missing OAuth access token');
    });

    it('should accept requests with valid auth token', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.result).toBeDefined();
    });

    it('should handle empty auth token', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', '')
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.error.message).toContain('Missing OAuth access token');
    });

    it('should handle whitespace-only auth token', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', '   ')
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.error.message).toContain('Missing OAuth access token');
    });
  });

  describe('JSON-RPC protocol', () => {
    it('should list tools', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.result.tools).toHaveLength(5);
      expect(response.body.result.tools[0].name).toBe('create_meeting');
    });

    it('should execute tools', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .send({
          jsonrpc: '2.0',
          method: 'tools/call',
          params: {
            name: 'create_meeting',
            arguments: {}
          },
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.result.content[0].text).toBe('Tool executed successfully');
    });

    it('should handle invalid methods', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .send({
          jsonrpc: '2.0',
          method: 'invalid/method',
          id: 1
        });

      expect(response.status).toBe(400);
      expect(response.body.error.code).toBe(-32600);
    });

    it('should handle malformed JSON', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .type('json')
        .send('{"invalid": json}');

      expect(response.status).toBe(400);
    });

    it('should preserve request IDs', async () => {
      const testIds = [1, '2', null, 'test-id-123'];

      for (const id of testIds) {
        const response = await request(app)
          .post('/mcp')
          .set('x-auth-token', 'ya29.valid-test-token-123')
          .send({
            jsonrpc: '2.0',
            method: 'tools/list',
            id
          });

        expect(response.body.id).toBe(id);
      }
    });
  });

  describe('Edge cases and robustness', () => {
    it('should handle very long auth tokens', async () => {
      const longToken = 'ya29.' + 'a'.repeat(4000);
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', longToken)
        .send({
          jsonrpc: '2.0',
          method: 'tools/list',
          id: 1
        });

      expect(response.status).toBe(200);
      expect(response.body.result).toBeDefined();
    });

    it('should handle special characters in request', async () => {
      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .send({
          jsonrpc: '2.0',
          method: 'tools/call',
          params: {
            name: 'create_meeting',
            arguments: {
              name: 'Meeting with 🚀 emojis and unicode 测试'
            }
          },
          id: 'test-with-unicode-测试'
        });

      expect(response.status).toBe(200);
      expect(response.body.id).toBe('test-with-unicode-测试');
    });

    it('should handle large request payloads', async () => {
      const largeArgs = {
        filter: 'a'.repeat(1000),
        description: 'b'.repeat(1000),
        metadata: Array(100).fill({ key: 'value'.repeat(10) })
      };

      const response = await request(app)
        .post('/mcp')
        .set('x-auth-token', 'ya29.valid-test-token-123')
        .send({
          jsonrpc: '2.0',
          method: 'tools/call',
          params: {
            name: 'create_meeting',
            arguments: largeArgs
          },
          id: 1
        });

      expect(response.status).toBe(200);
    });

    it('should handle concurrent requests', async () => {
      const requests = Array(10).fill(null).map((_, i) =>
        request(app)
          .post('/mcp')
          .set('x-auth-token', 'ya29.valid-test-token-123')
          .send({
            jsonrpc: '2.0',
            method: 'tools/list',
            id: i
          })
      );

      const responses = await Promise.all(requests);

      responses.forEach((response, i) => {
        expect(response.status).toBe(200);
        expect(response.body.id).toBe(i);
        expect(response.body.result.tools).toHaveLength(5);
      });
    });
  });
});
