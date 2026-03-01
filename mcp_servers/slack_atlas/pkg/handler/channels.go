package handler

import (
	"context"
	"sort"
	"strings"

	"github.com/gocarina/gocsv"
	"github.com/korotovsky/slack-mcp-server/pkg/provider"
	"github.com/korotovsky/slack-mcp-server/pkg/text"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/slack-go/slack"
	"go.uber.org/zap"
)

type Channel struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Topic       string `json:"topic"`
	Purpose     string `json:"purpose"`
	MemberCount int    `json:"memberCount"`
	Cursor      string `json:"cursor"`
}

type ChannelsHandler struct {
	apiProvider *provider.ApiProvider
	validTypes  map[string]bool
	logger      *zap.Logger
}

func NewChannelsHandler(apiProvider *provider.ApiProvider, logger *zap.Logger) *ChannelsHandler {
	validTypes := make(map[string]bool, len(provider.AllChanTypes))
	for _, v := range provider.AllChanTypes {
		validTypes[v] = true
	}

	return &ChannelsHandler{
		apiProvider: apiProvider,
		validTypes:  validTypes,
		logger:      logger,
	}
}

func (ch *ChannelsHandler) ChannelsResource(ctx context.Context, request mcp.ReadResourceRequest) ([]mcp.ResourceContents, error) {
	ch.logger.Debug("ChannelsResource called", zap.Any("params", request.Params))

	client, err := ch.apiProvider.GetClient(ctx)
	if err != nil {
		ch.logger.Error("Failed to get Slack client", zap.Error(err))
		return nil, err
	}

	ar, err := client.AuthTest()
	if err != nil {
		ch.logger.Error("Auth test failed", zap.Error(err))
		return nil, err
	}

	ws, err := text.Workspace(ar.URL)
	if err != nil {
		ch.logger.Error("Failed to parse workspace from URL",
			zap.String("url", ar.URL),
			zap.Error(err),
		)
		return nil, err
	}

	channels, err := fetchAllChannels(ctx, client, provider.AllChanTypes)
	if err != nil {
		ch.logger.Error("Failed to fetch channels", zap.Error(err))
		return nil, err
	}

	var channelList []Channel
	for _, c := range channels {
		mapped := provider.MapChannelFromSlack(c)
		channelList = append(channelList, Channel{
			ID:          mapped.ID,
			Name:        mapped.Name,
			Topic:       mapped.Topic,
			Purpose:     mapped.Purpose,
			MemberCount: mapped.MemberCount,
		})
	}

	csvBytes, err := gocsv.MarshalBytes(&channelList)
	if err != nil {
		ch.logger.Error("Failed to marshal channels to CSV", zap.Error(err))
		return nil, err
	}

	return []mcp.ResourceContents{
		mcp.TextResourceContents{
			URI:      "slack://" + ws + "/channels",
			MIMEType: "text/csv",
			Text:     string(csvBytes),
		},
	}, nil
}

func (ch *ChannelsHandler) ChannelsHandler(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	ch.logger.Debug("ChannelsHandler called", zap.Any("params", request.Params))

	client, err := ch.apiProvider.GetClient(ctx)
	if err != nil {
		ch.logger.Error("Failed to get Slack client", zap.Error(err))
		return nil, err
	}

	sortType := request.GetString("sort", "popularity")
	types := request.GetString("channel_types", provider.PubChanType)
	cursor := request.GetString("cursor", "")
	limit := request.GetInt("limit", 0)

	ch.logger.Debug("Request parameters",
		zap.String("sort", sortType),
		zap.String("channel_types", types),
		zap.String("cursor", cursor),
		zap.Int("limit", limit),
	)

	channelTypes := []string{}
	for _, t := range strings.Split(types, ",") {
		t = strings.TrimSpace(t)
		if ch.validTypes[t] {
			channelTypes = append(channelTypes, t)
		} else if t != "" {
			ch.logger.Warn("Invalid channel type ignored", zap.String("type", t))
		}
	}

	if len(channelTypes) == 0 {
		ch.logger.Debug("No valid channel types provided, using defaults")
		channelTypes = append(channelTypes, provider.PubChanType)
		channelTypes = append(channelTypes, provider.PrivateChanType)
	}

	if limit == 0 {
		limit = 100
	}
	if limit > 999 {
		ch.logger.Warn("Limit exceeds maximum, capping to 999", zap.Int("requested", limit))
		limit = 999
	}

	params := &slack.GetConversationsParameters{
		Types:           channelTypes,
		Limit:           limit,
		Cursor:          cursor,
		ExcludeArchived: true,
	}

	channels, nextCursor, err := client.GetConversationsContext(ctx, params)
	if err != nil {
		ch.logger.Error("Slack GetConversationsContext failed", zap.Error(err))
		return nil, err
	}

	ch.logger.Debug("Fetched channels from Slack API",
		zap.Int("count", len(channels)),
		zap.Bool("has_next_page", nextCursor != ""),
	)

	var channelList []Channel
	for _, c := range channels {
		mapped := provider.MapChannelFromSlack(c)
		channelList = append(channelList, Channel{
			ID:          mapped.ID,
			Name:        mapped.Name,
			Topic:       mapped.Topic,
			Purpose:     mapped.Purpose,
			MemberCount: mapped.MemberCount,
		})
	}

	if sortType == "popularity" {
		sort.Slice(channelList, func(i, j int) bool {
			return channelList[i].MemberCount > channelList[j].MemberCount
		})
	}

	if len(channelList) > 0 && nextCursor != "" {
		channelList[len(channelList)-1].Cursor = nextCursor
	}

	csvBytes, err := gocsv.MarshalBytes(&channelList)
	if err != nil {
		ch.logger.Error("Failed to marshal channels to CSV", zap.Error(err))
		return nil, err
	}

	return mcp.NewToolResultText(string(csvBytes)), nil
}

// fetchAllChannels pages through the Slack API to retrieve all channels (used by ChannelsResource).
func fetchAllChannels(ctx context.Context, client provider.SlackAPI, channelTypes []string) ([]slack.Channel, error) {
	var all []slack.Channel
	params := &slack.GetConversationsParameters{
		Types:           channelTypes,
		Limit:           999,
		ExcludeArchived: true,
	}

	for {
		channels, nextCursor, err := client.GetConversationsContext(ctx, params)
		if err != nil {
			return nil, err
		}
		all = append(all, channels...)
		if nextCursor == "" {
			break
		}
		params.Cursor = nextCursor
	}

	return all, nil
}
