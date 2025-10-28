const UPPERCASE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const LOWERCASE_CHARS = 'abcdefghijklmnopqrstuvwxyz';
const NUMBER_CHARS = '0123456789';
const SYMBOL_CHARS = '!@#$%^&*()_+~`|}{[]:;?><,./-=';

export type GeneratePasswordOptions = {
  length?: number;
  numbers?: boolean;
  uppercase?: boolean;
  lowercase?: boolean;
  symbols?: boolean;
};

/**
 * Generates a cryptographically secure random password.
 *
 * @returns The generated password
 */
export const generatePassword = ({
  length = 10,
  numbers = false,
  symbols = false,
  uppercase = true,
  lowercase = true,
} = {}) => {
  // Build the character set based on options
  let chars = '';
  if (uppercase) {
    chars += UPPERCASE_CHARS;
  }
  if (lowercase) {
    chars += LOWERCASE_CHARS;
  }
  if (numbers) {
    chars += NUMBER_CHARS;
  }
  if (symbols) {
    chars += SYMBOL_CHARS;
  }

  if (chars.length === 0) {
    throw new Error('at least one character set must be selected');
  }

  const randomValues = new Uint32Array(length);
  crypto.getRandomValues(randomValues);

  // Map random values to our character set
  let password = '';
  for (let i = 0; i < length; i++) {
    const randomIndex = randomValues[i]! % chars.length;
    password += chars.charAt(randomIndex);
  }

  return password;
};
