import { FastMCP } from 'fastmcp';
import { getUsersByName, getUsersToolSchema } from './tools';

const server = new FastMCP({
  name: 'monday',
  version: '1.0.0',
});

server.addTool({
  name: 'monday_get_users_by_name',
  description: 'Retrieve user information by name or partial name',
  parameters: getUsersToolSchema,
  execute: async (args) => await getUsersByName(args),
});

server.start({
  httpStream: {
    port: 5000,
    endpoint: '/mcp',
  },
  transportType: 'httpStream',
});
