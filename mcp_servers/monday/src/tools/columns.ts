import { ColumnType } from '@mondaydotcomorg/api';
import { z } from 'zod';
import { client } from './base';
import { createColumnQuery } from './queries.graphql';

export const createColumnToolSchema = z.object({
  boardId: z.string().describe('The id of the board to create the column in'),
  columnType: z.nativeEnum(ColumnType).describe('The type of the column to be created'),
  columnTitle: z.string().describe('The title of the column to be created'),
  columnDescription: z.string().optional().describe('The description of the column to be created'),
  columnSettings: z
    .array(z.string())
    .optional()
    .describe(
      "The default values for the new column (relevant only for column type 'status' or 'dropdown') when possible make the values relevant to the user's request",
    ),
});

export const createColumn = async (args: z.infer<typeof createColumnToolSchema>) => {
  const { boardId, columnType, columnTitle, columnDescription, columnSettings } = args;
  let columnSettingsString: string | undefined;
  if (columnSettings && columnType === ColumnType.Status) {
    columnSettingsString = JSON.stringify({
      labels: Object.fromEntries(
        columnSettings.map((label: string, i: number) => [String(i + 1), label]),
      ),
    });
  } else if (columnSettings && columnType === ColumnType.Dropdown) {
    columnSettingsString = JSON.stringify({
      settings: {
        labels: columnSettings.map((label: string, i: number) => ({ id: i + 1, name: label })),
      },
    });
  }
  const column = await client.request(createColumnQuery, {
    boardId: boardId.toString(),
    columnType,
    columnTitle,
    columnDescription,
    columnSettings: columnSettingsString,
  });
  return {
    type: 'text' as const,
    text: JSON.stringify(column, null, 2),
  };
};
