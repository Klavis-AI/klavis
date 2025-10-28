import { anthropic } from '@ai-sdk/anthropic';
import { generateObject } from 'ai';
import { codeBlock, stripIndent } from 'common-tags';
import { expect } from 'vitest';
import { z } from 'zod';

const model = anthropic('claude-3-7-sonnet-20250219');

expect.extend({
  async toMatchCriteria(received: string, criteria: string) {
    const completionResponse = await generateObject({
      model,
      schema: z.object({
        pass: z
          .boolean()
          .describe("Whether the 'Received' adheres to the test 'Criteria'"),
        reason: z
          .string()
          .describe(
            "The reason why 'Received' does or does not adhere to the test 'Criteria'. Must explain exactly which part of 'Received' did or did not pass the test 'Criteria'."
          ),
      }),
      messages: [
        {
          role: 'system',
          content: stripIndent`
            You are a test runner. Your job is to evaluate whether 'Received' adheres to the test 'Criteria'.
          `,
        },
        {
          role: 'user',
          content: codeBlock`
            Received:
            ${received}

            Criteria:
            ${criteria}
          `,
        },
      ],
    });

    const { pass, reason } = completionResponse.object;

    return {
      message: () =>
        codeBlock`
          ${this.utils.matcherHint('toMatchCriteria', received, criteria, {
            comment: `evaluated by LLM '${model.modelId}'`,
            isNot: this.isNot,
            promise: this.promise,
          })}

          ${reason}
        `,
      pass,
    };
  },
});
