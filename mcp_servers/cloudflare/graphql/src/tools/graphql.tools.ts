import * as LZString from 'lz-string'
import { z } from 'zod'

import type { GraphQLMCP } from '../graphql.app'

// GraphQL API endpoint
const CLOUDFLARE_GRAPHQL_ENDPOINT = 'https://api.cloudflare.com/client/v4/graphql'

// Type definitions for GraphQL schema responses
interface GraphQLTypeRef {
	kind: string
	name: string | null
	ofType?: GraphQLTypeRef | null
}

interface GraphQLField {
	name: string
	description: string | null
	args: Array<{
		name: string
		description: string | null
		type: GraphQLTypeRef
	}>
	type: GraphQLTypeRef
}

interface GraphQLType {
	name: string
	kind: string
	description: string | null
	fields?: GraphQLField[] | null
	inputFields?: Array<{
		name: string
		description: string | null
		type: GraphQLTypeRef
	}> | null
	interfaces?: Array<{ name: string }> | null
	enumValues?: Array<{
		name: string
		description: string | null
	}> | null
	possibleTypes?: Array<{ name: string }> | null
}

interface SchemaOverviewResponse {
	data: {
		__schema: {
			queryType: { name: string } | null
			mutationType: { name: string } | null
			subscriptionType: { name: string } | null
			types: Array<{
				name: string
				kind: string
				description: string | null
			}>
		}
	}
}

interface TypeDetailsResponse {
	data: {
		__type: GraphQLType
	}
}

// Define the structure of a single error
const graphQLErrorSchema = z.object({
	message: z.string(),
	path: z.array(z.union([z.string(), z.number()])),
	extensions: z.object({
		code: z.string(),
		timestamp: z.string(),
		ray_id: z.string(),
	}),
})

// Define the overall GraphQL response schema
const graphQLResponseSchema = z.object({
	data: z.union([z.record(z.unknown()), z.null()]),
	errors: z.union([z.array(graphQLErrorSchema), z.null()]),
})

/**
 * Fetches the high-level overview of the GraphQL schema
 * @param apiToken Cloudflare API token
 * @returns Basic schema structure
 */
async function fetchSchemaOverview(apiToken: string): Promise<SchemaOverviewResponse> {
	const overviewQuery = `
		query SchemaOverview {
			__schema {
				queryType { name }
				mutationType { name }
				subscriptionType { name }
				types {
					name
					kind
					description
				}
			}
		}
	`

	const response = await executeGraphQLRequest<SchemaOverviewResponse>(overviewQuery, apiToken)
	return response
}

/**
 * Fetches detailed information about a specific GraphQL type
 * @param typeName The name of the type to fetch details for
 * @param apiToken Cloudflare API token
 * @returns Detailed type information
 */
async function fetchTypeDetails(typeName: string, apiToken: string): Promise<TypeDetailsResponse> {
	const typeDetailsQuery = `
		query TypeDetails {
			__type(name: "${typeName}") {
				name
				kind
				description
				fields(includeDeprecated: false) {
					name
					description
					args {
						name
						description
						type {
							kind
							name
							ofType {
								kind
								name
							}
						}
					}
					type {
						kind
						name
						ofType {
							kind
							name
							ofType {
								kind
								name
							}
						}
					}
				}
				inputFields {
					name
					description
					type {
						kind
						name
						ofType {
							kind
							name
						}
					}
				}
				interfaces {
					name
				}
				enumValues(includeDeprecated: false) {
					name
					description
				}
				possibleTypes {
					name
				}
			}
		}
	`

	const response = await executeGraphQLRequest<TypeDetailsResponse>(typeDetailsQuery, apiToken)
	return response
}

/**
 * Helper function to execute GraphQL requests
 * @param query GraphQL query to execute
 * @param apiToken Cloudflare API token
 * @returns Response data
 */
async function executeGraphQLRequest<T>(query: string, apiToken: string): Promise<T> {
	const response = await fetch(CLOUDFLARE_GRAPHQL_ENDPOINT, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${apiToken}`,
		},
		body: JSON.stringify({ query }),
	})

	if (!response.ok) {
		throw new Error(`Failed to execute GraphQL request: ${response.statusText}`)
	}

	const data = graphQLResponseSchema.parse(await response.json())

	// Check for GraphQL errors in the response
	if (data && data.errors && Array.isArray(data.errors) && data.errors.length > 0) {
		const errorMessages = data.errors.map((e: { message: string }) => e.message).join(', ')
		console.warn(`GraphQL errors: ${errorMessages}`)

		// If the error is about mutations not being supported, we can handle it gracefully
		if (errorMessages.includes('Mutations are not supported')) {
			console.info('Mutations are not supported by the Cloudflare GraphQL API')
		}
	}

	return data as T
}

/**
 * Executes a GraphQL query against Cloudflare's API
 * @param query The GraphQL query to execute
 * @param variables Variables for the query
 * @param apiToken Cloudflare API token
 * @returns The query results
 */
async function executeGraphQLQuery(query: string, variables: any, apiToken: string) {
	// Clone the variables to avoid modifying the original
	const queryVariables = { ...variables }

	const response = await fetch(CLOUDFLARE_GRAPHQL_ENDPOINT, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${apiToken}`,
		},
		body: JSON.stringify({
			query,
			variables: queryVariables,
		}),
	})

	if (!response.ok) {
		throw new Error(`Failed to execute GraphQL query: ${response.statusText}`)
	}

	const result = graphQLResponseSchema.parse(await response.json())

	// Check for GraphQL errors in the response
	if (result && result.errors && Array.isArray(result.errors) && result.errors.length > 0) {
		const errorMessages = result.errors.map((e: { message: string }) => e.message).join(', ')
		console.warn(`GraphQL query errors: ${errorMessages}`)
	}

	return result
}

/**
 * Searches for matching types and fields in a GraphQL schema
 * @param schema The GraphQL schema to search
 * @param keyword The keyword to search for
 * @param typeDetails Optional map of type details for deeper searching
 * @returns Matching types and fields
 */
async function searchGraphQLSchema(
	schema: SchemaOverviewResponse,
	keyword: string,
	accountId: string,
	apiToken: string,
	maxDetailsToFetch: number = 10,
	onlyObjectTypes: boolean = true
) {
	const normalizedKeyword = keyword.toLowerCase()
	const results = {
		types: [] as Array<{
			name: string
			kind: string
			description: string | null
			matchReason: string
		}>,
		fields: [] as Array<{
			typeName: string
			fieldName: string
			description: string | null
			matchReason: string
		}>,
		enumValues: [] as Array<{
			typeName: string
			enumValue: string
			description: string | null
			matchReason: string
		}>,
		args: [] as Array<{
			typeName: string
			fieldName: string
			argName: string
			description: string | null
			matchReason: string
		}>,
	}

	// First pass: Search through type names and descriptions
	const matchingTypeNames: string[] = []

	for (const type of schema.data.__schema.types || []) {
		// Skip internal types (those starting with __)
		if (type.name?.startsWith('__')) continue

		// Check if type name or description matches
		if (type.name?.toLowerCase().includes(normalizedKeyword)) {
			results.types.push({
				...type,
				matchReason: `Type name contains "${keyword}"`,
			})
			matchingTypeNames.push(type.name)
		} else if (type.description?.toLowerCase().includes(normalizedKeyword)) {
			results.types.push({
				...type,
				matchReason: `Type description contains "${keyword}"`,
			})
			matchingTypeNames.push(type.name)
		}
	}

	// Second pass: For potentially relevant types, fetch details and search deeper
	// Start with matching types, then add important schema types if we have capacity
	let typesToExamine = [...matchingTypeNames]

	// Add root operation types if they're not already included
	const rootTypes = [
		schema.data.__schema.queryType?.name,
		schema.data.__schema.mutationType?.name,
		schema.data.__schema.subscriptionType?.name,
	].filter(Boolean) as string[]

	for (const rootType of rootTypes) {
		if (!typesToExamine.includes(rootType)) {
			typesToExamine.push(rootType)
		}
	}

	// Add object types that might contain relevant fields
	const objectTypes = schema.data.__schema.types
		.filter((t) => {
			// If onlyObjectTypes is true, only include OBJECT types
			if (onlyObjectTypes) {
				return t.kind === 'OBJECT' && !t.name.startsWith('__')
			}
			// Otherwise include both OBJECT and INTERFACE types
			return (t.kind === 'OBJECT' || t.kind === 'INTERFACE') && !t.name.startsWith('__')
		})
		.map((t) => t.name)

	// Combine all potential types to examine, but limit to a reasonable number
	typesToExamine = [...new Set([...typesToExamine, ...objectTypes])].slice(0, maxDetailsToFetch)

	// Fetch details for these types and search through their fields
	for (const typeName of typesToExamine) {
		try {
			const typeDetails = await fetchTypeDetails(typeName, apiToken)
			const type = typeDetails.data.__type

			if (!type) continue

			// Search through fields
			if (type.fields) {
				for (const field of type.fields) {
					// Check if field name or description matches
					if (field.name.toLowerCase().includes(normalizedKeyword)) {
						results.fields.push({
							typeName: type.name,
							fieldName: field.name,
							description: field.description,
							matchReason: `Field name contains "${keyword}"`,
						})
					} else if (field.description?.toLowerCase().includes(normalizedKeyword)) {
						results.fields.push({
							typeName: type.name,
							fieldName: field.name,
							description: field.description,
							matchReason: `Field description contains "${keyword}"`,
						})
					}

					// Search through field arguments
					if (field.args) {
						for (const arg of field.args) {
							if (arg.name.toLowerCase().includes(normalizedKeyword)) {
								results.args.push({
									typeName: type.name,
									fieldName: field.name,
									argName: arg.name,
									description: arg.description,
									matchReason: `Argument name contains "${keyword}"`,
								})
							} else if (arg.description?.toLowerCase().includes(normalizedKeyword)) {
								results.args.push({
									typeName: type.name,
									fieldName: field.name,
									argName: arg.name,
									description: arg.description,
									matchReason: `Argument description contains "${keyword}"`,
								})
							}
						}
					}
				}
			}

			// Search through enum values
			if (type.enumValues) {
				for (const enumValue of type.enumValues) {
					if (enumValue.name.toLowerCase().includes(normalizedKeyword)) {
						results.enumValues.push({
							typeName: type.name,
							enumValue: enumValue.name,
							description: enumValue.description,
							matchReason: `Enum value contains "${keyword}"`,
						})
					} else if (enumValue.description?.toLowerCase().includes(normalizedKeyword)) {
						results.enumValues.push({
							typeName: type.name,
							enumValue: enumValue.name,
							description: enumValue.description,
							matchReason: `Enum value description contains "${keyword}"`,
						})
					}
				}
			}
		} catch (error) {
			console.error(`Error fetching details for type ${typeName}:`, error)
		}
	}

	return results
}

/**
 * Registers GraphQL tools with the MCP server
 * @param agent The MCP agent instance
 */
export function registerGraphQLTools(agent: GraphQLMCP) {
	// Tool to search the GraphQL schema for types, fields, and enum values matching a keyword
	agent.server.tool(
		'graphql_schema_search',
		`Search the Cloudflare GraphQL API schema for types, fields, and enum values matching a keyword

		Use this tool when:

			- You are unsure which dataset to use for your query.
			- A user is looking for specific types, fields, or enum values in the Cloudflare GraphQL API schema.

		IMPORTANT GUIDELINES:
			- DO NOT query for dimensions unless the user explicitly asked to group by or show dimensions.
			- Only include fields that the user specifically requested in their query.
			- Keep queries as simple as possible while fulfilling the user's request.

		Workflow:
			1. Use this tool to search for dataset types by keyword.
			2. When a relevant dataset type is found, immediately use graphql_schema_details to get the complete structure of that dataset.
			3. After understanding the schema structure, proceed directly to constructing and executing queries using the graphql_query tool.
			4. Do not use graphql_schema_overview or graphql_complete_schema after finding the relevant dataset - these are redundant steps.

		This tool searches the Cloudflare GraphQL API schema for any schema elements (such as object types, field names, or enum options) that match a given keyword. It returns schema fragments and definitions to assist in constructing valid and precise GraphQL queries.
		`,
		{
			keyword: z.string().describe('The keyword to search for in the schema'),
			maxDetailsToFetch: z
				.number()
				.min(1)
				.max(50)
				.default(10)
				.describe('Maximum number of types to fetch details for'),
			includeInternalTypes: z
				.boolean()
				.default(false)
				.describe(
					'Whether to include internal types (those starting with __) in the search results'
				),
			onlyObjectTypes: z
				.boolean()
				.default(true)
				.describe(
					'Whether to only include OBJECT kind types in the search results with descriptions'
				),
		},
		async (params) => {
			const {
				keyword,
				maxDetailsToFetch = 10,
				includeInternalTypes = false,
				onlyObjectTypes = true,
			} = params
			const accountId = await agent.getActiveAccountId()
			if (!accountId) {
				return {
					content: [
						{
							type: 'text',
							text: 'No currently active accountId. Try listing your accounts (accounts_list) and then setting an active account (set_active_account)',
						},
					],
				}
			}

			try {
				// First fetch the schema overview
				const schemaOverview = await fetchSchemaOverview(agent.props.accessToken)

				// Search the schema for the keyword
				const searchResults = await searchGraphQLSchema(
					schemaOverview,
					keyword,
					accountId,
					agent.props.accessToken,
					maxDetailsToFetch,
					onlyObjectTypes
				)

				// Filter out internal types if requested
				if (!includeInternalTypes) {
					searchResults.types = searchResults.types.filter((t) => !t.name.startsWith('__'))
					searchResults.fields = searchResults.fields.filter((f) => !f.typeName.startsWith('__'))
					searchResults.enumValues = searchResults.enumValues.filter(
						(e) => !e.typeName.startsWith('__')
					)
					searchResults.args = searchResults.args.filter((a) => !a.typeName.startsWith('__'))
				}

				// Filter out items without descriptions when onlyObjectTypes is true
				if (onlyObjectTypes) {
					searchResults.types = searchResults.types.filter((t) => {
						return t.description && t.description.trim() !== ''
					})
					searchResults.fields = searchResults.fields.filter((f) => {
						return f.description && f.description.trim() !== ''
					})
					searchResults.enumValues = searchResults.enumValues.filter((e) => {
						return e.description && e.description.trim() !== ''
					})
					searchResults.args = searchResults.args.filter((a) => {
						return a.description && a.description.trim() !== ''
					})
				}

				// Add summary information
				const results = {
					keyword,
					summary: {
						totalMatches:
							searchResults.types.length +
							searchResults.fields.length +
							searchResults.enumValues.length +
							searchResults.args.length,
						typeMatches: searchResults.types.length,
						fieldMatches: searchResults.fields.length,
						enumValueMatches: searchResults.enumValues.length,
						argumentMatches: searchResults.args.length,
					},
					results: searchResults,
				}

				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify(results),
						},
					],
				}
			} catch (error) {
				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify({
								error: `Error searching GraphQL schema: ${error instanceof Error ? error.message : String(error)}`,
							}),
						},
					],
				}
			}
		}
	)

	// Tool to fetch the GraphQL schema overview (high-level structure)
	agent.server.tool(
		'graphql_schema_overview',
		`Fetch the high-level overview of the Cloudflare GraphQL API schema
		
		Use this tool when:

			- A user requests insights into the structure or capabilities of Cloudflare’s GraphQL API.
			- You need to explore available types, queries, mutations, or schema relationships exposed by Cloudflare’s GraphQL interface.
			- You're generating or validating GraphQL queries against Cloudflare’s schema.
			- You are troubleshooting or developing integrations with Cloudflare’s API and require up-to-date schema information.

		This tool returns a high-level summary of the Cloudflare GraphQL API schema. It provides a structured outline of API entry points, data models, and relationships to help guide query construction or system integration.
		`,
		{
			pageSize: z
				.number()
				.min(10)
				.max(1000)
				.default(100)
				.describe('Number of types to return per page'),
			page: z.number().min(1).default(1).describe('Page number to fetch'),
		},
		async (params) => {
			const { pageSize = 100, page = 1 } = params
			const accountId = await agent.getActiveAccountId()
			if (!accountId) {
				return {
					content: [
						{
							type: 'text',
							text: 'No currently active accountId. Try listing your accounts (accounts_list) and then setting an active account (set_active_account)',
						},
					],
				}
			}

			try {
				const schemaOverview = await fetchSchemaOverview(agent.props.accessToken)

				// Apply pagination to the types array
				const allTypes = schemaOverview.data.__schema.types || []
				const totalTypes = allTypes.length
				const totalPages = Math.ceil(totalTypes / pageSize)

				// Calculate start and end indices for the current page
				const startIndex = (page - 1) * pageSize
				const endIndex = Math.min(startIndex + pageSize, totalTypes)

				// Create a paginated version of the schema
				const paginatedSchema = {
					data: {
						__schema: {
							queryType: schemaOverview.data.__schema.queryType,
							mutationType: schemaOverview.data.__schema.mutationType,
							subscriptionType: schemaOverview.data.__schema.subscriptionType,
							types: allTypes.slice(startIndex, endIndex),
						},
					},
					pagination: {
						page,
						pageSize,
						totalTypes,
						totalPages,
						hasNextPage: page < totalPages,
						hasPreviousPage: page > 1,
					},
				}

				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify(paginatedSchema),
						},
					],
				}
			} catch (error) {
				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify({
								error: `Error fetching GraphQL schema overview: ${error instanceof Error ? error.message : String(error)}`,
							}),
						},
					],
				}
			}
		}
	)

	// Tool to fetch detailed information about a specific GraphQL type
	agent.server.tool(
		'graphql_type_details',
		`Fetch detailed information about a specific GraphQL type (dataset)

		IMPORTANT: After exploring the schema, DO NOT generate overly complicated GraphQL queries that the user didn't explicitly ask for. Only include fields that were specifically requested.

		Use this tool when:

			- You need to explore the fields by the type name (dataset) for detailed information
			- You're building or debugging GraphQL queries and want to ensure the correct usage of schema components
			- You need contextual information about how a certain concept or object is represented in Cloudflare's GraphQL API.

		Guidelines for query construction:
			- Keep queries as simple as possible while fulfilling the user's request
			- Only include fields that the user specifically asked for
			- Do not add dimensions or additional fields unless explicitly requested
			- When in doubt, ask the user for clarification rather than creating a complex query
		`,
		{
			typeName: z
				.string()
				.describe('The type name (dataset) of the GraphQL type to fetch details for'),
			fieldsPageSize: z
				.number()
				.min(5)
				.max(500)
				.default(50)
				.describe('Number of fields to return per page'),
			fieldsPage: z.number().min(1).default(1).describe('Page number for fields to fetch'),
			enumValuesPageSize: z
				.number()
				.min(5)
				.max(500)
				.default(50)
				.describe('Number of enum values to return per page'),
			enumValuesPage: z.number().min(1).default(1).describe('Page number for enum values to fetch'),
		},
		async (params) => {
			const {
				typeName,
				fieldsPageSize = 50,
				fieldsPage = 1,
				enumValuesPageSize = 50,
				enumValuesPage = 1,
			} = params

			const accountId = await agent.getActiveAccountId()
			if (!accountId) {
				return {
					content: [
						{
							type: 'text',
							text: 'No currently active accountId. Try listing your accounts (accounts_list) and then setting an active account (set_active_account)',
						},
					],
				}
			}

			try {
				const typeDetails = await fetchTypeDetails(typeName, agent.props.accessToken)

				// Apply pagination to fields if they exist
				const allFields = typeDetails.data.__type.fields || []
				const totalFields = allFields.length
				const totalFieldsPages = Math.ceil(totalFields / fieldsPageSize)

				// Calculate start and end indices for the fields page
				const fieldsStartIndex = (fieldsPage - 1) * fieldsPageSize
				const fieldsEndIndex = Math.min(fieldsStartIndex + fieldsPageSize, totalFields)

				// Apply pagination to enum values if they exist
				const allEnumValues = typeDetails.data.__type.enumValues || []
				const totalEnumValues = allEnumValues.length
				const totalEnumValuesPages = Math.ceil(totalEnumValues / enumValuesPageSize)

				// Calculate start and end indices for the enum values page
				const enumValuesStartIndex = (enumValuesPage - 1) * enumValuesPageSize
				const enumValuesEndIndex = Math.min(
					enumValuesStartIndex + enumValuesPageSize,
					totalEnumValues
				)

				// Create a paginated version of the type details
				const paginatedTypeDetails = {
					data: {
						__type: {
							...typeDetails.data.__type,
							fields: allFields.slice(fieldsStartIndex, fieldsEndIndex),
							enumValues: allEnumValues.slice(enumValuesStartIndex, enumValuesEndIndex),
						},
					},
					pagination: {
						fields: {
							page: fieldsPage,
							pageSize: fieldsPageSize,
							totalFields,
							totalPages: totalFieldsPages,
							hasNextPage: fieldsPage < totalFieldsPages,
							hasPreviousPage: fieldsPage > 1,
						},
						enumValues: {
							page: enumValuesPage,
							pageSize: enumValuesPageSize,
							totalEnumValues,
							totalPages: totalEnumValuesPages,
							hasNextPage: enumValuesPage < totalEnumValuesPages,
							hasPreviousPage: enumValuesPage > 1,
						},
					},
				}

				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify(paginatedTypeDetails),
						},
					],
				}
			} catch (error) {
				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify({
								error: `Error fetching type details: ${error instanceof Error ? error.message : String(error)}`,
							}),
						},
					],
				}
			}
		}
	)

	// Tool to fetch the complete GraphQL schema (combines overview and important type details)
	agent.server.tool(
		'graphql_complete_schema',
		'Fetch the complete Cloudflare GraphQL API schema (combines overview and important type details)',
		{
			typesPageSize: z
				.number()
				.min(10)
				.max(500)
				.default(100)
				.describe('Number of types to return per page'),
			typesPage: z.number().min(1).default(1).describe('Page number for types to fetch'),
			includeRootTypeDetails: z
				.boolean()
				.default(true)
				.describe('Whether to include detailed information about root types'),
			maxTypeDetailsToFetch: z
				.number()
				.min(0)
				.max(10)
				.default(3)
				.describe('Maximum number of important types to fetch details for'),
		},
		async (params) => {
			const {
				typesPageSize = 100,
				typesPage = 1,
				includeRootTypeDetails = true,
				maxTypeDetailsToFetch = 3,
			} = params

			const accountId = await agent.getActiveAccountId()
			if (!accountId) {
				return {
					content: [
						{
							type: 'text',
							text: 'No currently active accountId. Try listing your accounts (accounts_list) and then setting an active account (set_active_account)',
						},
					],
				}
			}

			try {
				// First fetch the schema overview
				const schemaOverview = await fetchSchemaOverview(agent.props.accessToken)

				// Apply pagination to the types array
				const allTypes = schemaOverview.data.__schema.types || []
				const totalTypes = allTypes.length
				const totalPages = Math.ceil(totalTypes / typesPageSize)

				// Calculate start and end indices for the current page
				const startIndex = (typesPage - 1) * typesPageSize
				const endIndex = Math.min(startIndex + typesPageSize, totalTypes)

				// Get the paginated types
				const paginatedTypes = allTypes.slice(startIndex, endIndex)

				// Create the base schema with paginated types
				const schema: {
					data: {
						__schema: {
							queryType: { name: string } | null
							mutationType: { name: string } | null
							subscriptionType: { name: string } | null
							types: Array<{
								name: string
								kind: string
								description: string | null
							}>
						}
					}
					typeDetails: Record<string, GraphQLType>
					pagination: {
						types: {
							page: number
							pageSize: number
							totalTypes: number
							totalPages: number
							hasNextPage: boolean
							hasPreviousPage: boolean
						}
					}
				} = {
					data: {
						__schema: {
							queryType: schemaOverview.data.__schema.queryType,
							mutationType: schemaOverview.data.__schema.mutationType,
							subscriptionType: schemaOverview.data.__schema.subscriptionType,
							types: paginatedTypes,
						},
					},
					typeDetails: {} as Record<string, GraphQLType>,
					pagination: {
						types: {
							page: typesPage,
							pageSize: typesPageSize,
							totalTypes,
							totalPages,
							hasNextPage: typesPage < totalPages,
							hasPreviousPage: typesPage > 1,
						},
					},
				}

				// If requested, fetch details for root types
				if (includeRootTypeDetails) {
					// Identify important root types
					const rootTypes = [
						schemaOverview.data.__schema.queryType?.name,
						...(schemaOverview.data.__schema.mutationType?.name
							? [schemaOverview.data.__schema.mutationType.name]
							: []),
					].filter(Boolean) as string[]

					// Limit the number of types to fetch details for
					const typesToFetch = rootTypes.slice(0, maxTypeDetailsToFetch)

					// Fetch details for each type
					for (const typeName of typesToFetch) {
						try {
							const typeDetails = await fetchTypeDetails(typeName, agent.props.accessToken)
							if (typeDetails.data.__type) {
								schema.typeDetails[typeName] = typeDetails.data.__type
							}
						} catch (error) {
							console.error(`Error fetching details for type ${typeName}:`, error)
						}
					}
				}

				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify(schema),
						},
					],
				}
			} catch (error) {
				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify({
								error: `Error fetching GraphQL schema: ${error instanceof Error ? error.message : String(error)}`,
							}),
						},
					],
				}
			}
		}
	)

	// Tool to execute a GraphQL query
	agent.server.tool(
		'graphql_query',
		`Execute a GraphQL query against the Cloudflare API

		IMPORTANT: ONLY execute the EXACT GraphQL query provided by the user. DO NOT generate complicated queries that the user didn't explicitly ask for.

		CRITICAL: When querying, make sure to set a LIMIT (e.g., first: 10, limit: 20) otherwise the response may be too large for the MCP server to process.

		Use this tool when:

			- A user provides a GraphQL query and expects real-time data from Cloudflare's API.
			- You need to retrieve live information from Cloudflare, such as analytics, logs, account data, or configuration details.
			- You want to validate the behavior of a GraphQL query or inspect its runtime results.

		This tool sends a user-defined GraphQL query to the Cloudflare API and returns the raw response exactly as received. When filtering or querying by time, use ISO 8601 datetime format (e.g., "2020-08-03T02:07:05Z").

		For each query execution, a clickable GraphQL API Explorer link will be provided in the response. Users can click this link to open the query in Cloudflare's GraphQL Explorer interface where they can further modify and experiment with the query.

		Guidelines:
			- Only use the exact query provided by the user. Do not modify or expand it unless explicitly requested.
			- Always suggest including limits in queries (e.g., first: 10, limit: 20) to prevent response size issues.
			- If a query fails due to size limits, advise the user to add or reduce limits in their query.
		`,
		{
			query: z.string().describe('The GraphQL query to execute'),
			variables: z.record(z.any()).optional().describe('Variables for the query'),
		},
		async (params) => {
			const accountId = await agent.getActiveAccountId()
			if (!accountId) {
				return {
					content: [
						{
							type: 'text',
							text: 'No currently active accountId. Try listing your accounts (accounts_list) and then setting an active account (set_active_account)',
						},
					],
				}
			}

			try {
				const { query, variables = {} } = params

				// Execute the GraphQL query and get the raw result
				const result = await executeGraphQLQuery(query, variables, agent.props.accessToken)

				// Generate GraphQL API Explorer link for this query
				const compressedQuery = LZString.compressToEncodedURIComponent(query)
				const compressedVariables = LZString.compressToEncodedURIComponent(
					JSON.stringify(variables)
				)
				const explorerUrl = `https://graphql.cloudflare.com/explorer?query=${compressedQuery}&variables=${compressedVariables}`

				// Check if the response is too large (MCP server will fail if > 1MB)
				const resultString = JSON.stringify(result)
				const SIZE_LIMIT = 800000 // Set a safer limit (800KB) to ensure we stay under 1MB
				if (resultString.length > SIZE_LIMIT) {
					return {
						content: [
							{
								type: 'text',
								text: `ERROR: Query result exceeds size limit (${Math.round(resultString.length / 1024)}KB). MCP server will fail with results larger than 1MB. Please use a lower LIMIT in your GraphQL query to reduce the number of returned items. For example:

- Add 'first: 10' or 'limit: 10' parameters to your query
- Reduce the number of requested fields
- Add more specific filters to narrow down results`,
							},
						],
					}
				}

				return {
					content: [
						{
							type: 'text',
							text: `${resultString}\n\n**[Open in GraphQL Explorer](${explorerUrl})**\nClick the link above to view and modify this query in the Cloudflare GraphQL API Explorer.`,
						},
					],
				}
			} catch (error) {
				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify({
								error: `Error executing GraphQL query: ${error instanceof Error ? error.message : String(error)}`,
							}),
						},
					],
				}
			}
		}
	)

	// Tool to generate a GraphQL API Explorer link
	agent.server.tool(
		'graphql_api_explorer',
		`Generate a Cloudflare GraphQL API Explorer link

		Use this tool when:

			- A user asks for any GraphQL queries and wants to explore them in the Cloudflare GraphQL API Explorer.
			- You want to provide a shareable link to a specific GraphQL query for the user to explore and modify.
			- You need to help the user visualize or interact with GraphQL queries in a user-friendly interface.

		This tool generates a direct link to the Cloudflare GraphQL API Explorer with a pre-populated query and variables.
		The response includes a clickable Markdown link that users can click to open the query in Cloudflare's interactive GraphQL playground.
		The original query and variables are also displayed for reference.
		`,
		{
			query: z.string().describe('The GraphQL query to include in the explorer link'),
			variables: z.record(z.any()).optional().describe('Variables for the query in JSON format'),
		},
		async (params) => {
			try {
				const { query, variables = {} } = params

				// Compress the query and variables using lz-string
				const compressedQuery = LZString.compressToEncodedURIComponent(query)
				const compressedVariables = LZString.compressToEncodedURIComponent(
					JSON.stringify(variables)
				)

				// Generate the GraphQL API Explorer URL
				const explorerUrl = `https://graphql.cloudflare.com/explorer?query=${compressedQuery}&variables=${compressedVariables}`

				return {
					content: [
						{
							type: 'text',
							text: `**[Open in GraphQL Explorer](${explorerUrl})**\n\nYou can click the link above to open the Cloudflare GraphQL API Explorer with your query pre-populated.\n\n**Query:**\n\`\`\`graphql\n${query}\n\`\`\`\n\n${Object.keys(variables).length > 0 ? `**Variables:**\n\`\`\`json\n${JSON.stringify(variables, null, 2)}\n\`\`\`\n` : ''}`,
						},
					],
				}
			} catch (error) {
				return {
					content: [
						{
							type: 'text',
							text: JSON.stringify({
								error: `Error generating GraphQL API Explorer link: ${error instanceof Error ? error.message : String(error)}`,
							}),
						},
					],
				}
			}
		}
	)
}
