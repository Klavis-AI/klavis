package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/github/github-mcp-server/pkg/github"
	"github.com/github/github-mcp-server/pkg/translations"
	gogithub "github.com/google/go-github/v69/github"
	"github.com/joho/godotenv"
	"github.com/mark3labs/mcp-go/server"
	log "github.com/sirupsen/logrus"
)

// Define request context key type for safety
type contextKey string

const tokenContextKey contextKey = "auth_token"

func extractAccessToken(r *http.Request) string {
	// First try AUTH_DATA environment variable
	authData := os.Getenv("AUTH_DATA")

	if authData == "" {
		// Extract from x-auth-data header
		headerData := r.Header.Get("x-auth-data")
		if headerData != "" {
			// Decode base64
			decoded, err := base64.StdEncoding.DecodeString(headerData)
			if err != nil {
				log.WithError(err).Warn("Failed to decode base64 auth data")
				return ""
			}
			authData = string(decoded)
		}
	}

	if authData == "" {
		return ""
	}

	// Try to parse as JSON
	var authJSON map[string]interface{}
	if err := json.Unmarshal([]byte(authData), &authJSON); err != nil {
		log.WithError(err).Warn("Failed to parse auth data JSON")
		return ""
	}

	// Extract access_token field
	if accessToken, ok := authJSON["access_token"].(string); ok {
		return accessToken
	}

	return ""
}

func runServer() error {
	// Create app context
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	t, _ := translations.TranslationHelper()

	// Create a context function to extract the token from request headers
	contextFunc := func(ctx context.Context, r *http.Request) context.Context {
		// Extract from x-auth-data header
		token := extractAccessToken(r)
		if token != "" {
			return context.WithValue(ctx, tokenContextKey, token)
		}

		return ctx
	}

	// Create a function that returns a GitHub client for each request
	getClient := func(ctx context.Context) (*gogithub.Client, error) {
		// Extract token from context
		tokenValue := ctx.Value(tokenContextKey)
		token, ok := tokenValue.(string)
		if !ok || token == "" {
			log.Warn("No auth token found in context")
			return gogithub.NewClient(nil), nil
		}

		// Create authenticated client
		client := gogithub.NewClient(nil).WithAuthToken(token)
		// client.UserAgent = fmt.Sprintf("github-mcp-server/%s")
		return client, nil
	}

	// Get port from environment variable (Cloud Run sets PORT)
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000" // Fallback to 5000 for local development
	}

	// Get base URL from environment or construct a default
	baseURL := os.Getenv("BASE_URL")
	if baseURL == "" {
		baseURL = fmt.Sprintf("http://localhost:%s", port)
	}
	// Create a multiplexer to handle multiple handlers
	mux := http.NewServeMux()
	httpServer := &http.Server{
		Addr:    ":" + port,
		Handler: mux,
	}
	// Create servers with context function
	ghServer := github.NewServer(getClient, "", false, t)
	sseServer := server.NewSSEServer(ghServer,
		server.WithBaseURL(baseURL),
		server.WithSSEContextFunc(contextFunc),
		server.WithHTTPServer(httpServer),
	)
	streamableHttpServer := server.NewStreamableHTTPServer(ghServer,
		server.WithHTTPContextFunc(contextFunc),
		server.WithStreamableHTTPServer(httpServer),
		server.WithStateLess(true),
	)

	// Register handlers on different paths
	mux.Handle("/sse", sseServer)
	mux.Handle("/message", sseServer)
	mux.Handle("/mcp/", streamableHttpServer)

	// Start the server with a goroutine
	serverErr := make(chan error, 1)
	go func() {
		log.Printf("Server listening on :%s", port)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			serverErr <- err
		}
	}()

	// Wait for termination signal or server error
	select {
	case err := <-serverErr:
		return err
	case <-ctx.Done():
		log.Info("Shutdown signal received")
		// timeout context for shutdown
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		httpServer.Shutdown(shutdownCtx)

		log.Info("Server gracefully stopped")
	}

	return nil
}

func main() {
	_ = godotenv.Load(".env")
	if err := runServer(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
