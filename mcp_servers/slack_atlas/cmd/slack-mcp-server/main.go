package main

import (
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"

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

	p := provider.NewApiProvider(transport, logger)
	s := server.NewMCPServer(p, logger)

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

		listenAddr := host + ":" + port
		httpServer := s.ServeStreamableHTTP(listenAddr)
		logger.Info(
			fmt.Sprintf("StreamableHTTP server listening on %s:%s/mcp", host, port),
			zap.String("context", "console"),
			zap.String("host", host),
			zap.String("port", port),
		)

		if err := httpServer.Start(listenAddr); err != nil {
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
