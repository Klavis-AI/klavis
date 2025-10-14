import dotenv from 'dotenv';
import { FastMCP } from 'fastmcp';
import { IncomingMessage } from 'http';
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
import {
  changeItemColumnValues,
  changeItemColumnValuesToolSchema,
  createItem,
  createItemToolSchema,
  createUpdate,
  createUpdateToolSchema,
  deleteItem,
  deleteItemToolSchema,
  getBoardItemsByName,
  getBoardItemsByNameToolSchema,
  moveItemToGroup,
  moveItemToGroupToolSchema,
} from './tools/items';

dotenv.config();

function extractAccessToken(req: IncomingMessage): string {
  let authData = process.env.AUTH_DATA;
  
  if (!authData && req.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data JSON:', error);
    }
  }

  if (!authData) {
    console.error('Error: Monday access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
    return '';
  }

  const authDataJson = JSON.parse(authData);
  return authDataJson.access_token ?? '';
}

const server = new FastMCP({
  name: 'monday',
  version: '1.0.0',
  authenticate: async (request) => {
    const token = extractAccessToken(request);
    if (!token) {
      throw new Error(
        'Error: Monday API token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.',
      );
    }
    return { token };
  },
});

server.addTool({
  name: 'monday_get_users_by_name',
  description: 'Retrieve user information by name or partial name',
  parameters: getUsersToolSchema,
  annotations: { category: 'MONDAY_USER', readOnlyHint: true } as any,
  execute: async (args, { session }) => await getUsersByName(args, session?.token as string),
});

server.addTool({
  name: 'monday_get_board_schema',
  description: 'Get board schema (columns and groups) by board id',
  parameters: getBoardSchemaToolSchema,
  annotations: { category: 'MONDAY_BOARD', readOnlyHint: true } as any,
  execute: async (args, { session }) => await getBoardSchema(args, session?.token as string),
});

server.addTool({
  name: 'monday_create_board',
  description: 'Create a new monday.com board with specified columns and groups',
  parameters: createBoardToolSchema,
  annotations: { category: 'MONDAY_BOARD' } as any,
  execute: async (args, { session }) => await createBoard(args, session?.token as string),
});

server.addTool({
  name: 'monday_get_boards',
  description: 'Get all the monday.com boards',
  annotations: { category: 'MONDAY_BOARD', readOnlyHint: true } as any,
  execute: async (args, { session }) => await getBoards(session?.token as string),
});

server.addTool({
  name: 'monday_create_column',
  description: 'Create a new column in a monday.com board',
  parameters: createColumnToolSchema,
  annotations: { category: 'MONDAY_COLUMN' } as any,
  execute: async (args, { session }) => await createColumn(args, session?.token as string),
});

server.addTool({
  name: 'monday_delete_column',
  description: 'Delete a column from a monday.com board',
  parameters: deleteColumnToolSchema,
  annotations: { category: 'MONDAY_COLUMN' } as any,
  execute: async (args, { session }) => await deleteColumn(args, session?.token as string),
});

server.addTool({
  name: 'monday_create_item',
  description: 'Create a new item in a monday.com board',
  parameters: createItemToolSchema,
  annotations: { category: 'MONDAY_ITEM' } as any,
  execute: async (args, { session }) => await createItem(args, session?.token as string),
});

server.addTool({
  name: 'monday_get_board_items_by_name',
  description: 'Get items by name from a monday.com board',
  parameters: getBoardItemsByNameToolSchema,
  annotations: { category: 'MONDAY_ITEM', readOnlyHint: true } as any,
  execute: async (args, { session }) => await getBoardItemsByName(args, session?.token as string),
});

server.addTool({
  name: 'monday_create_update',
  description: 'Create a new update for an item in a monday.com board',
  parameters: createUpdateToolSchema,
  annotations: { category: 'MONDAY_UPDATE' } as any,
  execute: async (args, { session }) => await createUpdate(args, session?.token as string),
});

server.addTool({
  name: 'monday_delete_item',
  description: 'Delete an item from a monday.com board',
  parameters: deleteItemToolSchema,
  annotations: { category: 'MONDAY_ITEM' } as any,
  execute: async (args, { session }) => await deleteItem(args, session?.token as string),
});

server.addTool({
  name: 'monday_change_item_column_values',
  description: 'Change the column values of an item in a monday.com board',
  parameters: changeItemColumnValuesToolSchema,
  annotations: { category: 'MONDAY_ITEM' } as any,
  execute: async (args, { session }) =>
    await changeItemColumnValues(args, session?.token as string),
});

server.addTool({
  name: 'monday_move_item_to_group',
  description: 'Move an item to a group in a monday.com board',
  parameters: moveItemToGroupToolSchema,
  annotations: { category: 'MONDAY_ITEM' } as any,
  execute: async (args, { session }) => await moveItemToGroup(args, session?.token as string),
});

server.start({
  httpStream: {
    port: 5000,
    endpoint: '/mcp',
  },
  transportType: 'httpStream',
});
