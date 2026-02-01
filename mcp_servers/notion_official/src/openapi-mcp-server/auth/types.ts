export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

export interface AuthTemplate {
  url: string
  method: HttpMethod
  headers: Record<string, string>
  body?: string
}

export interface SecurityScheme {
  [key: string]: {
    tokenUrl?: string
    [key: string]: any
  }
}

export interface Server {
  url: string
  description?: string
}

export interface TemplateContext {
  securityScheme?: SecurityScheme
  servers?: Server[]
  args: Record<string, string>
}
