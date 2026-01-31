import { z } from "zod"
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { getOctokit } from "../index.js"

export function registerSearchTools(server: McpServer) {
	// Tool: Search Repositories
	server.tool(
		"search_repositories",
		"Search for GitHub repositories. Returns a concise list with essential information. Use 'get_repository' for detailed information about a specific repository.",
		{
			query: z
				.string()
				.describe(
					"Search query. Examples: 'language:typescript stars:>1000', 'org:facebook react', 'machine learning in:description', 'user:octocat', 'created:>2023-01-01', 'license:mit', 'topic:javascript', 'is:public archived:false'",
				),
			per_page: z
				.number()
				.optional()
				.default(10)
				.describe("Results per page (default 10, max 100)"),
			page: z
				.number()
				.optional()
				.default(1)
				.describe("Page number (default 1)"),
		},
		async ({ query, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.search.repos({
					q: query,
					per_page,
					page,
				})

				// Extract only essential information
				const repositories = response.data.items.map(repo => ({
					full_name: repo.full_name,
					description:
						repo.description?.slice(0, 150) +
						(repo.description && repo.description.length > 150 ? "..." : ""),
					stars: repo.stargazers_count,
					language: repo.language,
					// Only include updated_at if it's recent (within last year)
					...(new Date(repo.updated_at).getTime() >
					Date.now() - 365 * 24 * 60 * 60 * 1000
						? { updated: new Date(repo.updated_at).toISOString().split("T")[0] }
						: {}),
				}))

				// Format as simple text
				const text = repositories
					.map(
						(repo, i) =>
							`${i + 1}. **${repo.full_name}**${repo.stars ? ` - ${repo.stars.toLocaleString()} stars` : ""}${repo.language ? ` - \`${repo.language}\`` : ""}
   ${repo.description || "_No description_"}${repo.updated ? `\n   _Updated: ${repo.updated}_` : ""}`,
					)
					.join("\n\n")

				return {
					content: [
						{
							type: "text",
							text: text
								? `### Found ${repositories.length} repositories:\n\n${text}`
								: "No repositories found",
						},
					],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Search Code
	server.tool(
		"search_code",
		"Search for code across GitHub repositories. Returns a concise list with file paths and repositories. Use 'get_file_contents' for full file content.",
		{
			q: z
				.string()
				.describe(
					"Search query using GitHub code search syntax. Examples: 'addClass in:file language:js', 'repo:owner/name path:src/ extension:py', 'org:github extension:js', 'filename:test.py', 'user:octocat extension:rb', 'console.log path:/src/components', 'TODO in:comments'",
				),
			sort: z
				.enum(["indexed"])
				.optional()
				.describe("Sort field ('indexed' only)"),
			order: z.enum(["asc", "desc"]).optional().describe("Sort order"),
			per_page: z
				.number()
				.optional()
				.default(10)
				.describe("Results per page (default 10, max 100)"),
			page: z
				.number()
				.optional()
				.default(1)
				.describe("Page number (default 1)"),
		},
		async ({ q, sort, order, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.search.code({
					q,
					sort,
					order,
					per_page,
					page,
					mediaType: {
						format: "text-match",
					},
				})

				// Extract only essential information including text matches
				const results = response.data.items.map(item => ({
					repository: item.repository.full_name,
					path: item.path,
					// Only include the first match fragment for conciseness
					match: item.text_matches?.[0]?.fragment?.slice(0, 200) || null,
				}))

				// Format as simple text
				const text = results
					.map(
						(item, i) =>
							`${i + 1}. **${item.repository}** / \`${item.path}\`${item.match ? `\n   \`\`\`\n   ${item.match.replace(/\n/g, " ").trim()}\n   \`\`\`\`` : ""}`,
					)
					.join("\n\n")

				return {
					content: [
						{
							type: "text",
							text: text
								? `### Found ${results.length} code results:\n\n${text}`
								: "No code results found",
						},
					],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Search Users
	server.tool(
		"search_users",
		"Search for GitHub users.",
		{
			q: z
				.string()
				.describe(
					"Search query using GitHub users search syntax. Examples: 'location:\"San Francisco\" followers:>100', 'language:python repos:>50', 'fullname:\"John Doe\"', 'type:user', 'type:org', 'created:>2020-01-01', 'in:email example.com'",
				),
			sort: z
				.enum(["followers", "repositories", "joined"])
				.optional()
				.describe("Sort field by category"),
			order: z.enum(["asc", "desc"]).optional().describe("Sort order"),
			per_page: z
				.number()
				.optional()
				.default(10)
				.describe("Results per page (default 10, max 100)"),
			page: z
				.number()
				.optional()
				.default(1)
				.describe("Page number (default 1)"),
		},
		async ({ q, sort, order, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.search.users({
					q,
					sort,
					order,
					per_page,
					page,
				})

				// Extract only essential information
				const users = response.data.items.map(user => ({
					login: user.login,
					type: user.type,
					// Only include name if it exists and is different from login
					...(user.name && user.name !== user.login ? { name: user.name } : {}),
					// Include bio if it exists (truncated)
					...(user.bio
						? {
								bio:
									user.bio.slice(0, 100) + (user.bio.length > 100 ? "..." : ""),
							}
						: {}),
					// Include location if it exists
					...(user.location ? { location: user.location } : {}),
					// Include company if it exists
					...(user.company ? { company: user.company } : {}),
					// Include public repos if > 0
					...(user.public_repos && user.public_repos > 0
						? { repos: user.public_repos }
						: {}),
					// Only include followers if > 0
					...(user.followers && user.followers > 0
						? { followers: user.followers }
						: {}),
				}))

				// Format as simple text
				const text = users
					.map((user, i) => {
						let line = `${i + 1}. **${user.login}**${user.name ? ` (${user.name})` : ""}${user.type === "Organization" ? " `[org]`" : ""}`
						const details = []
						if (user.followers)
							details.push(`${user.followers.toLocaleString()} followers`)
						if (user.repos) details.push(`${user.repos} repos`)
						if (user.location) details.push(user.location)
						if (user.company) details.push(user.company)
						if (details.length > 0) line += `\n   ${details.join(" • ")}`
						if (user.bio) line += `\n   > ${user.bio}`
						return line
					})
					.join("\n\n")

				return {
					content: [
						{
							type: "text",
							text: text
								? `### Found ${users.length} users:\n\n${text}`
								: "No users found",
						},
					],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)
}
