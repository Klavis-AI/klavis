package util

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/exec"
	"strconv"
	"syscall"
)

type MCPConfig struct {
	SSEKey             string
	MessageToolEnabled bool
	MessageToolMark    bool
}

type MCPConnection struct {
	Host     string
	Port     int
	Shutdown func()
}

func SetupMCP(cfg MCPConfig) (*MCPConnection, error) {
	xoxp := os.Getenv("SLACK_MCP_XOXP_TOKEN")
	if xoxp == "" {
		return nil, fmt.Errorf("SLACK_MCP_XOXP_TOKEN not set")
	}

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, fmt.Errorf("could not get free port: %w", err)
	}
	tcpAddr := ln.Addr().(*net.TCPAddr)
	ln.Close()

	host := "127.0.0.1"
	port := tcpAddr.Port

	ctx, cancel := context.WithCancel(context.Background())
	cwd, err := os.Getwd()
	if err != nil {
		log.Println(err, cwd)
	}

	cmd := exec.CommandContext(ctx,
		"go", "run", cwd+"/../../cmd/slack-mcp-server/main.go",
		"--transport", "sse",
	)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		Setpgid: true,
	}

	cmd.Env = append(os.Environ(),
		"SLACK_MCP_XOXP_TOKEN="+xoxp,
		"SLACK_MCP_HOST="+host,
		"SLACK_MCP_PORT="+strconv.Itoa(port),
		"SLACK_MCP_ADD_MESSAGE_TOOL=true",
		"SLACK_MCP_SSE_API_KEY="+cfg.SSEKey,
		"SLACK_MCP_USERS_CACHE=/tmp/users_cache.json",
		"SLACK_MCP_CHANNELS_CACHE=/tmp/channels_cache_v3.json",
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		cancel()
		return nil, fmt.Errorf("failed to start MCP server: %w", err)
	}

	done := make(chan struct{})
	go func() {
		_ = cmd.Wait()
		close(done)
	}()

	return &MCPConnection{
		Host: host,
		Port: port,
		Shutdown: func() {
			if cmd.Process != nil {
				syscall.Kill(-cmd.Process.Pid, syscall.SIGTERM)
			}
			cancel()
			<-done
		},
	}, nil
}
