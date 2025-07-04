import { ApiClient } from '@mondaydotcomorg/api';

export function createClient(token: string): ApiClient {
  return new ApiClient({ token });
}
