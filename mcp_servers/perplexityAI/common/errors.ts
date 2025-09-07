export class PerplexityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PerplexityError";
  }
}
