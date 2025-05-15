import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { HttpClient } from '../http-client.js'
import type express from 'express'
//@ts-ignore
import { createPetstoreServer } from '../../../examples/petstore-server.cjs'
import type { OpenAPIV3 } from 'openapi-types'
import axios from 'axios'

interface Pet {
  id: number
  name: string
  species: string
  age: number
  status: 'available' | 'pending' | 'sold'
}

describe('HttpClient Integration Tests', () => {
  const PORT = 3456
  const BASE_URL = `http://localhost:${PORT}`
  let server: ReturnType<typeof express>
  let openApiSpec: OpenAPIV3.Document
  let client: HttpClient

  beforeAll(async () => {
    // Start the petstore server
    server = createPetstoreServer(PORT) as unknown as express.Express

    // Fetch the OpenAPI spec from the server
    const response = await axios.get(`${BASE_URL}/openapi.json`)
    openApiSpec = response.data

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

  afterAll(() => {
    //@ts-expect-error
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
