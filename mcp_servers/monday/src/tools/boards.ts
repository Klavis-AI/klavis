import { z } from 'zod';
import { client } from './base';
import { getBoardSchemaQuery } from './queries.graphql';

export const getBoardSchemaToolSchema = z.object({
  boardId: z.string().describe('The ID of the board to get the schema for'),
});

export const getBoardSchema = async (args: z.infer<typeof getBoardSchemaToolSchema>) => {
  const { boardId } = args;
  const board = await client.request(getBoardSchemaQuery, { boardId });
  return {
    type: 'text' as const,
    text: JSON.stringify(board),
  };
};
