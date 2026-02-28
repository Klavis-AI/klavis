package handler

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/korotovsky/slack-mcp-server/pkg/provider"
)

// ExtractAuthData parses the x-auth-data from the context if running via streamable-http and the client is uninitialized.
func ExtractAuthData(ctx context.Context, apiProvider *provider.ApiProvider) error {
	if apiProvider.ServerTransport() == "streamable-http" && apiProvider.Slack() == nil {
		req, ok := ctx.Value("request").(map[string]interface{})
		if !ok {
			return nil // soft fail if context isn't passed yet
		}

		headers, ok := req["headers"].(map[string][]string)
		if !ok {
			return errors.New("headers not found or malformed in request context")
		}

		var authData string
		if vals, ok := headers["x-auth-data"]; ok && len(vals) > 0 {
			authData = vals[0]
		} else if vals, ok := headers["X-Auth-Data"]; ok && len(vals) > 0 {
			authData = vals[0]
		}

		if authData == "" {
			return errors.New("x-auth-data header is missing from request")
		}

		decoded, err := base64.StdEncoding.DecodeString(authData)
		if err != nil {
			decoded = []byte(authData)
		}

		var tokens map[string]string
		if err := json.Unmarshal(decoded, &tokens); err != nil {
			return fmt.Errorf("failed to parse x-auth-data json: %w", err)
		}

		xoxp, pOk := tokens["xoxp_token"]
		xoxc, cOk := tokens["xoxc_token"]
		xoxd, dOk := tokens["xoxd_token"]

		if pOk && xoxp != "" {
			return apiProvider.RebuildClient(xoxp, "")
		} else if cOk && dOk && xoxc != "" && xoxd != "" {
			return apiProvider.RebuildClient(xoxc, xoxd)
		} else {
			return errors.New("valid Slack tokens not found in x-auth-data")
		}
	}
	return nil
}
