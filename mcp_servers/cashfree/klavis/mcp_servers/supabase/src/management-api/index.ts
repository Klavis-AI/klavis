import createClient, {
  type Client,
  type FetchResponse,
  type ParseAsResponse,
} from 'openapi-fetch';
import type {
  MediaType,
  ResponseObjectMap,
  SuccessResponse,
} from 'openapi-typescript-helpers';
import { z } from 'zod';
import type { paths } from './types.js';

export function createManagementApiClient(
  baseUrl: string,
  accessToken: string,
  headers: Record<string, string> = {}
) {
  return createClient<paths>({
    baseUrl,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
      ...headers,
    },
  });
}

export type ManagementApiClient = Client<paths>;

export type SuccessResponseType<
  T extends Record<string | number, any>,
  Options,
  Media extends MediaType,
> = {
  data: ParseAsResponse<SuccessResponse<ResponseObjectMap<T>, Media>, Options>;
  error?: never;
  response: Response;
};

const errorSchema = z.object({
  message: z.string(),
});

export function assertSuccess<
  T extends Record<string | number, any>,
  Options,
  Media extends MediaType,
>(
  response: FetchResponse<T, Options, Media>,
  fallbackMessage: string
): asserts response is SuccessResponseType<T, Options, Media> {
  if ('error' in response) {
    if (response.response.status === 401) {
      throw new Error(
        'Unauthorized. Please provide a valid access token to the MCP server via the --access-token flag.'
      );
    }

    const { data: errorContent } = errorSchema.safeParse(response.error);

    if (errorContent) {
      throw new Error(errorContent.message);
    }

    throw new Error(fallbackMessage);
  }
}
