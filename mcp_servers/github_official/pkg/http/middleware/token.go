package middleware

import (
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"

	ghcontext "github.com/github/github-mcp-server/pkg/context"
	"github.com/github/github-mcp-server/pkg/http/oauth"
	"github.com/github/github-mcp-server/pkg/utils"
)

func ExtractUserToken(oauthCfg *oauth.Config) func(next http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			tokenType, token, err := utils.ParseAuthorizationHeader(r)
			if err != nil {
				if errors.Is(err, utils.ErrMissingAuthorizationHeader) {
					// Fall back to x-auth-data header
					token, tokenType = extractTokenFromAuthData(r)
					if token == "" {
						sendAuthChallenge(w, r, oauthCfg)
						return
					}
				} else {
					// For other auth errors (bad format, unsupported), return 400
					http.Error(w, err.Error(), http.StatusBadRequest)
					return
				}
			}

			ctx := r.Context()
			ctx = ghcontext.WithTokenInfo(ctx, &ghcontext.TokenInfo{
				Token:     token,
				TokenType: tokenType,
			})
			r = r.WithContext(ctx)

			next.ServeHTTP(w, r)
		})
	}
}

// extractTokenFromAuthData extracts the access token from auth data.
// It first checks the AUTH_DATA environment variable (plain JSON).
// If not set, it falls back to the x-auth-data request header (base64-encoded JSON).
// The resulting JSON is parsed to extract the access_token field.
func extractTokenFromAuthData(r *http.Request) (string, utils.TokenType) {
	// First check AUTH_DATA env var (plain JSON)
	authData := os.Getenv("AUTH_DATA")

	if authData == "" {
		// Fall back to x-auth-data header (base64-encoded)
		headerVal := r.Header.Get("x-auth-data")
		if headerVal != "" {
			decoded, err := base64.StdEncoding.DecodeString(headerVal)
			if err != nil {
				return "", utils.TokenTypeUnknown
			}
			authData = string(decoded)
		}
	}

	if authData == "" {
		return "", utils.TokenTypeUnknown
	}

	var data map[string]interface{}
	if err := json.Unmarshal([]byte(authData), &data); err != nil {
		return "", utils.TokenTypeUnknown
	}

	token, ok := data["access_token"].(string)
	if !ok || token == "" {
		return "", utils.TokenTypeUnknown
	}

	return token, utils.DetectTokenType(token)
}

// sendAuthChallenge sends a 401 Unauthorized response with WWW-Authenticate header
// containing the OAuth protected resource metadata URL as per RFC 6750 and MCP spec.
func sendAuthChallenge(w http.ResponseWriter, r *http.Request, oauthCfg *oauth.Config) {
	resourcePath := oauth.ResolveResourcePath(r, oauthCfg)
	resourceMetadataURL := oauth.BuildResourceMetadataURL(r, oauthCfg, resourcePath)
	w.Header().Set("WWW-Authenticate", fmt.Sprintf(`Bearer resource_metadata=%q`, resourceMetadataURL))
	http.Error(w, "Unauthorized", http.StatusUnauthorized)
}
