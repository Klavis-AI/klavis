import { describe, expect, it } from 'vitest';
import { generatePassword } from './password.js';

describe('generatePassword', () => {
  it('should generate a password with default options', () => {
    const password = generatePassword();
    expect(password.length).toBe(10);
    expect(/^[A-Za-z]+$/.test(password)).toBe(true);
  });

  it('should generate a password with custom length', () => {
    const password = generatePassword({ length: 16 });
    expect(password.length).toBe(16);
  });

  it('should generate a password with numbers', () => {
    const password = generatePassword({
      numbers: true,
      uppercase: false,
      lowercase: false,
    });
    expect(/[0-9]/.test(password)).toBe(true);
  });

  it('should generate a password with symbols', () => {
    const password = generatePassword({ symbols: true });
    expect(/[!@#$%^&*()_+~`|}{[\]:;?><,./-=]/.test(password)).toBe(true);
  });

  it('should generate a password with uppercase only', () => {
    const password = generatePassword({ uppercase: true, lowercase: false });
    expect(/^[A-Z]+$/.test(password)).toBe(true);
  });

  it('should generate a password with lowercase only', () => {
    const password = generatePassword({ uppercase: false, lowercase: true });
    expect(/^[a-z]+$/.test(password)).toBe(true);
  });

  it('should not generate the same password twice', () => {
    const password1 = generatePassword();
    const password2 = generatePassword();
    expect(password1).not.toBe(password2);
  });

  it('should throw an error if no character sets are selected', () => {
    expect(() =>
      generatePassword({
        uppercase: false,
        lowercase: false,
        numbers: false,
        symbols: false,
      })
    ).toThrow('at least one character set must be selected');
  });
});
