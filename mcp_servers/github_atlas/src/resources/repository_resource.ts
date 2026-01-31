import {
	ResourceTemplate,
	type McpServer,
} from "@modelcontextprotocol/sdk/server/mcp.js"
import { getOctokit } from "../index.js"

export function registerRepositoryResource(server: McpServer) {
	server.resource(
		"github_repo_content",
		new ResourceTemplate("repo://{owner}/{repo}/contents/{...path}", {
			list: undefined,
		}),
		async (uri, params) => {
			const {
				owner,
				repo,
				path = "",
			} = params as { owner: string; repo: string; path?: string }
			try {
				const octokit = getOctokit()
				const response = await octokit.rest.repos.getContent({
					owner,
					repo,
					path,
				})
				let contents: any[] = []
				if (Array.isArray(response.data)) {
					// Directory listing
					contents = response.data.map(entry => ({
						uri: entry.html_url,
						mimeType: entry.type === "file" ? "text/plain" : "text/directory",
						text: entry.name,
					}))
				} else {
					// File content
					if (response.data.type === "file") {
						// If it's text, decode and return as text
						// If it's binary, return as base64 blob
						const isText =
							response.data.encoding === "base64" &&
							response.data.content &&
							response.data.content.match(/^[A-Za-z0-9+/=\s]+$/)
						if (isText) {
							const buff = Buffer.from(response.data.content, "base64")
							contents = [
								{
									uri: uri.href,
									mimeType: response.data.type,
									text: buff.toString("utf-8"),
								},
							]
						} else {
							contents = [
								{
									uri: uri.href,
									mimeType: response.data.type,
									blob: response.data.content,
								},
							]
						}
					}
				}
				return {
					contents: [
						{
							uri: uri.href,
							text: JSON.stringify(contents),
						},
					],
				}
			} catch (e: any) {
				return {
					contents: [
						{
							uri: uri.href,
							text: `Error: ${e.message}`,
						},
					],
				}
			}
		},
	)
}
