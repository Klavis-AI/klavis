/**
 * @fileoverview Markdown builder utility for creating well-structured, semantic markdown content
 * @module utils/formatting/markdownBuilder
 */

/**
 * Utility class for building well-formatted markdown content with consistent structure.
 *
 * This builder provides a fluent API for creating markdown documents with proper
 * spacing, hierarchy, and semantic structure. It helps eliminate string concatenation
 * and ensures consistent formatting across all tool response formatters.
 *
 * @example
 * ```typescript
 * const md = new MarkdownBuilder()
 *   .h1('Commit Created Successfully')
 *   .keyValue('Commit Hash', 'abc123def')
 *   .keyValue('Author', 'John Doe')
 *   .section('Files Changed', () => {
 *     md.list(['file1.ts', 'file2.ts']);
 *   });
 *
 * const markdown = md.build();
 * ```
 */
export class MarkdownBuilder {
  private sections: string[] = [];

  /**
   * Add a level 1 heading.
   * @param text - The heading text
   * @param emoji - Optional emoji to prepend
   * @returns this builder for chaining
   */
  h1(text: string, emoji?: string): this {
    const prefix = emoji ? `${emoji} ` : '';
    this.sections.push(`# ${prefix}${text}\n\n`);
    return this;
  }

  /**
   * Add a level 2 heading.
   * @param text - The heading text
   * @param emoji - Optional emoji to prepend
   * @returns this builder for chaining
   */
  h2(text: string, emoji?: string): this {
    const prefix = emoji ? `${emoji} ` : '';
    this.sections.push(`## ${prefix}${text}\n\n`);
    return this;
  }

  /**
   * Add a level 3 heading.
   * @param text - The heading text
   * @param emoji - Optional emoji to prepend
   * @returns this builder for chaining
   */
  h3(text: string, emoji?: string): this {
    const prefix = emoji ? `${emoji} ` : '';
    this.sections.push(`### ${prefix}${text}\n\n`);
    return this;
  }

  /**
   * Add a level 4 heading.
   * @param text - The heading text
   * @returns this builder for chaining
   */
  h4(text: string): this {
    this.sections.push(`#### ${text}\n\n`);
    return this;
  }

  /**
   * Add a bold key-value pair on a single line.
   * @param key - The key (will be bolded)
   * @param value - The value
   * @returns this builder for chaining
   */
  keyValue(key: string, value: string | number | boolean | null): this {
    const displayValue = value === null ? 'null' : String(value);
    this.sections.push(`**${key}:** ${displayValue}\n`);
    return this;
  }

  /**
   * Add a key-value pair without bolding (for less emphasis).
   * @param key - The key
   * @param value - The value
   * @returns this builder for chaining
   */
  keyValuePlain(key: string, value: string | number | boolean | null): this {
    const displayValue = value === null ? 'null' : String(value);
    this.sections.push(`${key}: ${displayValue}\n`);
    return this;
  }

  /**
   * Add a bulleted or numbered list.
   * @param items - Array of items to list
   * @param ordered - If true, creates a numbered list
   * @returns this builder for chaining
   */
  list(items: string[], ordered = false): this {
    if (items.length === 0) return this;

    const marker = ordered ? (i: number) => `${i + 1}.` : () => '-';
    this.sections.push(
      items.map((item, i) => `${marker(i)} ${item}`).join('\n') + '\n\n',
    );
    return this;
  }

  /**
   * Add a code block with optional language syntax highlighting.
   * @param content - The code content
   * @param language - Optional language identifier (e.g., 'typescript', 'diff', 'json')
   * @returns this builder for chaining
   */
  codeBlock(content: string, language = ''): this {
    this.sections.push(`\`\`\`${language}\n${content}\n\`\`\`\n\n`);
    return this;
  }

  /**
   * Add inline code (backticks).
   * @param code - The code text
   * @returns this builder for chaining
   */
  inlineCode(code: string): this {
    this.sections.push(`\`${code}\``);
    return this;
  }

  /**
   * Add a paragraph of text.
   * @param text - The paragraph content
   * @returns this builder for chaining
   */
  paragraph(text: string): this {
    this.sections.push(`${text}\n\n`);
    return this;
  }

  /**
   * Add a blockquote.
   * @param text - The quoted text
   * @returns this builder for chaining
   */
  blockquote(text: string): this {
    const lines = text.split('\n');
    const quoted = lines.map((line) => `> ${line}`).join('\n');
    this.sections.push(`${quoted}\n\n`);
    return this;
  }

  /**
   * Add a horizontal rule.
   * @returns this builder for chaining
   */
  hr(): this {
    this.sections.push('---\n\n');
    return this;
  }

  /**
   * Add a link.
   * @param text - The link text
   * @param url - The URL
   * @returns this builder for chaining
   */
  link(text: string, url: string): this {
    this.sections.push(`[${text}](${url})`);
    return this;
  }

  /**
   * Add a table from structured data.
   * @param headers - Array of column headers
   * @param rows - Array of rows, each row is an array of cell values
   * @returns this builder for chaining
   */
  table(headers: string[], rows: string[][]): this {
    if (headers.length === 0 || rows.length === 0) return this;

    // Header row
    this.sections.push(`| ${headers.join(' | ')} |\n`);

    // Separator row
    this.sections.push(`| ${headers.map(() => '---').join(' | ')} |\n`);

    // Data rows
    rows.forEach((row) => {
      this.sections.push(`| ${row.join(' | ')} |\n`);
    });

    this.sections.push('\n');
    return this;
  }

  /**
   * Add a section with a heading and callback for content.
   * This is useful for grouping related content.
   *
   * @example
   * ```typescript
   * md.section('Files Changed', () => {
   *   md.list(['file1.ts', 'file2.ts']);
   * });
   * ```
   *
   * @param title - The section heading
   * @param levelOrContent - Heading level (2-4) or callback function
   * @param content - Callback function (if level is provided)
   * @returns this builder for chaining
   */
  section(
    title: string,
    levelOrContent: 2 | 3 | 4 | (() => void),
    content?: () => void,
  ): this {
    const level = typeof levelOrContent === 'function' ? 2 : levelOrContent;
    const callback =
      typeof levelOrContent === 'function' ? levelOrContent : content!;
    switch (level) {
      case 2:
        this.h2(title);
        break;
      case 3:
        this.h3(title);
        break;
      case 4:
        this.h4(title);
        break;
    }
    callback();
    return this;
  }

  /**
   * Add a collapsible details section (HTML details/summary).
   * Note: Not all markdown renderers support this.
   *
   * @param summary - The summary text (always visible)
   * @param details - The detailed content (collapsed by default)
   * @returns this builder for chaining
   */
  details(summary: string, details: string): this {
    this.sections.push(`<details>\n<summary>${summary}</summary>\n\n`);
    this.sections.push(`${details}\n\n`);
    this.sections.push(`</details>\n\n`);
    return this;
  }

  /**
   * Add a status/alert box (GitHub/GitLab style).
   * Renders as a highlighted blockquote with an icon.
   *
   * Supported types:
   * - 'note': 📝 Neutral information
   * - 'tip': 💡 Helpful suggestions
   * - 'important': ❗ Critical information
   * - 'warning': ⚠️ Warning/caution
   * - 'caution': 🚨 Danger/destructive action
   *
   * @param type - Alert type
   * @param content - Alert content (can be multi-line)
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.alert('warning', 'This operation cannot be undone!');
   * // Renders: > [!WARNING]
   * //          > This operation cannot be undone!
   * ```
   */
  alert(
    type: 'note' | 'tip' | 'important' | 'warning' | 'caution',
    content: string,
  ): this {
    const typeUpper = type.toUpperCase();
    const lines = content.split('\n');
    this.sections.push(`> [!${typeUpper}]\n`);
    lines.forEach((line) => {
      this.sections.push(`> ${line}\n`);
    });
    this.sections.push('\n');
    return this;
  }

  /**
   * Add a task list with checkboxes (GitHub style).
   *
   * @param items - Array of tasks with checked status
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.taskList([
   *   { checked: true, text: 'Complete setup' },
   *   { checked: false, text: 'Run tests' },
   * ]);
   * // Renders: - [x] Complete setup
   * //          - [ ] Run tests
   * ```
   */
  taskList(items: Array<{ checked: boolean; text: string }>): this {
    if (items.length === 0) return this;

    this.sections.push(
      items
        .map((item) => `- [${item.checked ? 'x' : ' '}] ${item.text}`)
        .join('\n') + '\n\n',
    );
    return this;
  }

  /**
   * Add an image with alt text and optional title.
   *
   * @param altText - Alternative text for the image
   * @param url - Image URL
   * @param title - Optional title (shown on hover)
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.image('Architecture diagram', '/assets/diagram.png', 'System Architecture');
   * // Renders: ![Architecture diagram](/assets/diagram.png "System Architecture")
   * ```
   */
  image(altText: string, url: string, title?: string): this {
    const titlePart = title ? ` "${title}"` : '';
    this.sections.push(`![${altText}](${url}${titlePart})\n\n`);
    return this;
  }

  /**
   * Add strikethrough text.
   *
   * @param text - Text to strike through
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.text('Price: ').strikethrough('$100').text(' $80');
   * // Renders: Price: ~~$100~~ $80
   * ```
   */
  strikethrough(text: string): this {
    this.sections.push(`~~${text}~~`);
    return this;
  }

  /**
   * Add a diff-style code block showing additions and deletions.
   * Useful for showing file changes, configuration updates, etc.
   *
   * @param changes - Object with optional additions, deletions, and context lines
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.diff({
   *   additions: ['const newFeature = true;'],
   *   deletions: ['const oldFeature = false;'],
   *   context: ['// Configuration'],
   * });
   * // Renders as a diff code block with +/- prefixes
   * ```
   */
  diff(changes: {
    additions?: string[];
    deletions?: string[];
    context?: string[];
  }): this {
    const lines: string[] = [];

    // Context lines (no prefix)
    if (changes.context) {
      lines.push(...changes.context.map((line) => `  ${line}`));
    }

    // Deletions (- prefix)
    if (changes.deletions) {
      lines.push(...changes.deletions.map((line) => `- ${line}`));
    }

    // Additions (+ prefix)
    if (changes.additions) {
      lines.push(...changes.additions.map((line) => `+ ${line}`));
    }

    if (lines.length > 0) {
      this.codeBlock(lines.join('\n'), 'diff');
    }

    return this;
  }

  /**
   * Add a badge/shield (uses shields.io style).
   *
   * @param label - Badge label (left side)
   * @param message - Badge message (right side)
   * @param color - Optional color (e.g., 'green', 'red', 'blue', 'yellow')
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.badge('build', 'passing', 'green');
   * // Renders: ![build: passing](https://img.shields.io/badge/build-passing-green)
   * ```
   */
  badge(label: string, message: string, color = 'blue'): this {
    const encodedLabel = encodeURIComponent(label);
    const encodedMessage = encodeURIComponent(message);
    const url = `https://img.shields.io/badge/${encodedLabel}-${encodedMessage}-${color}`;
    this.sections.push(`![${label}: ${message}](${url})`);
    return this;
  }

  /**
   * Add bold text.
   *
   * @param text - Text to make bold
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.text('This is ').bold('important').text(' information.');
   * // Renders: This is **important** information.
   * ```
   */
  bold(text: string): this {
    this.sections.push(`**${text}**`);
    return this;
  }

  /**
   * Add italic text.
   *
   * @param text - Text to make italic
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.text('This is ').italic('emphasized').text('.');
   * // Renders: This is *emphasized*.
   * ```
   */
  italic(text: string): this {
    this.sections.push(`*${text}*`);
    return this;
  }

  /**
   * Add bold and italic text.
   *
   * @param text - Text to make bold and italic
   * @returns this builder for chaining
   *
   * @example
   * ```typescript
   * md.boldItalic('Very important');
   * // Renders: ***Very important***
   * ```
   */
  boldItalic(text: string): this {
    this.sections.push(`***${text}***`);
    return this;
  }

  /**
   * Add raw markdown content directly.
   * Use this for custom formatting not covered by other methods.
   *
   * @param markdown - Raw markdown string
   * @returns this builder for chaining
   */
  raw(markdown: string): this {
    this.sections.push(markdown);
    return this;
  }

  /**
   * Add a blank line for spacing.
   * @returns this builder for chaining
   */
  blankLine(): this {
    this.sections.push('\n');
    return this;
  }

  /**
   * Add text without any formatting or line breaks.
   * Useful for inline text that will be followed by other inline elements.
   *
   * @param text - The text to add
   * @returns this builder for chaining
   */
  text(text: string): this {
    this.sections.push(text);
    return this;
  }

  /**
   * Conditionally add content based on a predicate.
   *
   * @example
   * ```typescript
   * md.when(files.length > 0, () => {
   *   md.h2('Files Changed').list(files);
   * });
   * ```
   *
   * @param condition - If true, execute the callback
   * @param content - Callback function to build conditional content
   * @returns this builder for chaining
   */
  when(condition: boolean, content: () => void): this {
    if (condition) {
      content();
    }
    return this;
  }

  /**
   * Build the final markdown string.
   * Trims trailing whitespace and ensures the document ends cleanly.
   *
   * @returns The complete markdown document as a string
   */
  build(): string {
    return this.sections.join('').trim();
  }

  /**
   * Reset the builder to start building a new document.
   * @returns this builder for chaining
   */
  reset(): this {
    this.sections = [];
    return this;
  }
}

/**
 * Helper function to create a MarkdownBuilder instance.
 * Provides a shorter alternative to `new MarkdownBuilder()`.
 *
 * @returns A new MarkdownBuilder instance
 */
export function markdown(): MarkdownBuilder {
  return new MarkdownBuilder();
}
