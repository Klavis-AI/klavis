/**
 * @fileoverview Provides a utility class for creating, modifying, and parsing PDF documents.
 * Wraps the 'pdf-lib' npm library with structured error handling and logging.
 * @module src/utils/parsing/pdfParser
 */
import {
  PDFDocument,
  PDFFont,
  PDFImage,
  PDFPage,
  StandardFonts,
  degrees,
  rgb,
  type RGB,
} from 'pdf-lib';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  type RequestContext,
  logger,
  requestContextService,
} from '@/utils/index.js';

/**
 * Options for adding a new page to a PDF document.
 */
export interface AddPageOptions {
  /**
   * Width of the page in points (1/72 inch). Defaults to US Letter width (612 points).
   */
  width?: number;

  /**
   * Height of the page in points (1/72 inch). Defaults to US Letter height (792 points).
   */
  height?: number;
}

/**
 * Options for drawing text on a PDF page.
 */
export interface DrawTextOptions {
  /**
   * The text string to draw.
   */
  text: string;

  /**
   * X-coordinate (in points) of the text baseline start.
   */
  x: number;

  /**
   * Y-coordinate (in points) of the text baseline.
   */
  y: number;

  /**
   * Font size in points. Defaults to 12.
   */
  size?: number;

  /**
   * Font to use. Must be embedded first via embedFont().
   * Defaults to Helvetica.
   */
  font?: PDFFont;

  /**
   * Text color as an RGB object. Defaults to black.
   */
  color?: RGB;

  /**
   * Rotation angle in degrees. Defaults to 0.
   */
  rotate?: number;

  /**
   * Maximum width for text wrapping (in points). If specified, text will wrap.
   */
  maxWidth?: number;

  /**
   * Line height multiplier for wrapped text. Defaults to 1.2.
   */
  lineHeight?: number;
}

/**
 * Options for embedding an image into a PDF document.
 */
export interface EmbedImageOptions {
  /**
   * Image data as Uint8Array or ArrayBuffer.
   */
  imageBytes: Uint8Array | ArrayBuffer;

  /**
   * Image format: 'png' or 'jpg'.
   */
  format: 'png' | 'jpg';
}

/**
 * Options for drawing an embedded image on a page.
 */
export interface DrawImageOptions {
  /**
   * The embedded PDF image.
   */
  image: PDFImage;

  /**
   * X-coordinate (in points) of the image's top-left corner.
   */
  x: number;

  /**
   * Y-coordinate (in points) of the image's top-left corner.
   */
  y: number;

  /**
   * Width of the image in points. Defaults to original width.
   */
  width?: number;

  /**
   * Height of the image in points. Defaults to original height.
   */
  height?: number;

  /**
   * Rotation angle in degrees. Defaults to 0.
   */
  rotate?: number;

  /**
   * Opacity (0-1). Defaults to 1 (fully opaque).
   */
  opacity?: number;
}

/**
 * Page range specification for splitting PDFs.
 */
export interface PageRange {
  /**
   * Starting page index (0-based).
   */
  start: number;

  /**
   * Ending page index (0-based, inclusive).
   */
  end: number;
}

/**
 * Metadata extracted from a PDF document.
 */
export interface PdfMetadata {
  /**
   * Document title.
   */
  title?: string;

  /**
   * Document author.
   */
  author?: string;

  /**
   * Document subject.
   */
  subject?: string;

  /**
   * Keywords associated with the document.
   */
  keywords?: string;

  /**
   * Application that created the document.
   */
  creator?: string;

  /**
   * Application that produced the PDF.
   */
  producer?: string;

  /**
   * Creation date (ISO 8601 string).
   */
  creationDate?: string;

  /**
   * Modification date (ISO 8601 string).
   */
  modificationDate?: string;

  /**
   * Total number of pages.
   */
  pageCount: number;
}

/**
 * Options for setting PDF metadata.
 */
export interface SetMetadataOptions {
  /**
   * Document title.
   */
  title?: string;

  /**
   * Document author.
   */
  author?: string;

  /**
   * Document subject.
   */
  subject?: string;

  /**
   * Keywords associated with the document.
   */
  keywords?: string;

  /**
   * Application that created the document.
   */
  creator?: string;

  /**
   * Application that produced the PDF.
   */
  producer?: string;
}

/**
 * Options for filling PDF form fields.
 */
export interface FillFormOptions {
  /**
   * Map of field names to their values.
   */
  fields: Record<string, string | boolean | number>;

  /**
   * Whether to flatten the form after filling (make it non-editable).
   * Defaults to false.
   */
  flatten?: boolean;
}

/**
 * Utility class for creating, modifying, and parsing PDF documents.
 * Wraps the 'pdf-lib' library with structured error handling and logging.
 */
export class PdfParser {
  /**
   * Creates a new blank PDF document.
   *
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns A new PDFDocument instance.
   * @throws {McpError} If document creation fails.
   * @example
   * ```typescript
   * const doc = await pdfParser.createDocument();
   * const page = pdfParser.addPage(doc);
   * ```
   */
  async createDocument(context?: RequestContext): Promise<PDFDocument> {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.createDocument',
      });

    try {
      logger.debug('Creating new PDF document.', logContext);
      const doc = await PDFDocument.create();
      return doc;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to create PDF document.', {
        ...logContext,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to create PDF document: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Loads an existing PDF document from bytes.
   *
   * @param pdfBytes - The PDF file as Uint8Array or ArrayBuffer.
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns A PDFDocument instance.
   * @throws {McpError} If document loading fails.
   * @example
   * ```typescript
   * const existingPdfBytes = await fs.readFile('input.pdf');
   * const doc = await pdfParser.loadDocument(existingPdfBytes);
   * ```
   */
  async loadDocument(
    pdfBytes: Uint8Array | ArrayBuffer,
    context?: RequestContext,
  ): Promise<PDFDocument> {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.loadDocument',
      });

    try {
      logger.debug('Loading PDF document from bytes.', {
        ...logContext,
        byteLength:
          pdfBytes instanceof Uint8Array
            ? pdfBytes.length
            : pdfBytes.byteLength,
      });

      const doc = await PDFDocument.load(pdfBytes);
      return doc;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to load PDF document.', {
        ...logContext,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        `Failed to load PDF document: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Adds a new page to a PDF document.
   *
   * @param doc - The PDFDocument to add a page to.
   * @param options - Optional page dimensions.
   * @returns The newly created PDFPage.
   * @example
   * ```typescript
   * const page = pdfParser.addPage(doc, { width: 600, height: 400 });
   * ```
   */
  addPage(doc: PDFDocument, options?: AddPageOptions): PDFPage {
    const width = options?.width ?? 612; // US Letter width
    const height = options?.height ?? 792; // US Letter height
    return doc.addPage([width, height]);
  }

  /**
   * Embeds a standard font into a PDF document.
   *
   * @param doc - The PDFDocument to embed the font into.
   * @param fontName - The standard font name. Defaults to 'Helvetica'.
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns The embedded PDFFont.
   * @throws {McpError} If font embedding fails.
   * @example
   * ```typescript
   * const font = await pdfParser.embedFont(doc, 'TimesRoman');
   * ```
   */
  async embedFont(
    doc: PDFDocument,
    fontName: keyof typeof StandardFonts = 'Helvetica',
    context?: RequestContext,
  ): Promise<PDFFont> {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.embedFont',
      });

    try {
      logger.debug('Embedding standard font.', {
        ...logContext,
        fontName,
      });

      const font = await doc.embedFont(StandardFonts[fontName]);
      return font;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to embed font.', {
        ...logContext,
        fontName,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to embed font '${fontName}': ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Embeds an image (PNG or JPG) into a PDF document.
   *
   * @param doc - The PDFDocument to embed the image into.
   * @param options - Image data and format.
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns The embedded PDFImage.
   * @throws {McpError} If image embedding fails.
   * @example
   * ```typescript
   * const imageBytes = await fs.readFile('logo.png');
   * const image = await pdfParser.embedImage(doc, {
   *   imageBytes,
   *   format: 'png'
   * });
   * ```
   */
  async embedImage(
    doc: PDFDocument,
    options: EmbedImageOptions,
    context?: RequestContext,
  ): Promise<PDFImage> {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.embedImage',
      });

    try {
      logger.debug('Embedding image into PDF.', {
        ...logContext,
        format: options.format,
      });

      const image =
        options.format === 'png'
          ? await doc.embedPng(options.imageBytes)
          : await doc.embedJpg(options.imageBytes);

      return image;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to embed image.', {
        ...logContext,
        format: options.format,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to embed ${options.format} image: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Draws text on a PDF page with optional formatting.
   *
   * @param page - The PDFPage to draw text on.
   * @param options - Text content, position, and styling options.
   * @example
   * ```typescript
   * const font = await pdfParser.embedFont(doc, 'Helvetica');
   * pdfParser.drawText(page, {
   *   text: 'Hello, World!',
   *   x: 50,
   *   y: 700,
   *   size: 30,
   *   font,
   *   color: rgb(0, 0.53, 0.71)
   * });
   * ```
   */
  drawText(page: PDFPage, options: DrawTextOptions): void {
    const {
      text,
      x,
      y,
      size = 12,
      font,
      color = rgb(0, 0, 0),
      rotate = 0,
      maxWidth,
      lineHeight = 1.2,
    } = options;

    if (!maxWidth) {
      // Simple single-line text
      const drawOptions: {
        x: number;
        y: number;
        size: number;
        font?: PDFFont;
        color: RGB;
        rotate?: ReturnType<typeof degrees>;
      } = {
        x,
        y,
        size,
        color,
      };

      if (font) drawOptions.font = font;
      if (rotate) drawOptions.rotate = degrees(rotate);

      page.drawText(text, drawOptions);
    } else {
      // Text wrapping
      const words = text.split(' ');
      const lines: string[] = [];
      let currentLine = '';

      const effectiveFont = font || page.doc.getForm().getDefaultFont();

      for (const word of words) {
        const testLine = currentLine ? `${currentLine} ${word}` : word;
        const testWidth = effectiveFont.widthOfTextAtSize(testLine, size);

        if (testWidth <= maxWidth) {
          currentLine = testLine;
        } else {
          if (currentLine) {
            lines.push(currentLine);
          }
          currentLine = word;
        }
      }

      if (currentLine) {
        lines.push(currentLine);
      }

      // Draw each line
      let currentY = y;
      for (const line of lines) {
        const drawOptions: {
          x: number;
          y: number;
          size: number;
          font?: PDFFont;
          color: RGB;
          rotate?: ReturnType<typeof degrees>;
        } = {
          x,
          y: currentY,
          size,
          color,
        };

        if (font) drawOptions.font = font;
        if (rotate) drawOptions.rotate = degrees(rotate);

        page.drawText(line, drawOptions);
        currentY -= size * lineHeight;
      }
    }
  }

  /**
   * Draws an embedded image on a PDF page.
   *
   * @param page - The PDFPage to draw the image on.
   * @param options - Image, position, and sizing options.
   * @example
   * ```typescript
   * const image = await pdfParser.embedImage(doc, { imageBytes, format: 'png' });
   * pdfParser.drawImage(page, {
   *   image,
   *   x: 100,
   *   y: 500,
   *   width: 200,
   *   height: 150
   * });
   * ```
   */
  drawImage(page: PDFPage, options: DrawImageOptions): void {
    const {
      image,
      x,
      y,
      width = image.width,
      height = image.height,
      rotate = 0,
      opacity = 1,
    } = options;

    const drawOptions: {
      x: number;
      y: number;
      width: number;
      height: number;
      rotate?: ReturnType<typeof degrees>;
      opacity: number;
    } = {
      x,
      y,
      width,
      height,
      opacity,
    };

    if (rotate) drawOptions.rotate = degrees(rotate);

    page.drawImage(image, drawOptions);
  }

  /**
   * Merges multiple PDF documents into a single document.
   *
   * @param pdfBytesArray - Array of PDF documents as Uint8Array or ArrayBuffer.
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns A new merged PDFDocument.
   * @throws {McpError} If merging fails.
   * @example
   * ```typescript
   * const pdf1 = await fs.readFile('doc1.pdf');
   * const pdf2 = await fs.readFile('doc2.pdf');
   * const merged = await pdfParser.mergePdfs([pdf1, pdf2]);
   * ```
   */
  async mergePdfs(
    pdfBytesArray: (Uint8Array | ArrayBuffer)[],
    context?: RequestContext,
  ): Promise<PDFDocument> {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.mergePdfs',
      });

    try {
      logger.debug('Merging PDF documents.', {
        ...logContext,
        documentCount: pdfBytesArray.length,
      });

      const mergedPdf = await PDFDocument.create();

      for (let i = 0; i < pdfBytesArray.length; i++) {
        const pdfBytes = pdfBytesArray[i];
        if (!pdfBytes) continue;

        const pdfDoc = await PDFDocument.load(pdfBytes);
        const copiedPages = await mergedPdf.copyPages(
          pdfDoc,
          pdfDoc.getPageIndices(),
        );
        copiedPages.forEach((page) => mergedPdf.addPage(page));
      }

      logger.debug('Successfully merged PDF documents.', {
        ...logContext,
        mergedPageCount: mergedPdf.getPageCount(),
      });

      return mergedPdf;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to merge PDF documents.', {
        ...logContext,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to merge PDFs: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Splits a PDF document into multiple documents based on page ranges.
   *
   * @param pdfBytes - The source PDF as Uint8Array or ArrayBuffer.
   * @param ranges - Array of page ranges to extract.
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns Array of new PDFDocuments, one per range.
   * @throws {McpError} If splitting fails.
   * @example
   * ```typescript
   * const pdfBytes = await fs.readFile('document.pdf');
   * const [part1, part2] = await pdfParser.splitPdf(pdfBytes, [
   *   { start: 0, end: 4 },
   *   { start: 5, end: 9 }
   * ]);
   * ```
   */
  async splitPdf(
    pdfBytes: Uint8Array | ArrayBuffer,
    ranges: PageRange[],
    context?: RequestContext,
  ): Promise<PDFDocument[]> {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.splitPdf',
      });

    try {
      logger.debug('Splitting PDF document.', {
        ...logContext,
        rangeCount: ranges.length,
      });

      const sourcePdf = await PDFDocument.load(pdfBytes);
      const results: PDFDocument[] = [];

      for (const range of ranges) {
        const newPdf = await PDFDocument.create();
        const pageIndices: number[] = [];

        for (let i = range.start; i <= range.end; i++) {
          pageIndices.push(i);
        }

        const copiedPages = await newPdf.copyPages(sourcePdf, pageIndices);
        copiedPages.forEach((page) => newPdf.addPage(page));

        results.push(newPdf);
      }

      logger.debug('Successfully split PDF document.', {
        ...logContext,
        resultCount: results.length,
      });

      return results;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to split PDF document.', {
        ...logContext,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to split PDF: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Fills form fields in a PDF document.
   *
   * @param doc - The PDFDocument containing the form.
   * @param options - Field values and flatten option.
   * @param context - Optional RequestContext for logging and error correlation.
   * @throws {McpError} If form filling fails.
   * @example
   * ```typescript
   * pdfParser.fillForm(doc, {
   *   fields: {
   *     'Name': 'John Doe',
   *     'Age': 30,
   *     'Subscribe': true
   *   },
   *   flatten: true
   * });
   * ```
   */
  fillForm(
    doc: PDFDocument,
    options: FillFormOptions,
    context?: RequestContext,
  ): void {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.fillForm',
      });

    try {
      logger.debug('Filling PDF form fields.', {
        ...logContext,
        fieldCount: Object.keys(options.fields).length,
        flatten: options.flatten ?? false,
      });

      const form = doc.getForm();

      for (const [fieldName, value] of Object.entries(options.fields)) {
        try {
          const field = form.getField(fieldName);

          if (typeof value === 'string') {
            if ('setText' in field) {
              (field as { setText: (text: string) => void }).setText(value);
            }
          } else if (typeof value === 'boolean') {
            if ('check' in field || 'uncheck' in field) {
              const checkboxField = field as {
                check?: () => void;
                uncheck?: () => void;
              };
              if (value) {
                checkboxField.check?.();
              } else {
                checkboxField.uncheck?.();
              }
            }
          } else if (typeof value === 'number') {
            if ('setText' in field) {
              (field as { setText: (text: string) => void }).setText(
                String(value),
              );
            }
          }
        } catch (fieldError: unknown) {
          logger.warning('Failed to fill form field.', {
            ...logContext,
            fieldName,
            fieldError:
              fieldError instanceof Error
                ? fieldError.message
                : String(fieldError),
          });
        }
      }

      if (options.flatten) {
        form.flatten();
      }

      logger.debug('Successfully filled PDF form.', logContext);
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to fill PDF form.', {
        ...logContext,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to fill PDF form: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Extracts metadata from a PDF document.
   *
   * @param doc - The PDFDocument to extract metadata from.
   * @returns PDF metadata object.
   * @example
   * ```typescript
   * const metadata = pdfParser.extractMetadata(doc);
   * console.log(metadata.title, metadata.author);
   * ```
   */
  extractMetadata(doc: PDFDocument): PdfMetadata {
    const title = doc.getTitle();
    const author = doc.getAuthor();
    const subject = doc.getSubject();
    const keywords = doc.getKeywords();
    const creator = doc.getCreator();
    const producer = doc.getProducer();
    const creationDate = doc.getCreationDate();
    const modificationDate = doc.getModificationDate();

    const metadata: PdfMetadata = {
      pageCount: doc.getPageCount(),
    };

    if (title !== undefined) metadata.title = title;
    if (author !== undefined) metadata.author = author;
    if (subject !== undefined) metadata.subject = subject;
    if (keywords !== undefined) metadata.keywords = keywords;
    if (creator !== undefined) metadata.creator = creator;
    if (producer !== undefined) metadata.producer = producer;
    if (creationDate !== undefined)
      metadata.creationDate = creationDate.toISOString();
    if (modificationDate !== undefined)
      metadata.modificationDate = modificationDate.toISOString();

    return metadata;
  }

  /**
   * Sets metadata for a PDF document.
   *
   * @param doc - The PDFDocument to set metadata on.
   * @param metadata - Metadata values to set.
   * @example
   * ```typescript
   * pdfParser.setMetadata(doc, {
   *   title: 'My Document',
   *   author: 'John Doe',
   *   subject: 'Important Document'
   * });
   * ```
   */
  setMetadata(doc: PDFDocument, metadata: SetMetadataOptions): void {
    if (metadata.title) doc.setTitle(metadata.title);
    if (metadata.author) doc.setAuthor(metadata.author);
    if (metadata.subject) doc.setSubject(metadata.subject);
    if (metadata.keywords) doc.setKeywords([metadata.keywords]);
    if (metadata.creator) doc.setCreator(metadata.creator);
    if (metadata.producer) doc.setProducer(metadata.producer);
  }

  /**
   * Extracts text content from all pages of a PDF document.
   * Note: pdf-lib has limited text extraction capabilities.
   * For robust text extraction, consider using pdf-parse or pdfjs-dist.
   *
   * @param doc - The PDFDocument to extract text from.
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns Array of text strings, one per page.
   * @throws {McpError} If text extraction fails.
   * @example
   * ```typescript
   * const textPages = pdfParser.extractText(doc);
   * console.log(textPages[0]); // Text from first page
   * ```
   */
  extractText(doc: PDFDocument, context?: RequestContext): string[] {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.extractText',
      });

    try {
      logger.debug('Extracting text from PDF.', {
        ...logContext,
        pageCount: doc.getPageCount(),
      });

      // Note: pdf-lib doesn't have native text extraction.
      // This is a placeholder implementation.
      // For production use, integrate pdf-parse or pdfjs-dist.

      const pages = doc.getPages();
      const textPages: string[] = [];

      for (let i = 0; i < pages.length; i++) {
        // pdf-lib doesn't expose text extraction APIs directly.
        // This would require parsing the content streams.
        textPages.push('[Text extraction not implemented - use pdf-parse]');
      }

      logger.warning(
        'Text extraction is not fully implemented in pdf-lib. Consider using pdf-parse or pdfjs-dist for robust text extraction.',
        logContext,
      );

      return textPages;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to extract text from PDF.', {
        ...logContext,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to extract text: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }

  /**
   * Serializes a PDF document to bytes (Uint8Array) for saving to disk or transmission.
   *
   * @param doc - The PDFDocument to serialize.
   * @param context - Optional RequestContext for logging and error correlation.
   * @returns The PDF as Uint8Array.
   * @throws {McpError} If serialization fails.
   * @example
   * ```typescript
   * const pdfBytes = await pdfParser.saveDocument(doc);
   * await fs.writeFile('output.pdf', pdfBytes);
   * ```
   */
  async saveDocument(
    doc: PDFDocument,
    context?: RequestContext,
  ): Promise<Uint8Array> {
    const logContext =
      context ||
      requestContextService.createRequestContext({
        operation: 'PdfParser.saveDocument',
      });

    try {
      logger.debug('Serializing PDF document to bytes.', logContext);
      const bytes = await doc.save();
      logger.debug('Successfully serialized PDF document.', {
        ...logContext,
        byteLength: bytes.length,
      });
      return bytes;
    } catch (e: unknown) {
      const error = e as Error;
      logger.error('Failed to serialize PDF document.', {
        ...logContext,
        errorDetails: error.message,
      });

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to save PDF document: ${error.message}`,
        {
          ...context,
          rawError: error instanceof Error ? error.stack : String(error),
        },
      );
    }
  }
}

/**
 * Singleton instance of the PdfParser.
 * Use this instance for all PDF operations with support for creating, modifying,
 * and parsing PDF documents using pdf-lib.
 *
 * @example
 * ```typescript
 * import { pdfParser, rgb } from '@/utils';
 *
 * // Create a new PDF
 * const doc = await pdfParser.createDocument();
 * const page = pdfParser.addPage(doc);
 * const font = await pdfParser.embedFont(doc, 'Helvetica');
 *
 * pdfParser.drawText(page, {
 *   text: 'Hello, World!',
 *   x: 50,
 *   y: 750,
 *   size: 30,
 *   font,
 *   color: rgb(0, 0.53, 0.71)
 * });
 *
 * const pdfBytes = await pdfParser.saveDocument(doc);
 * await fs.writeFile('output.pdf', pdfBytes);
 * ```
 */
export const pdfParser = new PdfParser();

/**
 * Re-export commonly used pdf-lib utilities for convenience.
 */
export { PDFDocument, StandardFonts, degrees, rgb };
