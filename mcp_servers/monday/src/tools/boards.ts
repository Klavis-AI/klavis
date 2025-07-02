import { BoardKind } from '@mondaydotcomorg/api';
import { z } from 'zod';
import { client } from './base';
import { createBoardQuery, getBoardSchemaQuery, getBoardsQuery } from './queries.graphql';

export const getBoardSchemaToolSchema = z.object({
  boardId: z.string().describe('The ID of the board to get the schema for'),
});

export const createBoardToolSchema = z.object({
  boardName: z.string().describe('The name of the board to create'),
  boardKind: z
    .nativeEnum(BoardKind)
    .default(BoardKind.Public)
    .describe('The kind of board to create'),
  boardDescription: z.string().optional().describe('The description of the board to create'),
  workspaceId: z.string().optional().describe('The ID of the workspace to create the board in'),
});

export const getBoards = async () => {
  const boards = await client.request(getBoardsQuery);
  return {
    type: 'text' as const,
    text: JSON.stringify(boards),
  };
};
export const getBoardSchema = async (args: z.infer<typeof getBoardSchemaToolSchema>) => {
  const { boardId } = args;
  const board = await client.request(getBoardSchemaQuery, { boardId });
  return {
    type: 'text' as const,
    text: JSON.stringify(board),
  };
};

export const createBoard = async (args: z.infer<typeof createBoardToolSchema>) => {
  const { boardName, boardKind, boardDescription, workspaceId } = args;
  const board = await client.request(createBoardQuery, {
    boardName,
    boardKind,
    boardDescription,
    workspaceId,
  });
  return {
    type: 'text' as const,
    text: JSON.stringify(board),
  };
};
