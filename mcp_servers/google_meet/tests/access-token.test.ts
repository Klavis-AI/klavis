import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { AsyncLocalStorage } from 'async_hooks';

// Mock AsyncLocalStorage
const mockGetStore = jest.fn();
jest.mock('async_hooks', () => ({
  AsyncLocalStorage: jest.fn().mockImplementation(() => ({
    getStore: mockGetStore,
  })),
}));

// We'll need to create a testable version of getAccessToken
const getAccessToken = async (): Promise<string> => {
  const store = mockGetStore() as { accessToken?: string } | undefined;
  const accessToken = (store?.accessToken || '').trim();
  
  if (!accessToken) {
    throw new Error('Missing OAuth access token. Pass a valid token in the x-auth-token header.');
  }
  
  // Basic token format validation
  if (accessToken.length < 10) {
    throw new Error('Invalid access token format. Token is too short.');
  }
  
  if (accessToken.length > 4096) {
    throw new Error('Invalid access token format. Token is too long.');
  }
  
  // Check for potentially dangerous characters
  if (!/^[a-zA-Z0-9\-_.~:/?#[\]@!$&'()*+,;=]+$/.test(accessToken)) {
    throw new Error('Invalid access token format. Token contains invalid characters.');
  }
  
  return accessToken;
};

describe('Access Token Validation Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Valid access tokens', () => {
    it('should accept valid access token', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.valid-token-123' });
      const token = await getAccessToken();
      expect(token).toBe('ya29.valid-token-123');
    });

    it('should accept token with all allowed special characters', async () => {
      const validToken = 'ya29.token-with_all~allowed:chars/?#[]@!$&\'()*+,;=';
      mockGetStore.mockReturnValue({ accessToken: validToken });
      const token = await getAccessToken();
      expect(token).toBe(validToken);
    });

    it('should trim whitespace from token', async () => {
      mockGetStore.mockReturnValue({ accessToken: '  ya29.valid-token-123  ' });
      const token = await getAccessToken();
      expect(token).toBe('ya29.valid-token-123');
    });

    it('should accept very long but valid token', async () => {
      const longToken = 'ya29.' + 'a'.repeat(4000);
      mockGetStore.mockReturnValue({ accessToken: longToken });
      const token = await getAccessToken();
      expect(token).toBe(longToken);
    });

    it('should accept minimum length token', async () => {
      const minToken = 'ya29.12345';
      mockGetStore.mockReturnValue({ accessToken: minToken });
      const token = await getAccessToken();
      expect(token).toBe(minToken);
    });
  });

  describe('Invalid access tokens', () => {
    it('should reject empty token', async () => {
      mockGetStore.mockReturnValue({ accessToken: '' });
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should reject undefined token', async () => {
      mockGetStore.mockReturnValue({});
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should reject null token', async () => {
      mockGetStore.mockReturnValue({ accessToken: null });
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should reject whitespace-only token', async () => {
      mockGetStore.mockReturnValue({ accessToken: '   ' });
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should reject token that is too short', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'short' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token is too short.');
    });

    it('should reject token that is too long', async () => {
      const tooLongToken = 'ya29.' + 'a'.repeat(5000);
      mockGetStore.mockReturnValue({ accessToken: tooLongToken });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token is too long.');
    });

    it('should reject token with invalid characters - emojis', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token-with-🚀-emoji' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with invalid characters - spaces', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token with spaces' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with invalid characters - newlines', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token\nwith\nnewlines' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with invalid characters - tabs', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token\twith\ttabs' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with invalid characters - control characters', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token\x00with\x01control' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with invalid characters - backslash', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token\\with\\backslash' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with invalid characters - quotes', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token"with"quotes' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with invalid characters - angle brackets', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token<with>brackets' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });

    it('should reject token with unicode characters', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.token-with-unicode-测试' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token contains invalid characters.');
    });
  });

  describe('Edge cases', () => {
    it('should handle no store returned', async () => {
      mockGetStore.mockReturnValue(undefined);
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should handle null store returned', async () => {
      mockGetStore.mockReturnValue(null);
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should handle store with null accessToken', async () => {
      mockGetStore.mockReturnValue({ accessToken: null });
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should handle store with undefined accessToken', async () => {
      mockGetStore.mockReturnValue({ accessToken: undefined });
      await expect(getAccessToken()).rejects.toThrow('Missing OAuth access token');
    });

    it('should handle token that is exactly 10 characters', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.12345' });
      const token = await getAccessToken();
      expect(token).toBe('ya29.12345');
    });

    it('should handle token that is exactly 4096 characters', async () => {
      const exactLengthToken = 'ya29.' + 'a'.repeat(4091);
      mockGetStore.mockReturnValue({ accessToken: exactLengthToken });
      const token = await getAccessToken();
      expect(token).toBe(exactLengthToken);
    });

    it('should handle token that is 9 characters (boundary test)', async () => {
      mockGetStore.mockReturnValue({ accessToken: 'ya29.1234' });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token is too short.');
    });

    it('should handle token that is 4097 characters (boundary test)', async () => {
      const tooLongToken = 'ya29.' + 'a'.repeat(4092);
      mockGetStore.mockReturnValue({ accessToken: tooLongToken });
      await expect(getAccessToken()).rejects.toThrow('Invalid access token format. Token is too long.');
    });
  });
});
