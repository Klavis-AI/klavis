package handler

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/korotovsky/slack-mcp-server/pkg/provider"
	"go.uber.org/zap"
)

func maskToken(v string) string {
	if len(v) <= 8 {
		return "***"
	}
	return v[:4] + "***" + v[len(v)-4:]
}

// ExtractAuthData parses the x-auth-data from the context if running via streamable-http and the client is uninitialized.
func ExtractAuthData(ctx context.Context, apiProvider *provider.ApiProvider, logger *zap.Logger) error {
	if apiProvider.ServerTransport() == "streamable-http" && apiProvider.Slack() == nil {
		logger.Debug("Dynamic auth: extracting x-auth-data from request context")

		req, ok := ctx.Value("request").(map[string]interface{})
		if !ok {
			logger.Debug("Dynamic auth: request context not available yet, skipping")
			return nil
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

		logger.Debug("Dynamic auth: x-auth-data header found, decoding")

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

		if pOk && xoxp != "" { // in production, we use xoxp token only (USER OAUTH)
			logger.Info("Dynamic auth: rebuilding client with xoxp token", zap.String("xoxp", maskToken(xoxp)))
			return apiProvider.RebuildClient(xoxp, "")
		} else if cOk && dOk && xoxc != "" && xoxd != "" {
			logger.Info("Dynamic auth: rebuilding client with xoxc/xoxd tokens", zap.String("xoxc", maskToken(xoxc)), zap.String("xoxd", maskToken(xoxd)))
			return apiProvider.RebuildClient(xoxc, xoxd)
		} else {
			return errors.New("valid Slack tokens not found in x-auth-data")
		}
	}
	return nil
}
