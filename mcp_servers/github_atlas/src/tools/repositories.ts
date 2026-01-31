import { z } from "zod"
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { getOctokit } from "../index.js"

export function registerRepositoryTools(server: McpServer) {
	// Tool: Get Repository Details
	server.tool(
		"get_repository",
		"Get detailed information about a GitHub repository including README and file structure",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
		},
		async ({ owner, repo }) => {
			try {
				const octokit = getOctokit()
				// Get basic repository info
				const repoResponse = await octokit.rest.repos.get({
					owner,
					repo,
				})
				const repoData = repoResponse.data

				// Start building markdown
				let markdown = `# ${repoData.full_name}\n\n`

				// Add description if available
				if (repoData.description) {
					markdown += `> ${repoData.description}\n\n`
				}

				// Add basic stats in a single line
				markdown += `**Language:** ${repoData.language || "Not specified"} | `
				markdown += `**Stars:** ${repoData.stargazers_count} | `
				markdown += `**Forks:** ${repoData.forks_count} | `
				markdown += `**License:** ${repoData.license?.spdx_id || "None"}\n\n`

				// Get README content
				try {
					const readmeResponse = await octokit.rest.repos.getReadme({
						owner,
						repo,
					})

					// Decode README content from base64
					const readmeContent = Buffer.from(
						readmeResponse.data.content,
						"base64",
					).toString("utf-8")

					markdown += `## README\n\n`
					markdown += readmeContent
					markdown += `\n\n`
				} catch (readmeError) {
					markdown += `## README\n\n`
					markdown += `*No README file found*\n\n`
				}

				// Get repository file structure (root directory)
				try {
					const contentsResponse = await octokit.rest.repos.getContent({
						owner,
						repo,
						path: "",
					})

					if (Array.isArray(contentsResponse.data)) {
						markdown += `## Repository Structure\n\n`

						// Sort contents: directories first, then files
						const contents = contentsResponse.data.sort((a, b) => {
							if (a.type === b.type) return a.name.localeCompare(b.name)
							return a.type === "dir" ? -1 : 1
						})

						// Group by type
						const dirs = contents.filter(item => item.type === "dir")
						const files = contents.filter(item => item.type === "file")

						if (dirs.length > 0) {
							markdown += `### Directories\n`
							dirs.forEach(dir => {
								markdown += `- **${dir.name}/**\n`
							})
							markdown += `\n`
						}

						if (files.length > 0) {
							markdown += `### Files\n`
							files.forEach(file => {
								const size = file.size
									? ` (${(file.size / 1024).toFixed(1)} KB)`
									: ""
								markdown += `- ${file.name}${size}\n`
							})
							markdown += `\n`
						}
					}
				} catch (contentsError) {
					markdown += `## Repository Structure\n\n`
					markdown += `*Unable to fetch repository contents*\n\n`
				}

				// Add essential links at the bottom
				markdown += `## Links\n\n`
				markdown += `- **GitHub:** ${repoData.html_url}\n`
				markdown += `- **Clone:** \`git clone ${repoData.clone_url}\`\n`
				if (repoData.homepage) {
					markdown += `- **Website:** ${repoData.homepage}\n`
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

	// Tool: Get Commit
	server.tool(
		"get_commit",
		"Get details for a commit from a GitHub repository",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			sha: z.string().describe("Commit SHA, branch name, or tag name"),
		},
		async ({ owner, repo, sha }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.getCommit({
					owner,
					repo,
					ref: sha,
				})

				const commit = response.data

				// Format as clean markdown
				let markdown = `# Commit ${commit.sha.substring(0, 7)}\n\n`
				markdown += `**Message:** ${commit.commit.message}\n\n`
				markdown += `**Author:** ${commit.commit.author?.name} <${commit.commit.author?.email}>\n`
				markdown += `**Date:** ${new Date(commit.commit.author?.date || "").toLocaleDateString()}\n`

				if (commit.commit.committer?.name !== commit.commit.author?.name) {
					markdown += `**Committer:** ${commit.commit.committer?.name} <${commit.commit.committer?.email}>\n`
				}

				markdown += `\n## Changes\n\n`
				markdown += `- **Files changed:** ${commit.files?.length || 0}\n`
				markdown += `- **Additions:** ${commit.stats?.additions || 0}\n`
				markdown += `- **Deletions:** ${commit.stats?.deletions || 0}\n`

				if (commit.files && commit.files.length > 0) {
					markdown += `\n## Files\n\n`
					commit.files.forEach(file => {
						const status =
							file.status === "added"
								? "[A]"
								: file.status === "removed"
									? "[D]"
									: file.status === "modified"
										? "[M]"
										: file.status === "renamed"
											? "[R]"
											: "[?]"
						markdown += `- ${status} ${file.filename} (+${file.additions} -${file.deletions})\n`
					})
				}

				markdown += `\n## Links\n\n`
				markdown += `- **Commit URL:** ${commit.html_url}\n`
				markdown += `- **Full SHA:** ${commit.sha}\n`

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

	// Tool: List Commits
	server.tool(
		"list_commits",
		"Get list of commits of a branch in a GitHub repository",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			sha: z.string().optional().describe("SHA or Branch name"),
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
		async ({ owner, repo, sha, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.listCommits({
					owner,
					repo,
					sha,
					per_page,
					page,
				})

				const commits = response.data

				if (commits.length === 0) {
					return {
						content: [{ type: "text", text: "No commits found." }],
					}
				}

				// Format as clean markdown
				let markdown = `# Commits for ${owner}/${repo}`
				if (sha) {
					markdown += ` (${sha})`
				}
				markdown += `\n\n`
				markdown += `Showing ${commits.length} commit(s) - Page ${page}\n`
				if (commits.length === per_page) {
					markdown += `*Note: More commits may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				commits.forEach(commit => {
					const shortSha = commit.sha.substring(0, 7)
					const message = commit.commit.message.split("\n")[0] // First line only
					const author =
						commit.commit.author?.name || commit.author?.login || "Unknown"
					const date = new Date(
						commit.commit.author?.date || "",
					).toLocaleDateString()

					markdown += `## ${shortSha}: ${message}\n\n`
					markdown += `- **Author:** ${author}\n`
					markdown += `- **Date:** ${date}\n`

					if (commit.commit.comment_count > 0) {
						markdown += `- **Comments:** ${commit.commit.comment_count}\n`
					}

					markdown += `- **URL:** ${commit.html_url}\n`
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

	// Tool: List Branches
	server.tool(
		"list_branches",
		"List branches in a GitHub repository",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
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
		async ({ owner, repo, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.listBranches({
					owner,
					repo,
					per_page,
					page,
				})

				const branches = response.data

				if (branches.length === 0) {
					return {
						content: [{ type: "text", text: "No branches found." }],
					}
				}

				// Get default branch
				const repoResponse = await octokit.rest.repos.get({ owner, repo })
				const defaultBranch = repoResponse.data.default_branch

				// Format as clean markdown
				let markdown = `# Branches for ${owner}/${repo}\n\n`
				markdown += `Showing ${branches.length} branch(es) - Page ${page}\n`
				if (branches.length === per_page) {
					markdown += `*Note: More branches may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				branches.forEach(branch => {
					const isDefault = branch.name === defaultBranch
					markdown += `## ${branch.name}${isDefault ? " (default)" : ""}\n\n`
					markdown += `- **SHA:** ${branch.commit.sha.substring(0, 7)}\n`

					if (branch.protected) {
						markdown += `- **Protected:** Yes\n`
					}

					markdown += `- **URL:** ${branch.commit.url.replace("api.github.com/repos", "github.com").replace("/commits/", "/tree/")}\n`
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

	// Tool: Create or Update File
	server.tool(
		"create_or_update_file",
		"Create or update a single file in a GitHub repository. If updating an existing file, you must provide the current SHA of the file (the full 40-character SHA, not a shortened version).",
		{
			owner: z.string().describe("Repository owner (username or organization)"),
			repo: z.string().describe("Repository name"),
			path: z.string().describe("Path where to create/update the file"),
			content: z.string().describe("Content of the file"),
			message: z.string().describe("Commit message"),
			branch: z.string().describe("Branch to create/update the file in"),
			sha: z
				.string()
				.optional()
				.describe(
					"Full SHA of the current file blob (required for updates, must be the complete 40-character SHA)",
				),
		},
		async ({ owner, repo, path, content, message, branch, sha }) => {
			try {
				// If SHA is provided, validate it's the full SHA
				if (sha && sha.length !== 40) {
					return {
						content: [
							{
								type: "text",
								text: `Error: SHA must be the full 40-character blob SHA. Provided SHA "${sha}" is only ${sha.length} characters. Use get_file_contents to retrieve the full SHA.`,
							},
						],
					}
				}

				const octokit = getOctokit()
				const response = await octokit.rest.repos.createOrUpdateFileContents({
					owner,
					repo,
					path,
					message,
					content: Buffer.from(content).toString("base64"),
					branch,
					sha,
				})

				// Format response as markdown
				let markdown = `# File ${response.data.commit.message}\n\n`
				markdown += `**Path:** ${response.data.content?.path || path}\n`
				markdown += `**SHA:** ${response.data.content?.sha || "N/A"}\n`
				markdown += `**Size:** ${response.data.content?.size || 0} bytes\n\n`
				markdown += `## Commit Details\n\n`
				markdown += `- **Commit SHA:** ${response.data.commit.sha}\n`
				markdown += `- **Author:** ${response.data.commit.author?.name} <${response.data.commit.author?.email}>\n`
				markdown += `- **Date:** ${response.data.commit.author?.date}\n`
				markdown += `- **URL:** ${response.data.commit.html_url}\n`

				return {
					content: [{ type: "text", text: markdown }],
				}
			} catch (e: any) {
				// Provide more helpful error messages
				if (e.message.includes("does not match")) {
					return {
						content: [
							{
								type: "text",
								text: `Error: SHA mismatch. The provided SHA does not match the current file's SHA. This usually means the file has been modified since you last retrieved it. Use get_file_contents to get the current SHA, then retry the update.\n\nOriginal error: ${e.message}`,
							},
						],
					}
				}
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Create Repository
	server.tool(
		"create_repository",
		"Create a new GitHub repository in your account",
		{
			name: z.string().describe("Repository name"),
			description: z.string().optional().describe("Repository description"),
			private: z
				.boolean()
				.optional()
				.describe("Whether repo should be private"),
			autoInit: z.boolean().optional().describe("Initialize with README"),
		},
		async ({ name, description, private: isPrivate, autoInit }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.createForAuthenticatedUser({
					name,
					description,
					private: isPrivate,
					auto_init: autoInit,
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

	// Tool: Get File Contents
	server.tool(
		"get_file_contents",
		"Get the contents of a file from a GitHub repository",
		{
			owner: z.string().describe("Repository owner (username or organization)"),
			repo: z.string().describe("Repository name"),
			path: z.string().describe("Path to file"),
			branch: z
				.string()
				.optional()
				.describe("Branch to get contents from (defaults to default branch)"),
			mode: z
				.enum(["overview", "full"])
				.optional()
				.default("overview")
				.describe(
					"Mode: 'overview' for truncated preview, 'full' for complete file",
				),
		},
		async ({ owner, repo, path, branch, mode }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.getContent({
					owner,
					repo,
					path,
					ref: branch,
				})

				// Handle only files
				if (Array.isArray(response.data)) {
					return {
						content: [
							{
								type: "text",
								text: "Error: Path points to a directory, not a file.",
							},
						],
					}
				}

				if (response.data.type !== "file") {
					return {
						content: [
							{
								type: "text",
								text: `Error: Path points to a ${response.data.type}, not a file.`,
							},
						],
					}
				}

				// Decode the file content
				const fullContent = Buffer.from(
					response.data.content,
					"base64",
				).toString("utf-8")

				// Get file extension for syntax highlighting
				const ext = path.split(".").pop() || ""
				const fileName = path.split("/").pop() || path

				// Format as markdown
				let markdown = `# File: ${fileName}\n\n`
				markdown += `**Path:** ${response.data.path}\n`
				markdown += `**Size:** ${(response.data.size / 1024).toFixed(2)} KB (${response.data.size} bytes)\n`
				markdown += `**SHA:** ${response.data.sha.substring(0, 7)} (full: ${response.data.sha})\n\n`

				if (mode === "overview") {
					// Truncated overview mode
					const lines = fullContent.split("\n")
					const totalLines = lines.length

					markdown += `**Lines:** ${totalLines}\n\n`
					markdown += `## Preview (first 50 lines)\n\n`

					const previewLines = lines.slice(0, 50)
					const preview = previewLines.join("\n")

					markdown += `\`\`\`${ext}\n${preview}\n`

					if (totalLines > 50) {
						markdown += `\n... (${totalLines - 50} more lines)\n`
					}

					markdown += `\`\`\`\n\n`

					if (totalLines > 50) {
						markdown += `*Showing first 50 lines of ${totalLines} total. Use mode='full' to see complete file.*\n`
					}
				} else {
					// Full content mode
					const lines = fullContent.split("\n").length
					markdown += `**Lines:** ${lines}\n\n`
					markdown += `## Full Content\n\n`
					markdown += `\`\`\`${ext}\n${fullContent}\n\`\`\``
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

	// Tool: Fork Repository
	server.tool(
		"fork_repository",
		"Fork a GitHub repository to your account or specified organization",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			organization: z.string().optional().describe("Organization to fork to"),
		},
		async ({ owner, repo, organization }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.createFork({
					owner,
					repo,
					organization,
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

	// Tool: Create Branch
	server.tool(
		"create_branch",
		"Create a new branch in a GitHub repository",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			branch: z.string().describe("Name for new branch"),
			from_branch: z
				.string()
				.optional()
				.describe("Source branch (defaults to repo default)"),
		},
		async ({ owner, repo, branch, from_branch }) => {
			try {
				const octokit = getOctokit()
				// Get the source branch ref
				let sourceBranch = from_branch
				if (!sourceBranch) {
					const repoResp = await octokit.rest.repos.get({ owner, repo })
					sourceBranch = repoResp.data.default_branch
				}
				const refResp = await octokit.rest.git.getRef({
					owner,
					repo,
					ref: `heads/${sourceBranch}`,
				})
				const sha = refResp.data.object.sha
				// Create new branch
				const response = await octokit.rest.git.createRef({
					owner,
					repo,
					ref: `refs/heads/${branch}`,
					sha,
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

	// Tool: List Tags
	server.tool(
		"list_tags",
		"List git tags in a GitHub repository",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
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
		async ({ owner, repo, per_page, page }) => {
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.listTags({
					owner,
					repo,
					per_page,
					page,
				})

				const tags = response.data

				if (tags.length === 0) {
					return {
						content: [{ type: "text", text: "No tags found." }],
					}
				}

				// Format as clean markdown
				let markdown = `# Tags for ${owner}/${repo}\n\n`
				markdown += `Showing ${tags.length} tag(s) - Page ${page}\n`
				if (tags.length === per_page) {
					markdown += `*Note: More tags may be available. Use 'page' parameter to see next page.*\n`
				}
				markdown += `\n`

				tags.forEach(tag => {
					markdown += `## ${tag.name}\n\n`
					markdown += `- **SHA:** ${tag.commit.sha.substring(0, 7)}\n`
					markdown += `- **URL:** ${tag.commit.url.replace("api.github.com/repos", "github.com").replace("/commits/", "/releases/tag/")}\n`

					if (tag.zipball_url) {
						markdown += `- **Download:** [ZIP](${tag.zipball_url}) | [TAR](${tag.tarball_url})\n`
					}

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

	// Tool: Get Tag
	server.tool(
		"get_tag",
		"Get details about a specific git tag in a GitHub repository",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			tag: z.string().describe("Tag name"),
		},
		async ({ owner, repo, tag }) => {
			try {
				const octokit = getOctokit()
				// Get the tag reference
				const refResp = await octokit.rest.git.getRef({
					owner,
					repo,
					ref: `tags/${tag}`,
				})
				const sha = refResp.data.object.sha
				// Get the tag object
				const tagResp = await octokit.rest.git.getTag({
					owner,
					repo,
					tag_sha: sha,
				})
				return {
					content: [{ type: "text", text: JSON.stringify(tagResp.data) }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)

	// Tool: Push Files
	server.tool(
		"push_files",
		"Push multiple files to a GitHub repository in a single commit",
		{
			owner: z.string().describe("Repository owner"),
			repo: z.string().describe("Repository name"),
			branch: z.string().describe("Branch to push to"),
			files: z
				.array(z.object({ path: z.string(), content: z.string() }))
				.describe(
					"Array of file objects to push, each object with path (string) and content (string)",
				),
			message: z.string().describe("Commit message"),
		},
		async ({ owner, repo, branch, files, message }) => {
			try {
				const octokit = getOctokit()
				// Get the reference for the branch
				const refResp = await octokit.rest.git.getRef({
					owner,
					repo,
					ref: `heads/${branch}`,
				})
				const baseSha = refResp.data.object.sha

				// Get the commit object that the branch points to
				const baseCommit = await octokit.rest.git.getCommit({
					owner,
					repo,
					commit_sha: baseSha,
				})

				// Create tree entries for all files
				const treeItems = files.map(file => ({
					path: file.path,
					mode: "100644" as const, // Regular file mode
					type: "blob" as const,
					content: file.content,
				}))

				// Create a new tree with the file entries
				const newTree = await octokit.rest.git.createTree({
					owner,
					repo,
					base_tree: baseCommit.data.tree.sha,
					tree: treeItems,
				})

				// Create a new commit
				const newCommit = await octokit.rest.git.createCommit({
					owner,
					repo,
					message,
					tree: newTree.data.sha,
					parents: [baseSha],
				})

				// Update the reference to point to the new commit
				const updatedRef = await octokit.rest.git.updateRef({
					owner,
					repo,
					ref: `heads/${branch}`,
					sha: newCommit.data.sha,
					force: false,
				})

				return {
					content: [{ type: "text", text: JSON.stringify(updatedRef.data) }],
				}
			} catch (e: any) {
				return {
					content: [{ type: "text", text: `Error: ${e.message}` }],
				}
			}
		},
	)
}
