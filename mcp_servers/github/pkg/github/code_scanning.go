package github

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/github/github-mcp-server/pkg/translations"
	"github.com/google/go-github/v69/github"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// SecurityAlertData represents the restructured code scanning alert response
type SecurityAlertData struct {
	AlertID      int64       `json:"alert_id"`
	AlertNumber  int         `json:"alert_number"`
	State        string      `json:"state"`
	Severity     string      `json:"severity"`
	Description  string      `json:"description"`
	RuleName     string      `json:"rule_name"`
	RuleID       string      `json:"rule_id"`
	Tool         ToolInfo    `json:"tool"`
	Location     LocationInfo `json:"location,omitempty"`
	CreatedAt    time.Time   `json:"created_at"`
	UpdatedAt    time.Time   `json:"updated_at"`
	DismissedAt  *time.Time  `json:"dismissed_at,omitempty"`
	FixedAt      *time.Time  `json:"fixed_at,omitempty"`
}

// ToolInfo represents security tool information
type ToolInfo struct {
	Name    string `json:"name"`
	Version string `json:"version,omitempty"`
}

// LocationInfo represents alert location information
type LocationInfo struct {
	FilePath   string `json:"file_path"`
	StartLine  int    `json:"start_line,omitempty"`
	EndLine    int    `json:"end_line,omitempty"`
}

// transformAlertToSecurityAlertData converts GitHub alert to SecurityAlertData
func transformAlertToSecurityAlertData(alert *github.Alert) SecurityAlertData {
	data := SecurityAlertData{
		AlertID:     int64(alert.GetNumber()),
		AlertNumber: alert.GetNumber(),
		State:       alert.GetState(),
		CreatedAt:   alert.GetCreatedAt().Time,
		UpdatedAt:   alert.GetUpdatedAt().Time,
	}

	if alert.Rule != nil {
		data.Severity = alert.Rule.GetSeverity()
		data.Description = alert.Rule.GetDescription()
		data.RuleName = alert.Rule.GetName()
		data.RuleID = alert.Rule.GetID()
	}

	if alert.Tool != nil {
		data.Tool = ToolInfo{
			Name:    alert.Tool.GetName(),
			Version: alert.Tool.GetVersion(),
		}
	}

	if alert.MostRecentInstance != nil && alert.MostRecentInstance.Location != nil {
		data.Location = LocationInfo{
			FilePath:  alert.MostRecentInstance.Location.GetPath(),
			StartLine: alert.MostRecentInstance.Location.GetStartLine(),
			EndLine:   alert.MostRecentInstance.Location.GetEndLine(),
		}
	}

	if alert.DismissedAt != nil {
		dismissedAt := alert.GetDismissedAt().Time
		data.DismissedAt = &dismissedAt
	}

	if alert.FixedAt != nil {
		fixedAt := alert.GetFixedAt().Time
		data.FixedAt = &fixedAt
	}

	return data
}

func GetCodeScanningAlert(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_get_code_scanning_alert",
			mcp.WithDescription(t("TOOL_GET_CODE_SCANNING_ALERT_DESCRIPTION", "Get details of a specific code scanning alert in a GitHub repository.")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("The owner of the repository."),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("The name of the repository."),
			),
			mcp.WithNumber("alertNumber",
				mcp.Required(),
				mcp.Description("The number of the alert."),
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
			alertNumber, err := RequiredInt(request, "alertNumber")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}

			alert, resp, err := client.CodeScanning.GetAlert(ctx, owner, repo, int64(alertNumber))
			if err != nil {
				return nil, fmt.Errorf("failed to get alert: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != http.StatusOK {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to get alert: %s", string(body))), nil
			}

			// Transform to custom structure
			alertData := transformAlertToSecurityAlertData(alert)

			r, err := json.Marshal(alertData)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal alert: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}

func ListCodeScanningAlerts(getClient GetClientFn, t translations.TranslationHelperFunc) (tool mcp.Tool, handler server.ToolHandlerFunc) {
	return mcp.NewTool("github_list_code_scanning_alerts",
			mcp.WithDescription(t("TOOL_LIST_CODE_SCANNING_ALERTS_DESCRIPTION", "List code scanning alerts in a GitHub repository.")),
			mcp.WithString("owner",
				mcp.Required(),
				mcp.Description("The owner of the repository."),
			),
			mcp.WithString("repo",
				mcp.Required(),
				mcp.Description("The name of the repository."),
			),
			mcp.WithString("ref",
				mcp.Description("The Git reference for the results you want to list."),
			),
			mcp.WithString("state",
				mcp.Description("State of the code scanning alerts to list. Set to closed to list only closed code scanning alerts. Default: open"),
				mcp.DefaultString("open"),
			),
			mcp.WithString("severity",
				mcp.Description("Only code scanning alerts with this severity will be returned. Possible values are: critical, high, medium, low, warning, note, error."),
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
			ref, err := OptionalParam[string](request, "ref")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			state, err := OptionalParam[string](request, "state")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}
			severity, err := OptionalParam[string](request, "severity")
			if err != nil {
				return mcp.NewToolResultError(err.Error()), nil
			}

			client, err := getClient(ctx)
			if err != nil {
				return nil, fmt.Errorf("failed to get GitHub client: %w", err)
			}
			alerts, resp, err := client.CodeScanning.ListAlertsForRepo(ctx, owner, repo, &github.AlertListOptions{Ref: ref, State: state, Severity: severity})
			if err != nil {
				return nil, fmt.Errorf("failed to list alerts: %w", err)
			}
			defer func() { _ = resp.Body.Close() }()

			if resp.StatusCode != http.StatusOK {
				body, err := io.ReadAll(resp.Body)
				if err != nil {
					return nil, fmt.Errorf("failed to read response body: %w", err)
				}
				return mcp.NewToolResultError(fmt.Sprintf("failed to list alerts: %s", string(body))), nil
			}

			// Transform to custom structure
			alertList := make([]SecurityAlertData, 0, len(alerts))
			for _, alert := range alerts {
				alertList = append(alertList, transformAlertToSecurityAlertData(alert))
			}

			r, err := json.Marshal(alertList)
			if err != nil {
				return nil, fmt.Errorf("failed to marshal alerts: %w", err)
			}

			return mcp.NewToolResultText(string(r)), nil
		}
}
