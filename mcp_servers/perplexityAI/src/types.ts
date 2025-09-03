export interface Message {
  role: string;
  content: string;
}

export interface PerplexityOptions {
  tool?: string;
  max_citations?: number;
  verbose?: boolean;
  extra?: Record<string, any>;
}
