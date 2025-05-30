package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/github/github-mcp-server/pkg/github"
	"github.com/github/github-mcp-server/pkg/translations"
	gogithub "github.com/google/go-github/v69/github"
	"github.com/mark3labs/mcp-go/server"
	log "github.com/sirupsen/logrus"
)

// Define request context key type for safety
type contextKey string

const tokenContextKey contextKey = "auth_token"

func runServer() error {
	// Create app context
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	t, _ := translations.TranslationHelper()

	// Get auth token from environment variable
	envAuthToken := os.Getenv("GITHUB_AUTH_TOKEN")
	if envAuthToken != "" {
		log.Info("Using auth token from environment variable")
	}

	// Create a context function to extract the token from request headers
	contextFunc := func(ctx context.Context, r *http.Request) context.Context {
		// If env auth token is set, use it directly
		if envAuthToken != "" {
			return context.WithValue(ctx, tokenContextKey, envAuthToken)
		}

		// Otherwise fall back to header token
		token := r.Header.Get("x-auth-token")
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
	if err := runServer(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
