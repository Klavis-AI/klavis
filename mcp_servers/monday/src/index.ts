import { FastMCP } from 'fastmcp';
import { getUsersByName, getUsersToolSchema } from './tools';
import { getBoardSchema, getBoardSchemaToolSchema } from './tools/boards';

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

server.addTool({
  name: 'monday_get_board_schema',
  description: 'Get board schema (columns and groups) by board id',
  parameters: getBoardSchemaToolSchema,
  execute: async (args) => await getBoardSchema(args),
});

server.start({
  httpStream: {
    port: 5000,
    endpoint: '/mcp',
  },
  transportType: 'httpStream',
});
