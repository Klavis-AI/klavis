import { z } from "zod"
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { getOctokit } from "../index.js"

export function registerIssueTools(server: McpServer) {
	// Tool: Get Issue
	server.tool(
		"get_issue",
		"Get details of a specific issue in a GitHub repository.",
		{
			owner: z.string().describe("The owner of the repository"),
			repo: z.string().describe("The name of the repository"),
			issue_number: z.number().describe("The number of the issue"),
		},
		async ({ owner, repo, issue_number }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.issues.get({
					owner,
					repo,
					issue_number,
				})
				return {
					content: [{ type: "text", text: JSON.stringify(response.data) }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Add Issue Comment
	server.tool(
		"add_issue_comment",
		"Add a comment to a specific issue in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			issue_number: z.number().describe("Issue number to comment on"),
			body: z.string().describe("Comment content"),
		},
		async ({ owner, repo, issue_number, body }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.issues.createComment({
					owner,
					repo,
					issue_number,
					body,
				})
				return {
					content: [{ type: "text", text: JSON.stringify(response.data) }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Search Issues
	server.tool(
		"search_issues",
		"Search for issues in GitHub repositories.",
		{
			q: z.string().describe("Search query using GitHub issues search syntax"),
			sort: z
				.enum([
					"comments",
					"reactions",
					"reactions-+1",
					"reactions--1",
					"reactions-smile",
					"reactions-thinking_face",
					"reactions-heart",
					"reactions-tada",
					"interactions",
					"created",
					"updated",
				])
				.optional()
				.describe(
					"Sort field by number of matches of categories, defaults to best match",
				),
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
				const response = await octokit.rest.search.issuesAndPullRequests({
					q,
					sort,
					order,
					per_page,
					page,
				})

				// Format the response as clean markdown
				const items = response.data.items
				const totalCount = response.data.total_count

				if (items.length === 0) {
					return {
						content: [
							{ type: "text", text: "No issues found matching your search." },
						],
					}
				}

				let markdown = `# Search Results\n\n`
				markdown += `Found ${totalCount} total result(s), showing ${items.length}\n\n`
				markdown += `**Query**: ${q}\n\n`

				items.forEach(item => {
					const type = item.pull_request ? "PR" : "Issue"
					markdown += `## ${type} #${item.number}: ${item.title}\n\n`
					markdown += `- **Repository**: ${item.repository_url.split("/").slice(-2).join("/")}\n`
					markdown += `- **State**: ${item.state}\n`
					markdown += `- **Author**: ${item.user?.login || "Unknown"}\n`
					markdown += `- **Created**: ${new Date(item.created_at).toLocaleDateString()}\n`
					markdown += `- **Updated**: ${new Date(item.updated_at).toLocaleDateString()}\n`

					if (item.labels && item.labels.length > 0) {
						markdown += `- **Labels**: ${item.labels.map(l => l.name).join(", ")}\n`
					}

					if (item.assignees && item.assignees.length > 0) {
						markdown += `- **Assignees**: ${item.assignees.map(a => a.login).join(", ")}\n`
					}

					markdown += `- **Comments**: ${item.comments}\n`
					markdown += `- **URL**: ${item.html_url}\n`
					markdown += `\n`
				})

				return {
					content: [{ type: "text", text: markdown }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Create Issue
	server.tool(
		"create_issue",
		"Create a new issue in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			title: z.string().describe("Issue title"),
			body: z.string().optional().describe("Issue body content"),
			assignees: z
				.array(z.string())
				.optional()
				.describe("Usernames to assign to this issue"),
			labels: z
				.array(z.string())
				.optional()
				.describe("Labels to apply to this issue"),
			milestone: z.number().optional().describe("Milestone number"),
		},
		async ({ owner, repo, title, body, assignees, labels, milestone }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.issues.create({
					owner,
					repo,
					title,
					body,
					assignees,
					labels,
					milestone,
				})
				return {
					content: [{ type: "text", text: JSON.stringify(response.data) }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: List Issues
	server.tool(
		"list_issues",
		"List issues in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			state: z
				.enum(["open", "closed", "all"])
				.optional()
				.describe("Filter by state"),
			labels: z.array(z.string()).optional().describe("Filter by labels"),
			sort: z
				.enum(["created", "updated", "comments"])
				.optional()
				.describe("Sort order"),
			direction: z.enum(["asc", "desc"]).optional().describe("Sort direction"),
			since: z
				.string()
				.optional()
				.describe("Filter by date (ISO 8601 timestamp)"),
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
		async ({
			owner,
			repo,
			state,
			labels,
			sort,
			direction,
			since,
			per_page,
			page,
		}) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.issues.listForRepo({
					owner,
					repo,
					state,
					labels: labels ? labels.join(",") : undefined,
					sort,
					direction,
					since,
					per_page,
					page,
				})

				// Format the response as clean markdown
				const issues = response.data.filter(item => !item.pull_request) // Filter out PRs

				if (issues.length === 0) {
					return {
						content: [{ type: "text", text: "No issues found." }],
					}
				}

				let markdown = `# Issues for ${owner}/${repo}\n\n`
				markdown += `Showing ${issues.length} issue(s) - Page ${page}\n`
				if (response.data.length === per_page) {
					markdown += `*Note: More results may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				issues.forEach(issue => {
					markdown += `## #${issue.number}: ${issue.title}\n\n`
					markdown += `- **State**: ${issue.state}\n`
					markdown += `- **Author**: ${issue.user?.login || "Unknown"}\n`
					markdown += `- **Created**: ${new Date(issue.created_at).toLocaleDateString()}\n`
					markdown += `- **Updated**: ${new Date(issue.updated_at).toLocaleDateString()}\n`

					if (issue.labels && issue.labels.length > 0) {
						markdown += `- **Labels**: ${issue.labels.map(l => (typeof l === "string" ? l : l.name)).join(", ")}\n`
					}

					if (issue.assignees && issue.assignees.length > 0) {
						markdown += `- **Assignees**: ${issue.assignees.map(a => a.login).join(", ")}\n`
					}

					if (issue.milestone) {
						markdown += `- **Milestone**: ${issue.milestone.title}\n`
					}

					markdown += `- **Comments**: ${issue.comments}\n`
					markdown += `- **URL**: ${issue.html_url}\n`
					markdown += `\n`
				})

				return {
					content: [{ type: "text", text: markdown }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Update Issue
	server.tool(
		"update_issue",
		"Update an existing issue in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			issue_number: z.number().describe("Issue number to update"),
			title: z.string().optional().describe("New title"),
			body: z.string().optional().describe("New description"),
			state: z.enum(["open", "closed"]).optional().describe("New state"),
			labels: z.array(z.string()).optional().describe("New labels"),
			assignees: z.array(z.string()).optional().describe("New assignees"),
			milestone: z.number().optional().describe("New milestone number"),
		},
		async ({
			owner,
			repo,
			issue_number,
			title,
			body,
			state,
			labels,
			assignees,
			milestone,
		}) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.issues.update({
					owner,
					repo,
					issue_number,
					title,
					body,
					state,
					labels,
					assignees,
					milestone,
				})
				return {
					content: [{ type: "text", text: JSON.stringify(response.data) }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Get Issue Comments
	server.tool(
		"get_issue_comments",
		"Get comments for a specific issue in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			issue_number: z.number().describe("Issue number"),
			page: z.number().optional().default(1).describe("Page number"),
			per_page: z
				.number()
				.optional()
				.default(10)
				.describe("Number of records per page"),
		},
		async ({ owner, repo, issue_number, page, per_page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.issues.listComments({
					owner,
					repo,
					issue_number,
					page,
					per_page,
				})

				// Format the response as clean markdown
				const comments = response.data

				if (comments.length === 0) {
					return {
						content: [
							{ type: "text", text: "No comments found for this issue." },
						],
					}
				}

				let markdown = `# Comments for Issue #${issue_number}\n\n`
				markdown += `Showing ${comments.length} comment(s) - Page ${page}\n`
				if (comments.length === per_page) {
					markdown += `*Note: More comments may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				comments.forEach((comment, index) => {
					markdown += `## Comment ${index + 1}\n\n`
					markdown += `- **Author**: ${comment.user?.login || "Unknown"}\n`
					markdown += `- **Created**: ${new Date(comment.created_at).toLocaleDateString()}\n`
					markdown += `- **Updated**: ${new Date(comment.updated_at).toLocaleDateString()}\n\n`
					markdown += `**Content**:\n${comment.body}\n\n`
					markdown += `---\n\n`
				})

				return {
					content: [{ type: "text", text: markdown }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)
}
