package github

import (
	"context"
	"encoding/json"
	"fmt"
	"io"

	"github.com/github/github-mcp-server/pkg/translations"
	"github.com/google/go-github/v69/github"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// RepositorySearchResultsData represents the restructured repository search results
type RepositorySearchResultsData struct {
	TotalCount   int              `json:"total_count"`
	Repositories []RepositoryData `json:"repositories"`
}

// CodeSearchResultsData represents the restructured code search results
type CodeSearchResultsData struct {
	TotalMatches int             `json:"total_matches"`
	CodeResults  []CodeResultData `json:"code_results"`
}

// CodeResultData represents a single code search result
type CodeResultData struct {
	FileName       string         `json:"file_name"`
	FilePath       string         `json:"file_path"`
	Repository     RepositoryInfo `json:"repository"`
	SHA            string         `json:"sha"`
	HTMLURL        string         `json:"html_url"`
}

// RepositoryInfo represents simplified repository information
type RepositoryInfo struct {
	Name     string `json:"name"`
	FullName string `json:"full_name"`
	Owner    string `json:"owner"`
}

// UserSearchResultsData represents the restructured user search results
type UserSearchResultsData struct {
	TotalMatches int            `json:"total_matches"`
	Users        []UserInfoData `json:"users"`
}

// UserInfoData represents user search result
type UserInfoData struct {
	Username  string `json:"username"`
	ProfileID int64  `json:"profile_id"`
	AccountType string `json:"account_type"`
	AvatarURL string `json:"avatar_url,omitempty"`
	HTMLURL   string `json:"html_url"`
}

// SearchRepositories creates a tool to search for GitHub repositories.
func SearchRepositories(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_search_repositories",
			mcp.WithDescription(t("TOOL_SEARCH_REPOSITORIES_DESCRIPTION", "Search for GitHub repositories")),
			mcp.WithString("query",
				mcp.Required(),
				mcp.Description("Search query"),
			),
			WithPagination(),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			query, err := requiredParam[string](request, "query")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			pagination, err := OptionalPaginationParams(request)
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			opts := &github.SearchOptions{
				ListOptions: github.ListOptions{
					Page:    pagination.page,
					PerPage: pagination.perPage,
				},
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}
			result, resp, err := client.Search.Repositories(ctx, query, opts)
			if err != nil {
				return nil, fmt.Errorf("failed to search repositories: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != 200 {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to search repositories: %s", string(body))), nil
			}

			// Transform to custom structure
			repositories := make([]RepositoryData, 0, len(result.Repositories))
			for _, repo := range result.Repositories {
				repositories = append(repositories, transformRepoToRepositoryData(repo))
			}

			searchResults := RepositorySearchResultsData{
				TotalCount:   result.GetTotal(),
				Repositories: repositories,
			}

			r, err := json.Marshal(searchResults)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// SearchCode creates a tool to search for code across GitHub repositories.
func SearchCode(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_search_code",
			mcp.WithDescription(t("TOOL_SEARCH_CODE_DESCRIPTION", "Search for code across GitHub repositories")),
			mcp.WithString("q",
				mcp.Required(),
				mcp.Description("Search query using GitHub code search syntax"),
			),
			mcp.WithString("sort",
				mcp.Description("Sort field ('indexed' only)"),
			),
			mcp.WithString("order",
				mcp.Description("Sort order ('asc' or 'desc')"),
				mcp.Enum("asc", "desc"),
			),
			WithPagination(),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			query, err := requiredParam[string](request, "q")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			sort, err := OptionalParam[string](request, "sort")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			order, err := OptionalParam[string](request, "order")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			pagination, err := OptionalPaginationParams(request)
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			opts := &github.SearchOptions{
				Sort:  sort,
				Order: order,
				ListOptions: github.ListOptions{
					PerPage: pagination.perPage,
					Page:    pagination.page,
				},
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			result, resp, err := client.Search.Code(ctx, query, opts)
			if err != nil {
				return nil, fmt.Errorf("failed to search code: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != 200 {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to search code: %s", string(body))), nil
			}

			// Transform to custom structure
			codeResults := make([]CodeResultData, 0, len(result.CodeResults))
			for _, code := range result.CodeResults {
				codeResults = append(codeResults, CodeResultData{
					FileName: code.GetName(),
					FilePath: code.GetPath(),
					Repository: RepositoryInfo{
						Name:     code.Repository.GetName(),
						FullName: code.Repository.GetFullName(),
						Owner:    code.Repository.Owner.GetLogin(),
					},
					SHA:     code.GetSHA(),
					HTMLURL: code.GetHTMLURL(),
				})
			}

			searchResults := CodeSearchResultsData{
				TotalMatches: result.GetTotal(),
				CodeResults:  codeResults,
			}

			r, err := json.Marshal(searchResults)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

// SearchUsers creates a tool to search for GitHub users.
func SearchUsers(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_search_users",
			mcp.WithDescription(t("TOOL_SEARCH_USERS_DESCRIPTION", "Search for GitHub users")),
			mcp.WithString("q",
				mcp.Required(),
				mcp.Description("Search query using GitHub users search syntax"),
			),
			mcp.WithString("sort",
				mcp.Description("Sort field (followers, repositories, joined)"),
				mcp.Enum("followers", "repositories", "joined"),
			),
			mcp.WithString("order",
				mcp.Description("Sort order ('asc' or 'desc')"),
				mcp.Enum("asc", "desc"),
			),
			WithPagination(),
		),
		func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			query, err := requiredParam[string](request, "q")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			sort, err := OptionalParam[string](request, "sort")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			order, err := OptionalParam[string](request, "order")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			pagination, err := OptionalPaginationParams(request)
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			opts := &github.SearchOptions{
				Sort:  sort,
				Order: order,
				ListOptions: github.ListOptions{
					PerPage: pagination.perPage,
					Page:    pagination.page,
				},
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			result, resp, err := client.Search.Users(ctx, query, opts)
			if err != nil {
				return nil, fmt.Errorf("failed to search users: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != 200 {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to search users: %s", string(body))), nil
			}

			// Transform to custom structure
			users := make([]UserInfoData, 0, len(result.Users))
			for _, user := range result.Users {
				users = append(users, UserInfoData{
					Username:    user.GetLogin(),
					ProfileID:   user.GetID(),
					AccountType: user.GetType(),
					AvatarURL:   user.GetAvatarURL(),
					HTMLURL:     user.GetHTMLURL(),
				})
			}

			searchResults := UserSearchResultsData{
				TotalMatches: result.GetTotal(),
				Users:        users,
			}

			r, err := json.Marshal(searchResults)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal response: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}
