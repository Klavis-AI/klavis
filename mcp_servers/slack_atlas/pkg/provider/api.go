package provider

import (
	"context"
	"errors"
	"os"
	"strings"

	"github.com/slack-go/slack"
	"go.uber.org/zap"
)

type contextKey string

const TokenContextKey contextKey = "slack_xoxp_token"

var AllChanTypes = []string{"mpim", "im", "public_channel", "private_channel"}
var PrivateChanType = "private_channel"
var PubChanType = "public_channel"

type SlackAPI interface {
	AuthTest() (*slack.AuthTestResponse, error)
	GetUsersContext(ctx context.Context, options ...slack.GetUsersOption) ([]slack.User, error)
	GetConversationsContext(ctx context.Context, params *slack.GetConversationsParameters) ([]slack.Channel, string, error)
	GetConversationHistoryContext(ctx context.Context, params *slack.GetConversationHistoryParameters) (*slack.GetConversationHistoryResponse, error)
	GetConversationRepliesContext(ctx context.Context, params *slack.GetConversationRepliesParameters) (msgs []slack.Message, hasMore bool, nextCursor string, err error)
	SearchContext(ctx context.Context, query string, params slack.SearchParameters) (*slack.SearchMessages, *slack.SearchFiles, error)
	PostMessageContext(ctx context.Context, channel string, options ...slack.MsgOption) (string, string, error)
	MarkConversationContext(ctx context.Context, channel, ts string) error
}

type Channel struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Topic       string `json:"topic"`
	Purpose     string `json:"purpose"`
	MemberCount int    `json:"memberCount"`
	IsIM        bool   `json:"im"`
	IsMpIM      bool   `json:"mpim"`
	IsPrivate   bool   `json:"private"`
}

type ApiProvider struct {
	transport string
	logger    *zap.Logger
}

func NewApiProvider(transport string, logger *zap.Logger) *ApiProvider {
	return &ApiProvider{
		transport: transport,
		logger:    logger,
	}
}

func (ap *ApiProvider) ServerTransport() string {
	return ap.transport
}

// GetClient creates a fresh Slack client from the per-request token stored in
// context (set by the HTTP contextFunc), falling back to the SLACK_MCP_XOXP_TOKEN
// env var for stdio transport / local development.
func (ap *ApiProvider) GetClient(ctx context.Context) (SlackAPI, error) {
	token, _ := ctx.Value(TokenContextKey).(string)
	if token == "" {
		token = os.Getenv("SLACK_MCP_XOXP_TOKEN")
	}
	if token == "" {
		return nil, errors.New("no auth token found in request context or environment")
	}
	return &slackClient{client: slack.New(token)}, nil
}

// slackClient is a thin wrapper around slack.Client implementing SlackAPI.
type slackClient struct {
	client *slack.Client
}

func (c *slackClient) AuthTest() (*slack.AuthTestResponse, error) {
	return c.client.AuthTest()
}

func (c *slackClient) GetUsersContext(ctx context.Context, options ...slack.GetUsersOption) ([]slack.User, error) {
	return c.client.GetUsersContext(ctx, options...)
}

func (c *slackClient) GetConversationsContext(ctx context.Context, params *slack.GetConversationsParameters) ([]slack.Channel, string, error) {
	return c.client.GetConversationsContext(ctx, params)
}

func (c *slackClient) GetConversationHistoryContext(ctx context.Context, params *slack.GetConversationHistoryParameters) (*slack.GetConversationHistoryResponse, error) {
	return c.client.GetConversationHistoryContext(ctx, params)
}

func (c *slackClient) GetConversationRepliesContext(ctx context.Context, params *slack.GetConversationRepliesParameters) (msgs []slack.Message, hasMore bool, nextCursor string, err error) {
	return c.client.GetConversationRepliesContext(ctx, params)
}

func (c *slackClient) SearchContext(ctx context.Context, query string, params slack.SearchParameters) (*slack.SearchMessages, *slack.SearchFiles, error) {
	return c.client.SearchContext(ctx, query, params)
}

func (c *slackClient) PostMessageContext(ctx context.Context, channel string, options ...slack.MsgOption) (string, string, error) {
	return c.client.PostMessageContext(ctx, channel, options...)
}

func (c *slackClient) MarkConversationContext(ctx context.Context, channel, ts string) error {
	return c.client.MarkConversationContext(ctx, channel, ts)
}

// MapChannelFromSlack converts a slack.Channel to our Channel model.
func MapChannelFromSlack(ch slack.Channel) Channel {
	name := ch.NameNormalized
	if name == "" {
		name = ch.Name
	}

	purpose := ch.Purpose.Value
	topic := ch.Topic.Value
	memberCount := ch.NumMembers

	if ch.IsIM {
		name = "@" + ch.User
		purpose = "DM with " + ch.User
		topic = ""
		memberCount = 2
	} else if ch.IsMpIM {
		name = "@" + name
		if len(ch.Members) > 0 {
			purpose = "Group DM with " + strings.Join(ch.Members, ", ")
			memberCount = len(ch.Members)
		} else {
			purpose = "Group DM"
		}
		topic = ""
	} else {
		name = "#" + name
	}

	return Channel{
		ID:          ch.ID,
		Name:        name,
		Topic:       topic,
		Purpose:     purpose,
		MemberCount: memberCount,
		IsIM:        ch.IsIM,
		IsMpIM:      ch.IsMpIM,
		IsPrivate:   ch.IsPrivate,
	}
}
