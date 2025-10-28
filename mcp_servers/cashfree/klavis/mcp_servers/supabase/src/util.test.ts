import { describe, expect, it } from 'vitest';
import { hashObject, parseKeyValueList } from './util.js';

describe('parseKeyValueList', () => {
  it('should parse a simple key-value string', () => {
    const input = 'key1=value1\nkey2=value2';
    const result = parseKeyValueList(input);
    expect(result).toEqual({ key1: 'value1', key2: 'value2' });
  });

  it('should handle empty values', () => {
    const input = 'key1=\nkey2=value2';
    const result = parseKeyValueList(input);
    expect(result).toEqual({ key1: '', key2: 'value2' });
  });

  it('should handle values with equals sign', () => {
    const input = 'key1=value=with=equals\nkey2=simple';
    const result = parseKeyValueList(input);
    expect(result).toEqual({ key1: 'value=with=equals', key2: 'simple' });
  });

  it('should handle empty input', () => {
    const input = '';
    const result = parseKeyValueList(input);
    expect(result).toEqual({});
  });

  it('should handle input with only newlines', () => {
    const input = '\n\n\n';
    const result = parseKeyValueList(input);
    expect(result).toEqual({});
  });

  it('should parse real-world Cloudflare trace output', () => {
    const input =
      'fl=123abc\nvisit_scheme=https\nloc=US\ntls=TLSv1.3\nhttp=http/2';
    const result = parseKeyValueList(input);
    expect(result).toEqual({
      fl: '123abc',
      visit_scheme: 'https',
      loc: 'US',
      tls: 'TLSv1.3',
      http: 'http/2',
    });
  });
});

describe('hashObject', () => {
  it('should consistently hash the same object', async () => {
    const obj = { a: 1, b: 2, c: 3 };

    const hash1 = await hashObject(obj);
    const hash2 = await hashObject(obj);

    expect(hash1).toBe(hash2);
  });

  it('should produce the same hash regardless of property order', async () => {
    const obj1 = { a: 1, b: 2, c: 3 };
    const obj2 = { c: 3, a: 1, b: 2 };

    const hash1 = await hashObject(obj1);
    const hash2 = await hashObject(obj2);

    expect(hash1).toBe(hash2);
  });

  it('should produce different hashes for different objects', async () => {
    const obj1 = { a: 1, b: 2 };
    const obj2 = { a: 1, b: 3 };

    const hash1 = await hashObject(obj1);
    const hash2 = await hashObject(obj2);

    expect(hash1).not.toBe(hash2);
  });

  it('should handle nested objects', async () => {
    const obj1 = { a: 1, b: { c: 2 } };
    const obj2 = { a: 1, b: { c: 3 } };

    const hash1 = await hashObject(obj1);
    const hash2 = await hashObject(obj2);

    expect(hash1).not.toBe(hash2);
  });

  it('should handle arrays', async () => {
    const obj1 = { a: [1, 2, 3] };
    const obj2 = { a: [1, 2, 4] };

    const hash1 = await hashObject(obj1);
    const hash2 = await hashObject(obj2);

    expect(hash1).not.toBe(hash2);
  });
});
