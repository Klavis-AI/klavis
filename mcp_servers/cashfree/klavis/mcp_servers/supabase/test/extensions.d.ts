import 'vitest';

interface CustomMatchers<R = unknown> {
  /**
   * Uses LLM-as-a-judge to evaluate the received string against
   * criteria described in natural language.
   */
  toMatchCriteria(criteria: string): Promise<R>;
}

declare module 'vitest' {
  interface Assertion<T = any> extends CustomMatchers<T> {}
  interface AsymmetricMatchersContaining extends CustomMatchers {}
}
