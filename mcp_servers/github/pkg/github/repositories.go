package github

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/github/github-mcp-server/pkg/translations"
	"github.com/google/go-github/v69/github"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// CommitData represents the restructured commit response
type CommitData struct {
	SHA           string     `json:"sha"`
	Message       string     `json:"message"`
	Committer     AuthorInfo `json:"committer"`
	Author        AuthorInfo `json:"author"`
	CommittedDate time.Time  `json:"committed_date"`
	AuthoredDate  time.Time  `json:"authored_date"`
}

// AuthorInfo represents commit author/committer information
type AuthorInfo struct {
	Name  string `json:"name"`
	Email string `json:"email"`
}

// FileContentData represents the restructured file content response
type FileContentData struct {
	FileName    string `json:"file_name"`
	FilePath    string `json:"file_path"`
	Content     string `json:"content"`
	Size        int    `json:"size"`
	SHA         string `json:"sha"`
	DownloadURL string `json:"download_url,omitempty"`
}

// DirectoryContentData represents directory listing
type DirectoryContentData struct {
	Name        string `json:"name"`
	Path        string `json:"path"`
	Type        string `json:"type"`
	Size        int    `json:"size"`
	SHA         string `json:"sha"`
	DownloadURL string `json:"download_url,omitempty"`
}

// RepositoryData represents the restructured repository response
type RepositoryData struct {
	RepoID          int64     `json:"repo_id"`
	Name            string    `json:"name"`
	FullName        string    `json:"full_name"`
	Description     string    `json:"description"`
	Owner           UserInfo  `json:"owner"`
	IsPrivate       bool      `json:"is_private"`
	IsFork          bool      `json:"is_fork"`
	DefaultBranch   string    `json:"default_branch"`
	Language        string    `json:"language,omitempty"`
	StarCount       int       `json:"star_count"`
	ForkCount       int       `json:"fork_count"`
	WatcherCount    int       `json:"watcher_count"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
	PushedAt        time.Time `json:"pushed_at,omitempty"`
	CloneURL        string    `json:"clone_url"`
	HTMLURL         string    `json:"html_url"`
}

// FileOperationResultData represents file create/update result
type FileOperationResultData struct {
	FilePath      string        `json:"file_path"`
	CommitMessage string        `json:"commit_message"`
	CommitSHA     string        `json:"commit_sha"`
	Content       FileMetaData  `json:"content"`
}

// FileMetaData represents file metadata
type FileMetaData struct {
	Name        string `json:"name"`
	Path        string `json:"path"`
	SHA         string `json:"sha"`
	Size        int    `json:"size"`
	DownloadURL string `json:"download_url,omitempty"`
}

// BranchData represents branch information
type BranchData struct {
	Name      string `json:"name"`
	CommitSHA string `json:"commit_sha"`
	Protected bool   `json:"protected,omitempty"`
}

// StargazerData represents a user who starred a repository
type StargazerData struct {
	Username  string    `json:"username"`
	StarredAt time.Time `json:"starred_at,omitempty"`
}

// transformCommitToCommitData converts GitHub commit to CommitData
func transformCommitToCommitData(commit *github.RepositoryCommit) CommitData {
	data := CommitData{
		SHA:     commit.GetSHA(),
		Message: commit.GetCommit().GetMessage(),
	}

	if commit.Commit != nil {
		if commit.Commit.Committer != nil {
			data.Committer = AuthorInfo{
				Name:  commit.Commit.Committer.GetName(),
				Email: commit.Commit.Committer.GetEmail(),
			}
			data.CommittedDate = commit.Commit.Committer.GetDate().Time
		}

		if commit.Commit.Author != nil {
			data.Author = AuthorInfo{
				Name:  commit.Commit.Author.GetName(),
				Email: commit.Commit.Author.GetEmail(),
			}
			data.AuthoredDate = commit.Commit.Author.GetDate().Time
		}
	}

	return data
}

// transformRepoToRepositoryData converts GitHub repository to RepositoryData
func transformRepoToRepositoryData(repo *github.Repository) RepositoryData {
	data := RepositoryData{
		RepoID:        repo.GetID(),
		Name:          repo.GetName(),
		FullName:      repo.GetFullName(),
		Description:   repo.GetDescription(),
		Owner:         transformUserToUserInfo(repo.Owner),
		IsPrivate:     repo.GetPrivate(),
		IsFork:        repo.GetFork(),
		DefaultBranch: repo.GetDefaultBranch(),
		Language:      repo.GetLanguage(),
		StarCount:     repo.GetStargazersCount(),
		ForkCount:     repo.GetForksCount(),
		WatcherCount:  repo.GetWatchersCount(),
		CreatedAt:     repo.GetCreatedAt().Time,
		UpdatedAt:     repo.GetUpdatedAt().Time,
		CloneURL:      repo.GetCloneURL(),
		HTMLURL:       repo.GetHTMLURL(),
	}

	if !repo.GetPushedAt().Time.IsZero() {
		data.PushedAt = repo.GetPushedAt().Time
	}

	return data
}

// transformFileContentToFileContentData converts repository content to FileContentData
func transformFileContentToFileContentData(content *github.RepositoryContent) FileContentData {
	data := FileContentData{
		FileName:    content.GetName(),
		FilePath:    content.GetPath(),
		Size:        content.GetSize(),
		SHA:         content.GetSHA(),
		DownloadURL: content.GetDownloadURL(),
	}

	// Decode content if available
	if contentStr, err := content.GetContent(); err == nil {
		data.Content = contentStr
	}

	return data
}

// transformDirContentToDirectoryContentData converts repository content list to DirectoryContentData
func transformDirContentToDirectoryContentData(contents []*github.RepositoryContent) []DirectoryContentData {
	result := make([]DirectoryContentData, 0, len(contents))
	for _, item := range contents {
		result = append(result, DirectoryContentData{
			Name:        item.GetName(),
			Path:        item.GetPath(),
			Type:        item.GetType(),
			Size:        item.GetSize(),
			SHA:         item.GetSHA(),
			DownloadURL: item.GetDownloadURL(),
		})
	}
	return result
}

// ListCommits creates a tool to get commits of a branch in a repository.
func ListCommits(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_list_commits",
			mcp.WithDescription(t("TOOL_LIST_COMMITS_DESCRIPTION", "Get list of commits of a branch in a GitHub repository")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("Repository owner"),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			mcp.WithString("sha",
				mcp.Description("Branch name"),
			),
			WithPagination(),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			owner, err := requiredParam[string](request, "owner")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			repo, err := requiredParam[string](request, "repo")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			sha, err := OptionalParam[string](request, "sha")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			pagination, err := OptionalPaginationParams(request)
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			opts := &github.CommitsListOptions{
				SHA: sha,
				ListOptions: github.ListOptions{
					Page:    pagination.page,
					PerPage: pagination.perPage,
				},
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}
			commits, resp, err := client.Repositories.ListCommits(ctx, owner, repo, opts)
			if err != nil {
				return nil, fmt.Errorf("failed to list commits: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != 200 {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to list commits: %s", string(body))), nil
			}

			// Transform to custom structure
			commitList := make([]CommitData, 0, len(commits))
			for _, commit := range commits {
				commitList = append(commitList, transformCommitToCommitData(commit))
			}

			r, err := json.Marshal(commitList)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// CreateOrUpdateFile creates a tool to create or update a file in a GitHub repository.
func CreateOrUpdateFile(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_create_or_update_file",
			mcp.WithDescription(t("TOOL_CREATE_OR_UPDATE_FILE_DESCRIPTION", "Create or update a single file in a GitHub repository")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("Repository owner (username or organization)"),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			mcp.WithString("path",
				mcp.Required(),
				mcp.Description("Path where to create/update the file"),
			),
			mcp.WithString("content",
				mcp.Required(),
				mcp.Description("Content of the file"),
			),
			mcp.WithString("message",
				mcp.Required(),
				mcp.Description("Commit message"),
			),
			mcp.WithString("branch",
				mcp.Required(),
				mcp.Description("Branch to create/update the file in"),
			),
			mcp.WithString("sha",
				mcp.Description("SHA of file being replaced (for updates)"),
			),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			owner, err := requiredParam[string](request, "owner")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			repo, err := requiredParam[string](request, "repo")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			path, err := requiredParam[string](request, "path")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			content, err := requiredParam[string](request, "content")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			message, err := requiredParam[string](request, "message")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			branch, err := requiredParam[string](request, "branch")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			// Convert content to base64
			contentBytes := []byte(content)

			// Create the file options
			opts := &github.RepositoryContentFileOptions{
				Message: github.Ptr(message),
				Content: contentBytes,
				Branch:  github.Ptr(branch),
			}

			// If SHA is provided, set it (for updates)
			sha, err := OptionalParam[string](request, "sha")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			if sha != "" {
				opts.SHA = github.Ptr(sha)
			}

			// Create or update the file
			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}
			fileContent, resp, err := client.Repositories.CreateFile(ctx, owner, repo, path, opts)
			if err != nil {
				return nil, fmt.Errorf("failed to create/update file: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != 200 && resp.StatusCode != 201 {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to create/update file: %s", string(body))), nil
			}

			// Transform to custom structure
			result := FileOperationResultData{
				FilePath:      path,
				CommitMessage: message,
				CommitSHA:     fileContent.Commit.GetSHA(),
				Content: FileMetaData{
					Name:        fileContent.Content.GetName(),
					Path:        fileContent.Content.GetPath(),
					SHA:         fileContent.Content.GetSHA(),
					Size:        fileContent.Content.GetSize(),
					DownloadURL: fileContent.Content.GetDownloadURL(),
				},
			}

			r, err := json.Marshal(result)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// CreateRepository creates a tool to create a new GitHub repository.
func CreateRepository(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_create_repository",
			mcp.WithDescription(t("TOOL_CREATE_REPOSITORY_DESCRIPTION", "Create a new GitHub repository in your account")),
			mcp.WithString("name",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			mcp.WithString("description",
				mcp.Description("Repository description"),
			),
			mcp.WithBoolean("private",
				mcp.Description("Whether repo should be private"),
			),
			mcp.WithBoolean("autoInit",
				mcp.Description("Initialize with README"),
			),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			name, err := requiredParam[string](request, "name")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			description, err := OptionalParam[string](request, "description")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			private, err := OptionalParam[bool](request, "private")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			autoInit, err := OptionalParam[bool](request, "autoInit")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			repo := &github.Repository{
				Name:        github.Ptr(name),
				Description: github.Ptr(description),
				Private:     github.Ptr(private),
				AutoInit:    github.Ptr(autoInit),
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}
			createdRepo, resp, err := client.Repositories.Create(ctx, "", repo)
			if err != nil {
				return nil, fmt.Errorf("failed to create repository: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != http.StatusCreated {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to create repository: %s", string(body))), nil
			}

			// Transform to custom structure
			repoData := transformRepoToRepositoryData(createdRepo)

			r, err := json.Marshal(repoData)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// GetFileContents creates a tool to get the contents of a file or directory from a GitHub repository.
func GetFileContents(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_get_file_contents",
			mcp.WithDescription(t("TOOL_GET_FILE_CONTENTS_DESCRIPTION", "Get the contents of a file or directory from a GitHub repository")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("Repository owner (username or organization)"),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			mcp.WithString("path",
				mcp.Required(),
				mcp.Description("Path to file/directory"),
			),
			mcp.WithString("branch",
				mcp.Description("Branch to get contents from"),
			),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			owner, err := requiredParam[string](request, "owner")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			repo, err := requiredParam[string](request, "repo")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			path, err := requiredParam[string](request, "path")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			branch, err := OptionalParam[string](request, "branch")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}
			opts := &github.RepositoryContentGetOptions{Ref: branch}
			fileContent, dirContent, resp, err := client.Repositories.GetContents(ctx, owner, repo, path, opts)
			if err != nil {
				return nil, fmt.Errorf("failed to get file contents: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != 200 {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to get file contents: %s", string(body))), nil
			}

			// Transform to custom structure
			var result interface{}
			if fileContent != nil {
				result = transformFileContentToFileContentData(fileContent)
			} else {
				result = transformDirContentToDirectoryContentData(dirContent)
			}

			r, err := json.Marshal(result)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// ForkRepository creates a tool to fork a repository.
func ForkRepository(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_fork_repository",
			mcp.WithDescription(t("TOOL_FORK_REPOSITORY_DESCRIPTION", "Fork a GitHub repository to your account or specified organization")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("Repository owner"),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			mcp.WithString("organization",
				mcp.Description("Organization to fork to"),
			),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			owner, err := requiredParam[string](request, "owner")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			repo, err := requiredParam[string](request, "repo")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			org, err := OptionalParam[string](request, "organization")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			opts := &github.RepositoryCreateForkOptions{}
			if org != "" {
				opts.Organization = org
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}
			forkedRepo, resp, err := client.Repositories.CreateFork(ctx, owner, repo, opts)
			if err != nil {
				// Check if it's an acceptedError. An acceptedError indicates that the update is in progress,
				// and it's not a real error.
				if resp != nil && resp.StatusCode == http.StatusAccepted && isAcceptedError(err) {
					return mcp.NewToolResultText("Fork is in progress"), nil
				}
				return nil, fmt.Errorf("failed to fork repository: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != http.StatusAccepted {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to fork repository: %s", string(body))), nil
			}

			// Transform to custom structure
			repoData := transformRepoToRepositoryData(forkedRepo)

			r, err := json.Marshal(repoData)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// CreateBranch creates a tool to create a new branch.
func CreateBranch(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_create_branch",
			mcp.WithDescription(t("TOOL_CREATE_BRANCH_DESCRIPTION", "Create a new branch in a GitHub repository")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("Repository owner"),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			mcp.WithString("branch",
				mcp.Required(),
				mcp.Description("Name for new branch"),
			),
			mcp.WithString("from_branch",
				mcp.Description("Source branch (defaults to repo default)"),
			),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			owner, err := requiredParam[string](request, "owner")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			repo, err := requiredParam[string](request, "repo")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			branch, err := requiredParam[string](request, "branch")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			fromBranch, err := OptionalParam[string](request, "from_branch")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			// Get the source branch SHA
			var ref *github.Reference

			if fromBranch == "" {
				// Get default branch if from_branch not specified
				repository, resp, err := client.Repositories.Get(ctx, owner, repo)
				if err != nil {
					return nil, fmt.Errorf("failed to get repository: %w", err)
				}
				defer func() { _ = resp.Body.Close() }()

				fromBranch = *repository.DefaultBranch
			}

			// Get SHA of source branch
			ref, resp, err := client.Git.GetRef(ctx, owner, repo, "refs/heads/"+fromBranch)
			if err != nil {
				return nil, fmt.Errorf("failed to get reference: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			// Create new branch
			newRef := &github.Reference{
				Ref:    github.Ptr("refs/heads/" + branch),
				Object: &github.GitObject{SHA: ref.Object.SHA},
			}

			createdRef, resp, err := client.Git.CreateRef(ctx, owner, repo, newRef)
			if err != nil {
				return nil, fmt.Errorf("failed to create branch: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			// Transform to custom structure
			branchData := BranchData{
				Name:      branch,
				CommitSHA: createdRef.Object.GetSHA(),
			}

			r, err := json.Marshal(branchData)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// PushFiles creates a tool to push multiple files in a single commit to a GitHub repository.
func PushFiles(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_push_files",
			mcp.WithDescription(t("TOOL_PUSH_FILES_DESCRIPTION", "Push multiple files to a GitHub repository in a single commit")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("Repository owner"),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			mcp.WithString("branch",
				mcp.Required(),
				mcp.Description("Branch to push to"),
			),
			mcp.WithArray("files",
				mcp.Required(),
				mcp.Items(
					map[string]interface{}{
						"type":                 "object",
						"additionalProperties": false,
						"required":             []string{"path", "content"},
						"properties": map[string]interface{}{
							"path": map[string]interface{}{
								"type":        "string",
								"description": "path to the file",
							},
							"content": map[string]interface{}{
								"type":        "string",
								"description": "file content",
							},
						},
					}),
				mcp.Description("Array of file objects to push, each object with path (string) and content (string)"),
			),
			mcp.WithString("message",
				mcp.Required(),
				mcp.Description("Commit message"),
			),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			owner, err := requiredParam[string](request, "owner")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			repo, err := requiredParam[string](request, "repo")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			branch, err := requiredParam[string](request, "branch")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			message, err := requiredParam[string](request, "message")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			// Parse files parameter - this should be an array of objects with path and content
			filesObj, ok := request.GetArguments()["files"].([]interface{})
			if !ok {
				return mcp.NewToolResultError("files parameter must be an array of objects with path and content"), nil
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			// Get the reference for the branch
			ref, resp, err := client.Git.GetRef(ctx, owner, repo, "refs/heads/"+branch)
			if err != nil {
				return nil, fmt.Errorf("failed to get branch reference: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			// Get the commit object that the branch points to
			baseCommit, resp, err := client.Git.GetCommit(ctx, owner, repo, *ref.Object.SHA)
			if err != nil {
				return nil, fmt.Errorf("failed to get base commit: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			// Create tree entries for all files
			var entries []*github.TreeEntry

			for _, file := range filesObj {
				fileMap, ok := file.(map[string]interface{})
				if !ok {
					return mcp.NewToolResultError("each file must be an object with path and content"), nil
				}

				path, ok := fileMap["path"].(string)
				if !ok || path == "" {
					return mcp.NewToolResultError("each file must have a path"), nil
				}

				content, ok := fileMap["content"].(string)
				if !ok {
					return mcp.NewToolResultError("each file must have content"), nil
				}

				// Create a tree entry for the file
				entries = append(entries, &github.TreeEntry{
					Path:    github.Ptr(path),
					Mode:    github.Ptr("100644"), // Regular file mode
					Type:    github.Ptr("blob"),
					Content: github.Ptr(content),
				})
			}

			// Create a new tree with the file entries
			newTree, resp, err := client.Git.CreateTree(ctx, owner, repo, *baseCommit.Tree.SHA, entries)
			if err != nil {
				return nil, fmt.Errorf("failed to create tree: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			// Create a new commit
			commit := &github.Commit{
				Message: github.Ptr(message),
				Tree:    newTree,
				Parents: []*github.Commit{{SHA: baseCommit.SHA}},
			}
			newCommit, resp, err := client.Git.CreateCommit(ctx, owner, repo, commit, nil)
			if err != nil {
				return nil, fmt.Errorf("failed to create commit: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			// Update the reference to point to the new commit
			ref.Object.SHA = newCommit.SHA
			updatedRef, resp, err := client.Git.UpdateRef(ctx, owner, repo, ref, false)
			if err != nil {
				return nil, fmt.Errorf("failed to update reference: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			// Transform to custom structure
			result := BranchData{
				Name:      branch,
				CommitSHA: updatedRef.Object.GetSHA(),
			}

			r, err := json.Marshal(result)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// ListStargazers creates a tool to list users who have starred a GitHub repository. note: we use the graphql api and prompt to get accurate result!
func ListStargazers(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_list_recent_stargazers",
			mcp.WithDescription(t("TOOL_LIST_RECENT_STARGAZERS_DESCRIPTION", "Get a comprehensive list of users who have recently starred a specified GitHub repository, Ensure that the list includes every user without any omissions.")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("Repository owner (username or organization)"),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("Repository name"),
			),
			WithPagination(),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			owner, err := requiredParam[string](request, "owner")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			repo, err := requiredParam[string](request, "repo")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			pagination, err := OptionalPaginationParams(request)
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			// GraphQL query to fetch stargazers sorted by starred date
			query := `
				query($owner: String!, $name: String!, $first: Int!) { 
					repository(owner: $owner, name: $name) { 
						stargazers(first: $first, orderBy: {field: STARRED_AT, direction: DESC}) { 
							edges {  
								starredAt
								node { 
									login 
								} 
							} 
						} 
					} 
				}
			`

			variables := map[string]interface{}{
				"owner": owner,
				"name":  repo,
				"first": pagination.perPage,
			}

			req, err := client.NewRequest("POST", "graphql", map[string]interface{}{
				"query":     query,
				"variables": variables,
			})
			if err != nil {
				return nil, fmt.Errorf("failed to create GraphQL request: %w", err)
			}

			type GraphQLResponse struct {
				Data struct {
					Repository struct {
						Stargazers struct {
							Edges []struct {
								StarredAt string `json:"starredAt"`
								Node      struct {
									Login string `json:"login"`
								} `json:"node"`
							} `json:"edges"`
						} `json:"stargazers"`
					} `json:"repository"`
				} `json:"data"`
				Errors []struct {
					Message string `json:"message"`
				} `json:"errors,omitempty"`
			}

			var response GraphQLResponse
			resp, err := client.Do(ctx, req, &response)
			if err != nil {
				return nil, fmt.Errorf("failed to execute GraphQL request: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != 200 {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to list stargazers: %s", string(body))), nil
			}

			if len(response.Errors) > 0 {
				errMsgs := make([]string, len(response.Errors))
				for i, e := range response.Errors {
					errMsgs[i] = e.Message
				}
				return mcp.NewToolResultError(fmt.Sprintf("GraphQL errors: %s", strings.Join(errMsgs, "; "))), nil
			}

			stargazers := make([]StargazerData, 0, len(response.Data.Repository.Stargazers.Edges))
			for _, edge := range response.Data.Repository.Stargazers.Edges {
				starredAt, _ := time.Parse(time.RFC3339, edge.StarredAt)
				stargazers = append(stargazers, StargazerData{
					Username:  edge.Node.Login,
					StarredAt: starredAt,
				})
			}

			r, err := json.Marshal(stargazers)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}
