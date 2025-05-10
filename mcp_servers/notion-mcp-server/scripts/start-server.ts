import path from 'node:path'
import { fileURLToPath } from 'url'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'

import { initProxy, ValidationError } from '../src/init-server'

export async function startServer(args: string[] = process.argv.slice(2)) {
  const filename = fileURLToPath(import.meta.url)
  const directory = path.dirname(filename)
  const specPath = path.resolve(directory, '../scripts/notion-openapi.json')
  
  const baseUrl = process.env.BASE_URL ?? undefined

  const proxy = await initProxy(specPath, baseUrl)
  await proxy.connect(new StdioServerTransport())

  return proxy.getServer()
}

startServer().catch(error => {
  if (error instanceof ValidationError) {
    console.error('Invalid OpenAPI 3.1 specification:')
    error.errors.forEach(err => console.error(err))
  } else {
    console.error('Error:', error)
  }
  process.exit(1)
})
