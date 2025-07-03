import dotenv from 'dotenv';
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

const server = new FastMCP({
  name: 'monday',
  version: '1.0.0',
  authenticate: async (request) => {
    const token = process.env.MONDAY_API_KEY || (request.headers['x-auth-token'] as string);
    if (!token) {
      throw new Error(
        'Error: Monday API token is missing. Provide it via MONDAY_API_KEY env var or x-auth-token header.',
      );
    }
    return { token };
  },
});

server.addTool({
  name: 'monday_get_users_by_name',
  description: 'Retrieve user information by name or partial name',
  parameters: getUsersToolSchema,
  execute: async (args, { session }) => await getUsersByName(args, session?.token as string),
});

server.addTool({
  name: 'monday_get_board_schema',
  description: 'Get board schema (columns and groups) by board id',
  parameters: getBoardSchemaToolSchema,
  execute: async (args, { session }) => await getBoardSchema(args, session?.token as string),
});

server.addTool({
  name: 'monday_create_board',
  description: 'Create a new monday.com board with specified columns and groups',
  parameters: createBoardToolSchema,
  execute: async (args, { session }) => await createBoard(args, session?.token as string),
});

server.addTool({
  name: 'monday_get_boards',
  description: 'Get all the monday.com boards',
  execute: async (args, { session }) => await getBoards(session?.token as string),
});

server.addTool({
  name: 'monday_create_column',
  description: 'Create a new column in a monday.com board',
  parameters: createColumnToolSchema,
  execute: async (args, { session }) => await createColumn(args, session?.token as string),
});

server.addTool({
  name: 'monday_delete_column',
  description: 'Delete a column from a monday.com board',
  parameters: deleteColumnToolSchema,
  execute: async (args, { session }) => await deleteColumn(args, session?.token as string),
});

server.addTool({
  name: 'monday_create_item',
  description: 'Create a new item in a monday.com board',
  parameters: createItemToolSchema,
  execute: async (args, { session }) => await createItem(args, session?.token as string),
});

server.addTool({
  name: 'monday_get_board_items_by_name',
  description: 'Get items by name from a monday.com board',
  parameters: getBoardItemsByNameToolSchema,
  execute: async (args, { session }) => await getBoardItemsByName(args, session?.token as string),
});

server.addTool({
  name: 'monday_create_update',
  description: 'Create a new update for an item in a monday.com board',
  parameters: createUpdateToolSchema,
  execute: async (args, { session }) => await createUpdate(args, session?.token as string),
});

server.addTool({
  name: 'monday_delete_item',
  description: 'Delete an item from a monday.com board',
  parameters: deleteItemToolSchema,
  execute: async (args, { session }) => await deleteItem(args, session?.token as string),
});

server.addTool({
  name: 'monday_change_item_column_values',
  description: 'Change the column values of an item in a monday.com board',
  parameters: changeItemColumnValuesToolSchema,
  execute: async (args, { session }) =>
    await changeItemColumnValues(args, session?.token as string),
});

server.addTool({
  name: 'monday_move_item_to_group',
  description: 'Move an item to a group in a monday.com board',
  parameters: moveItemToGroupToolSchema,
  execute: async (args, { session }) => await moveItemToGroup(args, session?.token as string),
});

server.start({
  httpStream: {
    port: 5000,
    endpoint: '/mcp',
  },
  transportType: 'httpStream',
});
