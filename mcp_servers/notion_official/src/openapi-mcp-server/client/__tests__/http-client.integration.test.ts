import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { HttpClient } from '../http-client'
import express from 'express'
import type { OpenAPIV3 } from 'openapi-types'
import type { Server } from 'http'

interface Pet {
  id: number
  name: string
  species: string
  age: number
  status: 'available' | 'pending' | 'sold'
}

// Simple in-memory pet store
let pets: Pet[] = []
let nextId = 1

// Initialize/reset pets data
function resetPets() {
  pets = [
    { id: 1, name: 'Fluffy', species: 'Cat', age: 3, status: 'available' },
    { id: 2, name: 'Max', species: 'Dog', age: 5, status: 'available' },
    { id: 3, name: 'Tweety', species: 'Bird', age: 1, status: 'sold' },
  ]
  nextId = 4
}

function createTestServer(port: number): Server {
  const app = express()
  app.use(express.json())

  // GET /pets - List all pets
  app.get('/pets', (req, res) => {
    const status = req.query.status
    const filtered = status ? pets.filter((p) => p.status === status) : pets
    res.json(filtered)
  })

  // POST /pets - Create a pet
  app.post('/pets', (req, res) => {
    const newPet: Pet = {
      id: nextId++,
      name: req.body.name,
      species: req.body.species,
      age: req.body.age,
      status: 'available',
    }
    pets.push(newPet)
    res.status(201).json(newPet)
  })

  // GET /pets/:id - Get a pet by ID
  app.get('/pets/:id', (req: any, res: any) => {
    const pet = pets.find((p) => p.id === Number(req.params.id))
    if (!pet) {
      return res.status(404).json({ error: 'Pet not found' })
    }
    res.json(pet)
  })

  // PUT /pets/:id - Update a pet
  app.put('/pets/:id', (req: any, res: any) => {
    const pet = pets.find((p) => p.id === Number(req.params.id))
    if (!pet) {
      return res.status(404).json({ error: 'Pet not found' })
    }
    if (req.body.status) pet.status = req.body.status
    res.json(pet)
  })

  // DELETE /pets/:id - Delete a pet
  app.delete('/pets/:id', (req: any, res: any) => {
    const index = pets.findIndex((p) => p.id === Number(req.params.id))
    if (index === -1) {
      return res.status(404).json({ error: 'Pet not found' })
    }
    pets.splice(index, 1)
    res.status(204).send()
  })

  return app.listen(port)
}

describe('HttpClient Integration Tests', () => {
  let PORT: number
  let BASE_URL: string
  let server: Server
  let openApiSpec: OpenAPIV3.Document
  let client: HttpClient

  beforeEach(async () => {
    // Use a random port to avoid conflicts
    PORT = 3000 + Math.floor(Math.random() * 1000)
    BASE_URL = `http://localhost:${PORT}`

    // Initialize pets data
    resetPets()

    // Start the test server
    server = createTestServer(PORT)

    // Create a minimal OpenAPI spec for the test server
    openApiSpec = {
      openapi: '3.0.0',
      info: { title: 'Pet Store API', version: '1.0.0' },
      servers: [{ url: BASE_URL }],
      paths: {
        '/pets': {
          get: {
            operationId: 'listPets',
            parameters: [{ name: 'status', in: 'query', schema: { type: 'string' } }],
            responses: { '200': { description: 'Success' } },
          },
          post: {
            operationId: 'createPet',
            requestBody: { content: { 'application/json': { schema: { type: 'object' } } } },
            responses: { '201': { description: 'Created' } },
          },
        },
        '/pets/{id}': {
          get: {
            operationId: 'getPet',
            parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'integer' } }],
            responses: { '200': { description: 'Success' }, '404': { description: 'Not found' } },
          },
          put: {
            operationId: 'updatePet',
            parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'integer' } }],
            requestBody: { content: { 'application/json': { schema: { type: 'object' } } } },
            responses: { '200': { description: 'Success' }, '404': { description: 'Not found' } },
          },
          delete: {
            operationId: 'deletePet',
            parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'integer' } }],
            responses: { '204': { description: 'Deleted' }, '404': { description: 'Not found' } },
          },
        },
      },
    }

    // Create HTTP client
    client = new HttpClient(
      {
        baseUrl: BASE_URL,
        headers: {
          Accept: 'application/json',
        },
      },
      openApiSpec,
    )
  })

  afterEach(async () => {
    server.close()
  })

  it('should list all pets', async () => {
    const operation = openApiSpec.paths['/pets']?.get
    if (!operation) throw new Error('Operation not found')

    const response = await client.executeOperation<Pet[]>(operation as OpenAPIV3.OperationObject & { method: string; path: string })

    expect(response.status).toBe(200)
    expect(Array.isArray(response.data)).toBe(true)
    expect(response.data.length).toBeGreaterThan(0)
    expect(response.data[0]).toHaveProperty('name')
    expect(response.data[0]).toHaveProperty('species')
    expect(response.data[0]).toHaveProperty('status')
  })

  it('should filter pets by status', async () => {
    const operation = openApiSpec.paths['/pets']?.get as OpenAPIV3.OperationObject & { method: string; path: string }
    if (!operation) throw new Error('Operation not found')

    const response = await client.executeOperation<Pet[]>(operation, { status: 'available' })

    expect(response.status).toBe(200)
    expect(Array.isArray(response.data)).toBe(true)
    response.data.forEach((pet: Pet) => {
      expect(pet.status).toBe('available')
    })
  })

  it('should get a specific pet by ID', async () => {
    const operation = openApiSpec.paths['/pets/{id}']?.get as OpenAPIV3.OperationObject & { method: string; path: string }
    if (!operation) throw new Error('Operation not found')

    const response = await client.executeOperation<Pet>(operation, { id: 1 })

    expect(response.status).toBe(200)
    expect(response.data).toHaveProperty('id', 1)
    expect(response.data).toHaveProperty('name')
    expect(response.data).toHaveProperty('species')
  })

  it('should create a new pet', async () => {
    const operation = openApiSpec.paths['/pets']?.post as OpenAPIV3.OperationObject & { method: string; path: string }
    if (!operation) throw new Error('Operation not found')

    const newPet = {
      name: 'TestPet',
      species: 'Dog',
      age: 2,
    }

    const response = await client.executeOperation<Pet>(operation as OpenAPIV3.OperationObject & { method: string; path: string }, newPet)

    expect(response.status).toBe(201)
    expect(response.data).toMatchObject({
      ...newPet,
      status: 'available',
    })
    expect(response.data.id).toBeDefined()
  })

  it("should update a pet's status", async () => {
    const operation = openApiSpec.paths['/pets/{id}']?.put
    if (!operation) throw new Error('Operation not found')

    const response = await client.executeOperation<Pet>(operation as OpenAPIV3.OperationObject & { method: string; path: string }, {
      id: 1,
      status: 'sold',
    })

    expect(response.status).toBe(200)
    expect(response.data).toHaveProperty('id', 1)
    expect(response.data).toHaveProperty('status', 'sold')
  })

  it('should delete a pet', async () => {
    // First create a pet to delete
    const createOperation = openApiSpec.paths['/pets']?.post
    if (!createOperation) throw new Error('Operation not found')

    const createResponse = await client.executeOperation<Pet>(
      createOperation as OpenAPIV3.OperationObject & { method: string; path: string },
      {
        name: 'ToDelete',
        species: 'Cat',
        age: 3,
      },
    )
    const petId = createResponse.data.id

    // Then delete it
    const deleteOperation = openApiSpec.paths['/pets/{id}']?.delete
    if (!deleteOperation) throw new Error('Operation not found')

    const deleteResponse = await client.executeOperation(deleteOperation as OpenAPIV3.OperationObject & { method: string; path: string }, {
      id: petId,
    })

    expect(deleteResponse.status).toBe(204)

    // Verify the pet is deleted
    const getOperation = openApiSpec.paths['/pets/{id}']?.get
    if (!getOperation) throw new Error('Operation not found')

    try {
      await client.executeOperation(getOperation as OpenAPIV3.OperationObject & { method: string; path: string }, { id: petId })
      throw new Error('Should not reach here')
    } catch (error: any) {
      expect(error.message).toContain('404')
    }
  })

  it('should handle errors appropriately', async () => {
    const operation = openApiSpec.paths['/pets/{id}']?.get as OpenAPIV3.OperationObject & { method: string; path: string }
    if (!operation) throw new Error('Operation not found')

    try {
      await client.executeOperation(
        operation as OpenAPIV3.OperationObject & { method: string; path: string },
        { id: 99999 }, // Non-existent ID
      )
      throw new Error('Should not reach here')
    } catch (error: any) {
      expect(error.message).toContain('404')
    }
  })
})
