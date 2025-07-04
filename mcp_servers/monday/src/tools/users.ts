import { z } from 'zod';
import { createClient } from './base';
import { getUsersByNameQuery } from './queries.graphql';

export const getUsersToolSchema = z.object({
  name: z.string().describe('The name or partial name of the user to get'),
});

export const getUsersByName = async (args: z.infer<typeof getUsersToolSchema>, token: string) => {
  const client = createClient(token);
  const users = await client.request(getUsersByNameQuery, { name: args.name });
  return {
    type: 'text' as const,
    text: JSON.stringify(users),
  };
};
