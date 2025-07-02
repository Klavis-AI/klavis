import { FastMCP } from 'fastmcp';
import { getUsersByName, getUsersToolSchema } from './tools';
import {
  createBoard,
  createBoardToolSchema,
  getBoards,
  getBoardSchema,
  getBoardSchemaToolSchema,
} from './tools/boards';
import {
  createColumn,
  createColumnToolSchema,
  deleteColumn,
  deleteColumnToolSchema,
} from './tools/columns';
import { createItem, createItemToolSchema } from './tools/items';

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

server.addTool({
  name: 'monday_create_board',
  description: 'Create a new monday.com board with specified columns and groups',
  parameters: createBoardToolSchema,
  execute: async (args) => await createBoard(args),
});

server.addTool({
  name: 'monday_get_boards',
  description: 'Get all the monday.com boards',
  execute: async () => await getBoards(),
});

server.addTool({
  name: 'monday_create_column',
  description: 'Create a new column in a monday.com board',
  parameters: createColumnToolSchema,
  execute: async (args) => await createColumn(args),
});

server.addTool({
  name: 'monday_delete_column',
  description: 'Delete a column from a monday.com board',
  parameters: deleteColumnToolSchema,
  execute: async (args) => await deleteColumn(args),
});

server.addTool({
  name: 'monday_create_item',
  description: 'Create a new item in a monday.com board',
  parameters: createItemToolSchema,
  execute: async (args) => await createItem(args),
});

server.start({
  httpStream: {
    port: 5000,
    endpoint: '/mcp',
  },
  transportType: 'httpStream',
});
