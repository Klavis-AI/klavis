import { z } from "zod"
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { getOctokit } from "../index.js"

export function registerPullRequestTools(server: McpServer) {
	// Tool: Get Pull Request
	server.tool(
		"get_pull_request",
		"Get details of a specific pull request in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
		},
		async ({ owner, repo, pullNumber }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.get({
					owner,
					repo,
					pull_number: pullNumber,
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

	// Tool: Update Pull Request
	server.tool(
		"update_pull_request",
		"Update an existing pull request in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number to update"),
			title: z.string().optional().describe("New title"),
			body: z.string().optional().describe("New description"),
			state: z.enum(["open", "closed"]).optional().describe("New state"),
			base: z.string().optional().describe("New base branch name"),
			maintainer_can_modify: z
				.boolean()
				.optional()
				.describe("Allow maintainer edits"),
		},
		async ({
			owner,
			repo,
			pullNumber,
			title,
			body,
			state,
			base,
			maintainer_can_modify,
		}) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.update({
					owner,
					repo,
					pull_number: pullNumber,
					title,
					body,
					state,
					base,
					maintainer_can_modify,
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

	// Tool: List Pull Requests
	server.tool(
		"list_pull_requests",
		"List pull requests in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			state: z
				.enum(["open", "closed", "all"])
				.optional()
				.describe("Filter by state"),
			head: z
				.string()
				.optional()
				.describe("Filter by head user/org and branch"),
			base: z.string().optional().describe("Filter by base branch"),
			sort: z
				.enum(["created", "updated", "popularity", "long-running"])
				.optional()
				.describe("Sort by"),
			direction: z.enum(["asc", "desc"]).optional().describe("Sort direction"),
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
			head,
			base,
			sort,
			direction,
			per_page,
			page,
		}) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.list({
					owner,
					repo,
					state,
					head,
					base,
					sort,
					direction,
					per_page,
					page,
				})

				// Format the response as clean markdown
				const prs = response.data
				if (prs.length === 0) {
					return {
						content: [{ type: "text", text: "No pull requests found." }],
					}
				}

				let markdown = `# Pull Requests for ${owner}/${repo}\n\n`
				markdown += `Showing ${prs.length} pull request(s) - Page ${page}\n`
				if (prs.length === per_page) {
					markdown += `*Note: More results may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				prs.forEach(pr => {
					markdown += `## #${pr.number}: ${pr.title}\n\n`
					markdown += `- **State**: ${pr.state}\n`
					markdown += `- **Author**: ${pr.user?.login || "Unknown"}\n`
					markdown += `- **Created**: ${new Date(pr.created_at).toLocaleDateString()}\n`
					markdown += `- **Updated**: ${new Date(pr.updated_at).toLocaleDateString()}\n`
					markdown += `- **Branch**: ${pr.head.ref} → ${pr.base.ref}\n`

					if (pr.draft) {
						markdown += `- **Status**: Draft\n`
					}

					if (pr.labels && pr.labels.length > 0) {
						markdown += `- **Labels**: ${pr.labels.map(l => l.name).join(", ")}\n`
					}

					if (pr.assignees && pr.assignees.length > 0) {
						markdown += `- **Assignees**: ${pr.assignees.map(a => a.login).join(", ")}\n`
					}

					markdown += `- **URL**: ${pr.html_url}\n`
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

	// Tool: Merge Pull Request
	server.tool(
		"merge_pull_request",
		"Merge a pull request in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
			commit_title: z.string().optional().describe("Title for merge commit"),
			commit_message: z
				.string()
				.optional()
				.describe("Extra detail for merge commit"),
			merge_method: z
				.enum(["merge", "squash", "rebase"])
				.optional()
				.describe("Merge method"),
		},
		async ({
			owner,
			repo,
			pullNumber,
			commit_title,
			commit_message,
			merge_method,
		}) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.merge({
					owner,
					repo,
					pull_number: pullNumber,
					commit_title,
					commit_message,
					merge_method,
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

	// Tool: Get Pull Request Files
	server.tool(
		"get_pull_request_files",
		"Get the files changed in a specific pull request.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
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
		async ({ owner, repo, pullNumber, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.listFiles({
					owner,
					repo,
					pull_number: pullNumber,
					per_page,
					page,
				})

				const files = response.data

				if (files.length === 0) {
					return {
						content: [
							{ type: "text", text: "No files changed in this pull request." },
						],
					}
				}

				// Calculate totals
				const totals = files.reduce(
					(acc, file) => ({
						additions: acc.additions + file.additions,
						deletions: acc.deletions + file.deletions,
						changes: acc.changes + file.changes,
					}),
					{ additions: 0, deletions: 0, changes: 0 },
				)

				// Format as clean markdown
				let markdown = `# Files Changed in Pull Request #${pullNumber}\n\n`
				markdown += `**Total:** ${files.length} file(s) | `
				markdown += `**+${totals.additions}** additions | `
				markdown += `**-${totals.deletions}** deletions\n\n`

				// Group files by status
				const grouped = {
					added: files.filter(f => f.status === "added"),
					modified: files.filter(f => f.status === "modified"),
					removed: files.filter(f => f.status === "removed"),
					renamed: files.filter(f => f.status === "renamed"),
					other: files.filter(
						f =>
							!["added", "modified", "removed", "renamed"].includes(f.status),
					),
				}

				// Show files by status
				if (grouped.added.length > 0) {
					markdown += `## Added Files\n\n`
					grouped.added.forEach(file => {
						markdown += `- **${file.filename}** (+${file.additions} lines)\n`
					})
					markdown += `\n`
				}

				if (grouped.modified.length > 0) {
					markdown += `## Modified Files\n\n`
					grouped.modified.forEach(file => {
						markdown += `- **${file.filename}** (+${file.additions} -${file.deletions})\n`
						if (file.patch) {
							markdown += `  - [View Diff](${file.blob_url})\n`
						}
					})
					markdown += `\n`
				}

				if (grouped.removed.length > 0) {
					markdown += `## Removed Files\n\n`
					grouped.removed.forEach(file => {
						markdown += `- **${file.filename}** (-${file.deletions} lines)\n`
					})
					markdown += `\n`
				}

				if (grouped.renamed.length > 0) {
					markdown += `## Renamed Files\n\n`
					grouped.renamed.forEach(file => {
						markdown += `- **${file.previous_filename}** → **${file.filename}**`
						if (file.changes > 0) {
							markdown += ` (+${file.additions} -${file.deletions})`
						}
						markdown += `\n`
					})
					markdown += `\n`
				}

				if (grouped.other.length > 0) {
					markdown += `## Other Changes\n\n`
					grouped.other.forEach(file => {
						markdown += `- **${file.filename}** (${file.status}) (+${file.additions} -${file.deletions})\n`
					})
					markdown += `\n`
				}

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

	// Tool: Get Pull Request Status (combined status for head SHA)
	server.tool(
		"get_pull_request_status",
		"Get the status of a specific pull request.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
		},
		async ({ owner, repo, pullNumber }) => {
			try {
				const octokit = getOctokit()
				// Get the PR to find the head SHA
				const prResp = await octokit.rest.pulls.get({
					owner,
					repo,
					pull_number: pullNumber,
				})
				const sha = prResp.data.head.sha
				const statusResp = await octokit.rest.repos.getCombinedStatusForRef({
					owner,
					repo,
					ref: sha,
				})

				const status = statusResp.data

				// Format as clean markdown
				let markdown = `# Pull Request #${pullNumber} Status\n\n`
				markdown += `**Overall State:** ${status.state}\n`
				markdown += `**SHA:** ${status.sha.substring(0, 7)}\n`
				markdown += `**Total Checks:** ${status.total_count}\n\n`

				if (status.statuses && status.statuses.length > 0) {
					markdown += `## Status Checks\n\n`

					// Group statuses by state
					const grouped = {
						success: status.statuses.filter(s => s.state === "success"),
						failure: status.statuses.filter(s => s.state === "failure"),
						error: status.statuses.filter(s => s.state === "error"),
						pending: status.statuses.filter(s => s.state === "pending"),
					}

					// Show failures and errors first
					if (grouped.failure.length > 0) {
						markdown += `### Failed\n\n`
						grouped.failure.forEach(check => {
							markdown += `- **${check.context}**: ${check.description || "No description"}\n`
							if (check.target_url) {
								markdown += `  - [View Details](${check.target_url})\n`
							}
						})
						markdown += `\n`
					}

					if (grouped.error.length > 0) {
						markdown += `### Errors\n\n`
						grouped.error.forEach(check => {
							markdown += `- **${check.context}**: ${check.description || "No description"}\n`
							if (check.target_url) {
								markdown += `  - [View Details](${check.target_url})\n`
							}
						})
						markdown += `\n`
					}

					if (grouped.pending.length > 0) {
						markdown += `### Pending\n\n`
						grouped.pending.forEach(check => {
							markdown += `- **${check.context}**: ${check.description || "No description"}\n`
							if (check.target_url) {
								markdown += `  - [View Details](${check.target_url})\n`
							}
						})
						markdown += `\n`
					}

					if (grouped.success.length > 0) {
						markdown += `### Passed\n\n`
						grouped.success.forEach(check => {
							markdown += `- **${check.context}**: ${check.description || "No description"}\n`
						})
						markdown += `\n`
					}
				} else {
					markdown += `*No status checks found*\n`
				}

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

	// Tool: Update Pull Request Branch (stub, not implemented)
	server.tool(
		"update_pull_request_branch",
		"Update the branch of a pull request with the latest changes from the base branch (not implemented)",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
			expectedHeadSha: z
				.string()
				.optional()
				.describe("The expected SHA of the pull request's HEAD ref"),
		},
		async () => {
			return {
				content: [{ type: "text", text: "Not implemented yet" }],
			}
		},
	)

	// Tool: Get Pull Request Comments
	server.tool(
		"get_pull_request_comments",
		"Get comments for a specific pull request",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
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
		async ({ owner, repo, pullNumber, per_page, page }) => {
			try {
				const octokit = getOctokit()
				// Get both issue comments and review comments
				const [issueComments, reviewComments] = await Promise.all([
					octokit.rest.issues.listComments({
						owner,
						repo,
						issue_number: pullNumber,
						per_page,
						page,
					}),
					octokit.rest.pulls.listReviewComments({
						owner,
						repo,
						pull_number: pullNumber,
						per_page,
						page,
					}),
				])

				// Combine and sort all comments by creation date
				const allComments = [
					...issueComments.data.map(c => ({ ...c, type: "issue" })),
					...reviewComments.data.map(c => ({ ...c, type: "review" })),
				].sort(
					(a, b) =>
						new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
				)

				if (allComments.length === 0) {
					return {
						content: [
							{
								type: "text",
								text: "No comments found for this pull request.",
							},
						],
					}
				}

				// Format as clean markdown
				let markdown = `# Comments for Pull Request #${pullNumber}\n\n`
				markdown += `Showing ${allComments.length} comment(s) - Page ${page}\n`
				if (
					issueComments.data.length === per_page ||
					reviewComments.data.length === per_page
				) {
					markdown += `*Note: More comments may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				allComments.forEach((comment, index) => {
					const isReviewComment = comment.type === "review"

					markdown += `## Comment ${index + 1}${isReviewComment ? " (Code Review)" : ""}\n\n`
					markdown += `- **Author:** ${comment.user?.login || "Unknown"}\n`
					markdown += `- **Created:** ${new Date(comment.created_at).toLocaleDateString()}\n`

					if (comment.updated_at !== comment.created_at) {
						markdown += `- **Updated:** ${new Date(comment.updated_at).toLocaleDateString()}\n`
					}

					// For review comments, show the file and line context
					if (isReviewComment && "path" in comment) {
						markdown += `- **File:** ${comment.path}\n`
						if (comment.line) {
							markdown += `- **Line:** ${comment.line}\n`
						}
						if (comment.commit_id) {
							markdown += `- **Commit:** ${comment.commit_id.substring(0, 7)}\n`
						}
					}

					markdown += `\n**Content:**\n${comment.body}\n\n`
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

	// Tool: Create Pull Request
	server.tool(
		"create_pull_request",
		"Create a new pull request in a GitHub repository.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			title: z.string().describe("PR title"),
			body: z.string().optional().describe("PR description"),
			head: z.string().describe("Branch containing changes"),
			base: z.string().describe("Branch to merge into"),
			draft: z.boolean().optional().describe("Create as draft PR"),
			maintainer_can_modify: z
				.boolean()
				.optional()
				.describe("Allow maintainer edits"),
		},
		async ({
			owner,
			repo,
			title,
			body,
			head,
			base,
			draft,
			maintainer_can_modify,
		}) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.create({
					owner,
					repo,
					title,
					body,
					head,
					base,
					draft,
					maintainer_can_modify,
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

	// Tool: Get Pull Request Review Comments
	server.tool(
		"get_pull_request_review_comments",
		"Get review comments (line-by-line code comments) for a specific pull request.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
			sort: z
				.enum(["created", "updated"])
				.optional()
				.describe("Sort comments by created or updated time"),
			direction: z
				.enum(["asc", "desc"])
				.optional()
				.describe("Sort direction"),
			since: z
				.string()
				.optional()
				.describe("Only show comments updated after this time (ISO 8601 format)"),
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
		async ({ owner, repo, pullNumber, sort, direction, since, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.listReviewComments({
					owner,
					repo,
					pull_number: pullNumber,
					sort,
					direction,
					since,
					per_page,
					page,
				})

				const comments = response.data

				if (comments.length === 0) {
					return {
						content: [
							{
								type: "text",
								text: "No review comments found for this pull request.",
							},
						],
					}
				}

				// Format as clean markdown
				let markdown = `# Review Comments for Pull Request #${pullNumber}\n\n`
				markdown += `Showing ${comments.length} review comment(s) - Page ${page}\n`
				if (comments.length === per_page) {
					markdown += `*Note: More results may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				comments.forEach((comment, index) => {
					markdown += `## Comment ${index + 1}\n\n`
					markdown += `- **Author:** ${comment.user?.login || "Unknown"}\n`
					markdown += `- **File:** ${comment.path}\n`
					
					if (comment.line) {
						markdown += `- **Line:** ${comment.line}\n`
					}
					
					if (comment.start_line && comment.start_line !== comment.line) {
						markdown += `- **Lines:** ${comment.start_line}-${comment.line}\n`
					}
					
					markdown += `- **Side:** ${comment.side || "RIGHT"}\n`
					markdown += `- **Created:** ${new Date(comment.created_at).toLocaleDateString()}\n`
					
					if (comment.updated_at !== comment.created_at) {
						markdown += `- **Updated:** ${new Date(comment.updated_at).toLocaleDateString()}\n`
					}
					
					if (comment.commit_id) {
						markdown += `- **Commit:** ${comment.commit_id.substring(0, 7)}\n`
					}

					if (comment.in_reply_to_id) {
						markdown += `- **Reply to:** Comment #${comment.in_reply_to_id}\n`
					}

					markdown += `\n**Comment:**\n${comment.body}\n`
					
					if (comment.html_url) {
						markdown += `\n**URL:** ${comment.html_url}\n`
					}

					markdown += `\n---\n\n`
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

	// Tool: Create Pull Request Review Comment
	server.tool(
		"create_pull_request_review_comment",
		"Create a review comment (line-by-line code comment) on a pull request.",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			pullNumber: z.number().describe("Pull request number"),
			body: z.string().describe("Comment body"),
			commit_id: z.string().describe("SHA of the commit to comment on"),
			path: z.string().describe("Relative path to the file being commented on"),
			line: z.number().optional().describe("Line number for single-line comment"),
			start_line: z.number().optional().describe("Start line for multi-line comment"),
			side: z
				.enum(["LEFT", "RIGHT"])
				.optional()
				.default("RIGHT")
				.describe("Side of diff (LEFT for deletion, RIGHT for addition)"),
			start_side: z
				.enum(["LEFT", "RIGHT"])
				.optional()
				.describe("Start side for multi-line comment"),
			in_reply_to: z
				.number()
				.optional()
				.describe("ID of review comment to reply to"),
		},
		async ({
			owner,
			repo,
			pullNumber,
			body,
			commit_id,
			path,
			line,
			start_line,
			side,
			start_side,
			in_reply_to,
		}) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.pulls.createReviewComment({
					owner,
					repo,
					pull_number: pullNumber,
					body,
					commit_id,
					path,
					line,
					start_line,
					side,
					start_side,
					in_reply_to,
				})

				// Format response as clean markdown
				const comment = response.data
				let markdown = `# Review Comment Created for Pull Request #${pullNumber}\n\n`
				markdown += `- **Comment ID:** ${comment.id}\n`
				markdown += `- **Author:** ${comment.user?.login || "Unknown"}\n`
				markdown += `- **File:** ${comment.path}\n`
				
				if (comment.line) {
					markdown += `- **Line:** ${comment.line}\n`
				}
				
				if (comment.start_line && comment.start_line !== comment.line) {
					markdown += `- **Lines:** ${comment.start_line}-${comment.line}\n`
				}
				
				markdown += `- **Side:** ${comment.side || "RIGHT"}\n`
				markdown += `- **Created:** ${new Date(comment.created_at).toLocaleDateString()}\n`
				
				if (comment.commit_id) {
					markdown += `- **Commit:** ${comment.commit_id.substring(0, 7)}\n`
				}

				if (comment.in_reply_to_id) {
					markdown += `- **Reply to:** Comment #${comment.in_reply_to_id}\n`
				}

				markdown += `\n**Comment:**\n${comment.body}\n`
				markdown += `\n**URL:** ${comment.html_url}\n`

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
