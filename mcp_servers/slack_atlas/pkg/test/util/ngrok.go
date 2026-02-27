package util

import (
	"context"
	"fmt"
	"net/url"
	"os"

	"golang.ngrok.com/ngrok/v2"
)

type Forwarding struct {
	URL      *url.URL
	Shutdown func()
}

func SetupForwarding(parentCtx context.Context, to string) (*Forwarding, error) {
	authToken := os.Getenv("NGROK_AUTH_TOKEN")
	if authToken == "" {
		return nil, fmt.Errorf("NGROK_AUTH_TOKEN not set")
	}

	ctx, cancel := context.WithCancel(parentCtx)

	agent, err := ngrok.NewAgent(
		ngrok.WithAuthtoken(authToken),
		ngrok.WithAutoConnect(false),
	)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("ngrok.NewAgent failed: %w", err)
	}

	err = agent.Connect(ctx)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("ngrok.Connect failed: %w", err)
	}

	fwd, err := agent.Forward(ctx,
		ngrok.WithUpstream(to),
	)
	if err != nil {
		cancel()
		return nil, fmt.Errorf("ngrok.Forward failed: %w", err)
	}

	return &Forwarding{
		URL: fwd.URL(),
		Shutdown: func() {
			cancel()
			<-fwd.Done()
		},
	}, nil
}
