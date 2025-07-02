import { z } from 'zod';
import { client } from './base';
import { createItemQuery } from './queries.graphql';

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
      'A string containing the new column values for the item following this structure: {\\"column_id\\": \\"value\\",... you can change multiple columns at once, note that for status column you must use nested value with "label" as a key and for date column use "date" as key} - example: "{\\"text_column_id\\":\\"New text\\", \\"status_column_id\\":{\\"label\\":\\"Done\\"}, \\"date_column_id\\":{\\"date\\":\\"2023-05-25\\"},\\"dropdown_id\\":\\"value\\", \\"phone_id\\":\\"123-456-7890\\", \\"email_id\\":\\"test@example.com\\"}"',
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
