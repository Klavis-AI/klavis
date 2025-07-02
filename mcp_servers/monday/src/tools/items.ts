import { z } from 'zod';
import { client } from './base';
import {
  changeItemColumnValuesQuery,
  createItemQuery,
  createUpdateQuery,
  deleteItemQuery,
  getBoardItemsByNameQuery,
} from './queries.graphql';

export const createItemToolSchema = z.object({
  boardId: z.string().describe('The id of the board to create the item in'),
  name: z
    .string()
    .describe("The name of the new item to be created, must be relevant to the user's request"),
  groupId: z
    .string()
    .optional()
    .describe(
      'The id of the group id to which the new item will be added, if its not clearly specified, leave empty',
    ),
  columnValues: z
    .string()
    .describe(
      'A string containing the new column values for the item following this structure: {\\"column_id\\": \\"value\\",... you can change multiple columns at once, note that for status column you must use nested value with "label" as a key and for date column use "date" as key} - example: "{\\"text_column_id\\":\\"New text\\", \\"status_column_id\\":{\\"label\\":\\"Done\\"}, \\"date_column_id\\":{\\"date\\":\\"2023-05-25\\"},\\"dropdown_id\\":\\"value\\", \\"phone_id\\":\\"123-456-7890\\", \\"email_id\\":\\"test@example.com\\", {\\"boolean_column_id\\":{\\"checked\\":true}}',
    ),
});

export const getBoardItemsByNameToolSchema = z.object({
  boardId: z.string().describe('The id of the board to get the items from'),
  term: z.string().describe('The term to search for in the items'),
});

export const createUpdateToolSchema = z.object({
  itemId: z.string().describe('The id of the item to which the update will be added'),
  body: z.string().describe("The update to be created, must be relevant to the user's request"),
});

export const deleteItemToolSchema = z.object({
  itemId: z.string().describe('The id of the item to delete'),
});

export const changeItemColumnValuesToolSchema = z.object({
  boardId: z.string().describe('The id of the board to change the column values of'),
  itemId: z.string().describe('The id of the item to change the column values of'),
  columnValues: z
    .string()
    .describe(
      `A string containing the new column values for the item following this structure: {\\"column_id\\": \\"value\\",... you can change multiple columns at once, note that for status column you must use nested value with 'label' as a key and for date column use 'date' as key} - example: "{\\"text_column_id\\":\\"New text\\", \\"status_column_id\\":{\\"label\\":\\"Done\\"}, \\"date_column_id\\":{\\"date\\":\\"2023-05-25\\"}, \\"phone_id\\":\\"123-456-7890\\", \\"email_id\\":\\"test@example.com\\", {\\"boolean_column_id\\":{\\"checked\\":true}}"`,
    ),
});
export const createItem = async (args: z.infer<typeof createItemToolSchema>) => {
  const { boardId, name, groupId, columnValues } = args;
  const item = await client.request(createItemQuery, {
    boardId: boardId.toString(),
    itemName: name,
    groupId: groupId?.toString(),
    columnValues,
  });
  return {
    type: 'text' as const,
    text: JSON.stringify(item, null, 2),
  };
};

export const getBoardItemsByName = async (args: z.infer<typeof getBoardItemsByNameToolSchema>) => {
  const { boardId, term } = args;
  const items = await client.request(getBoardItemsByNameQuery, {
    boardId: boardId.toString(),
    term,
  });
  return {
    type: 'text' as const,
    text: JSON.stringify(items, null, 2),
  };
};

export const createUpdate = async (args: z.infer<typeof createUpdateToolSchema>) => {
  const { itemId, body } = args;
  const update = await client.request(createUpdateQuery, {
    itemId,
    body,
  });
  return {
    type: 'text' as const,
    text: JSON.stringify(update, null, 2),
  };
};

export const deleteItem = async (args: z.infer<typeof deleteItemToolSchema>) => {
  const { itemId } = args;
  const item = await client.request(deleteItemQuery, { id: itemId.toString() });
  return {
    type: 'text' as const,
    text: JSON.stringify(item, null, 2),
  };
};

export const changeItemColumnValues = async (
  args: z.infer<typeof changeItemColumnValuesToolSchema>,
) => {
  const { boardId, itemId, columnValues } = args;
  const item = await client.request(changeItemColumnValuesQuery, {
    boardId: boardId.toString(),
    itemId: itemId.toString(),
    columnValues,
  });
  return {
    type: 'text' as const,
    text: JSON.stringify(item, null, 2),
  };
};
