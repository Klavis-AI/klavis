package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
	"sync"

	"github.com/korotovsky/slack-mcp-server/pkg/provider"
	"github.com/korotovsky/slack-mcp-server/pkg/server"
	"github.com/mattn/go-isatty"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

var defaultSseHost = "127.0.0.1"
var defaultSsePort = 13080

func main() {
	var transport string
	flag.StringVar(&transport, "t", "stdio", "Transport type (stdio, sse, or streamable-http)")
	flag.StringVar(&transport, "transport", "stdio", "Transport type (stdio, sse, or streamable-http)")
	flag.Parse()

	parseAuthData()

	logger, err := newLogger(transport)
	if err != nil {
		panic(err)
	}
	defer logger.Sync()

	err = validateToolConfig(os.Getenv("SLACK_MCP_ADD_MESSAGE_TOOL"))
	if err != nil {
		logger.Fatal("error in SLACK_MCP_ADD_MESSAGE_TOOL",
			zap.String("context", "console"),
			zap.Error(err),
		)
	}

	p := provider.New(transport, logger)
	s := server.NewMCPServer(p, logger)

	go func() {
		var once sync.Once

		newUsersWatcher(p, &once, logger)()
		newChannelsWatcher(p, &once, logger)()
	}()

	switch transport {
	case "stdio":
		if err := s.ServeStdio(); err != nil {
			logger.Fatal("Server error",
				zap.String("context", "console"),
				zap.Error(err),
			)
		}
	case "sse":
		host := os.Getenv("SLACK_MCP_HOST")
		if host == "" {
			host = defaultSseHost
		}
		port := os.Getenv("SLACK_MCP_PORT")
		if port == "" {
			port = strconv.Itoa(defaultSsePort)
		}

		sseServer := s.ServeSSE(":" + port)
		logger.Info(
			fmt.Sprintf("SSE server listening on %s", fmt.Sprintf("%s:%s/sse", host, port)),
			zap.String("context", "console"),
			zap.String("host", host),
			zap.String("port", port),
		)

		if ready, _ := p.IsReady(); !ready {
			logger.Info("Slack MCP Server is still warming up caches",
				zap.String("context", "console"),
			)
		}

		if err := sseServer.Start(host + ":" + port); err != nil {
			logger.Fatal("Server error",
				zap.String("context", "console"),
				zap.Error(err),
			)
		}
	case "streamable-http":
		host := os.Getenv("SLACK_MCP_HOST")
		if host == "" {
			host = "0.0.0.0"
		}
		port := os.Getenv("SLACK_MCP_PORT")
		if port == "" {
			port = strconv.Itoa(defaultSsePort)
		}

		httpServer := s.ServeStreamableHTTP()
		logger.Info(
			fmt.Sprintf("StreamableHTTP server listening on %s:%s/mcp", host, port),
			zap.String("context", "console"),
			zap.String("host", host),
			zap.String("port", port),
		)

		if ready, _ := p.IsReady(); !ready {
			logger.Info("Slack MCP Server is still warming up caches",
				zap.String("context", "console"),
			)
		}

		if err := httpServer.Start(host + ":" + port); err != nil {
			logger.Fatal("Server error",
				zap.String("context", "console"),
				zap.Error(err),
			)
		}
	default:
		logger.Fatal("Invalid transport type",
			zap.String("context", "console"),
			zap.String("transport", transport),
			zap.String("allowed", "stdio,sse,streamable-http"),
		)
	}
}

func newUsersWatcher(p *provider.ApiProvider, once *sync.Once, logger *zap.Logger) func() {
	return func() {
		logger.Info("Caching users collection...",
			zap.String("context", "console"),
		)

		if os.Getenv("SLACK_MCP_XOXP_TOKEN") == "demo" || (os.Getenv("SLACK_MCP_XOXC_TOKEN") == "demo" && os.Getenv("SLACK_MCP_XOXD_TOKEN") == "demo") {
			logger.Info("Demo credentials are set, skip",
				zap.String("context", "console"),
			)
			return
		}

		err := p.RefreshUsers(context.Background())
		if err != nil {
			logger.Fatal("Error booting provider",
				zap.String("context", "console"),
				zap.Error(err),
			)
		}

		ready, _ := p.IsReady()
		if ready {
			once.Do(func() {
				logger.Info("Slack MCP Server is fully ready",
					zap.String("context", "console"),
				)
			})
		}
	}
}

func newChannelsWatcher(p *provider.ApiProvider, once *sync.Once, logger *zap.Logger) func() {
	return func() {
		logger.Info("Caching channels collection...",
			zap.String("context", "console"),
		)

		if os.Getenv("SLACK_MCP_XOXP_TOKEN") == "demo" || (os.Getenv("SLACK_MCP_XOXC_TOKEN") == "demo" && os.Getenv("SLACK_MCP_XOXD_TOKEN") == "demo") {
			logger.Info("Demo credentials are set, skip.",
				zap.String("context", "console"),
			)
			return
		}

		err := p.RefreshChannels(context.Background())
		if err != nil {
			logger.Fatal("Error booting provider",
				zap.String("context", "console"),
				zap.Error(err),
			)
		}

		ready, _ := p.IsReady()
		if ready {
			once.Do(func() {
				logger.Info("Slack MCP Server is fully ready.",
					zap.String("context", "console"),
				)
			})
		}
	}
}

func validateToolConfig(config string) error {
	if config == "" || config == "true" || config == "1" {
		return nil
	}

	items := strings.Split(config, ",")
	hasNegated := false
	hasPositive := false

	for _, item := range items {
		item = strings.TrimSpace(item)
		if item == "" {
			continue
		}
		if strings.HasPrefix(item, "!") {
			hasNegated = true
		} else {
			hasPositive = true
		}
	}

	if hasNegated && hasPositive {
		return fmt.Errorf("cannot mix allowed and disallowed (! prefixed) channels")
	}

	return nil
}

func newLogger(transport string) (*zap.Logger, error) {
	atomicLevel := zap.NewAtomicLevelAt(zap.InfoLevel)
	if envLevel := os.Getenv("SLACK_MCP_LOG_LEVEL"); envLevel != "" {
		if err := atomicLevel.UnmarshalText([]byte(envLevel)); err != nil {
			fmt.Printf("Invalid log level '%s': %v, using 'info'\n", envLevel, err)
		}
	}

	useJSON := shouldUseJSONFormat()
	useColors := shouldUseColors() && !useJSON

	outputPath := "stdout"
	if transport == "stdio" {
		outputPath = "stderr"
	}

	var config zap.Config

	if useJSON {
		config = zap.Config{
			Level:            atomicLevel,
			Development:      false,
			Encoding:         "json",
			OutputPaths:      []string{outputPath},
			ErrorOutputPaths: []string{"stderr"},
			EncoderConfig: zapcore.EncoderConfig{
				TimeKey:       "timestamp",
				LevelKey:      "level",
				NameKey:       "logger",
				MessageKey:    "message",
				StacktraceKey: "stacktrace",
				EncodeLevel:   zapcore.LowercaseLevelEncoder,
				EncodeTime:    zapcore.RFC3339TimeEncoder,
				EncodeCaller:  zapcore.ShortCallerEncoder,
			},
		}
	} else {
		config = zap.Config{
			Level:            atomicLevel,
			Development:      true,
			Encoding:         "console",
			OutputPaths:      []string{outputPath},
			ErrorOutputPaths: []string{"stderr"},
			EncoderConfig: zapcore.EncoderConfig{
				TimeKey:          "timestamp",
				LevelKey:         "level",
				NameKey:          "logger",
				MessageKey:       "msg",
				StacktraceKey:    "stacktrace",
				EncodeLevel:      getConsoleLevelEncoder(useColors),
				EncodeTime:       zapcore.ISO8601TimeEncoder,
				EncodeCaller:     zapcore.ShortCallerEncoder,
				ConsoleSeparator: " | ",
			},
		}
	}

	logger, err := config.Build(zap.AddCaller())
	if err != nil {
		return nil, err
	}

	logger = logger.With(zap.String("app", "slack-mcp-server"))

	return logger, err
}

// shouldUseJSONFormat determines if JSON format should be used
func shouldUseJSONFormat() bool {
	if format := os.Getenv("SLACK_MCP_LOG_FORMAT"); format != "" {
		return strings.ToLower(format) == "json"
	}

	if env := os.Getenv("ENVIRONMENT"); env != "" {
		switch strings.ToLower(env) {
		case "production", "prod", "staging":
			return true
		case "development", "dev", "local":
			return false
		}
	}

	if os.Getenv("KUBERNETES_SERVICE_HOST") != "" ||
		os.Getenv("DOCKER_CONTAINER") != "" ||
		os.Getenv("container") != "" {
		return true
	}

	if !isatty.IsTerminal(os.Stdout.Fd()) {
		return true
	}

	return false
}

func shouldUseColors() bool {
	if colorEnv := os.Getenv("SLACK_MCP_LOG_COLOR"); colorEnv != "" {
		return colorEnv == "true" || colorEnv == "1"
	}

	if os.Getenv("NO_COLOR") != "" {
		return false
	}

	if os.Getenv("FORCE_COLOR") != "" {
		return true
	}

	if env := os.Getenv("ENVIRONMENT"); env == "development" || env == "dev" {
		return isatty.IsTerminal(os.Stdout.Fd())
	}

	return isatty.IsTerminal(os.Stdout.Fd())
}

func getConsoleLevelEncoder(useColors bool) zapcore.LevelEncoder {
	if useColors {
		return zapcore.CapitalColorLevelEncoder
	}
	return zapcore.CapitalLevelEncoder
}

// parseAuthData reads AUTH_DATA env var (or base64-encoded JSON) and sets individual
// Slack token env vars. This enables the ingress pattern where auth data is passed
// as a single structured env var instead of individual token vars.
func parseAuthData() {
	authData := os.Getenv("AUTH_DATA")
	if authData == "" {
		return
	}

	var raw []byte
	decoded, err := base64.StdEncoding.DecodeString(authData)
	if err == nil {
		raw = decoded
	} else {
		raw = []byte(authData)
	}

	var data map[string]string
	if err := json.Unmarshal(raw, &data); err != nil {
		return
	}

	mask := func(v string) string {
		if len(v) <= 8 {
			return "***"
		}
		return v[:4] + "***" + v[len(v)-4:]
	}
	fmt.Println("Parsed slack auth data:", map[string]string{
		"xoxc_token": mask(data["xoxc_token"]),
		"xoxd_token": mask(data["xoxd_token"]),
		"xoxp_token": mask(data["xoxp_token"]),
	})

	if v, ok := data["xoxc_token"]; ok && v != "" && os.Getenv("SLACK_MCP_XOXC_TOKEN") == "" {
		os.Setenv("SLACK_MCP_XOXC_TOKEN", v)
	}
	if v, ok := data["xoxd_token"]; ok && v != "" && os.Getenv("SLACK_MCP_XOXD_TOKEN") == "" {
		os.Setenv("SLACK_MCP_XOXD_TOKEN", v)
	}
	if v, ok := data["xoxp_token"]; ok && v != "" && os.Getenv("SLACK_MCP_XOXP_TOKEN") == "" {
		os.Setenv("SLACK_MCP_XOXP_TOKEN", v)
	}
}
