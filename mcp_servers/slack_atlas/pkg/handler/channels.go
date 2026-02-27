package handler

import (
	"context"
	"encoding/base64"
	"fmt"
	"sort"
	"strings"

	"github.com/gocarina/gocsv"
	"github.com/korotovsky/slack-mcp-server/pkg/provider"
	"github.com/korotovsky/slack-mcp-server/pkg/server/auth"
	"github.com/korotovsky/slack-mcp-server/pkg/text"
	"github.com/mark3labs/mcp-go/mcp"
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

	// mark3labs/mcp-go does not support middlewares for resources.
	if authenticated, err := auth.IsAuthenticated(ctx, ch.apiProvider.ServerTransport(), ch.logger); !authenticated {
		ch.logger.Error("Authentication failed for channels resource", zap.Error(err))
		return nil, err
	}

	var channelList []Channel

	if ready, err := ch.apiProvider.IsReady(); !ready {
		ch.logger.Error("API provider not ready", zap.Error(err))
		return nil, err
	}

	ar, err := ch.apiProvider.Slack().AuthTest()
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
		return nil, fmt.Errorf("failed to parse workspace from URL: %v", err)
	}

	channels := ch.apiProvider.ProvideChannelsMaps().Channels
	ch.logger.Debug("Retrieved channels from provider", zap.Int("count", len(channels)))

	for _, channel := range channels {
		channelList = append(channelList, Channel{
			ID:          channel.ID,
			Name:        channel.Name,
			Topic:       channel.Topic,
			Purpose:     channel.Purpose,
			MemberCount: channel.MemberCount,
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
	ch.logger.Debug("ChannelsHandler called")

	if ready, err := ch.apiProvider.IsReady(); !ready {
		ch.logger.Error("API provider not ready", zap.Error(err))
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

	// MCP Inspector v0.14.0 has issues with Slice type
	// introspection, so some type simplification makes sense here
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

	ch.logger.Debug("Validated channel types", zap.Strings("types", channelTypes))

	if limit == 0 {
		limit = 100
		ch.logger.Debug("Limit not provided, using default", zap.Int("limit", limit))
	}
	if limit > 999 {
		ch.logger.Warn("Limit exceeds maximum, capping to 999", zap.Int("requested", limit))
		limit = 999
	}

	var (
		nextcur     string
		channelList []Channel
	)

	allChannels := ch.apiProvider.ProvideChannelsMaps().Channels
	ch.logger.Debug("Total channels available", zap.Int("count", len(allChannels)))

	channels := filterChannelsByTypes(allChannels, channelTypes)
	ch.logger.Debug("Channels after filtering by type", zap.Int("count", len(channels)))

	var chans []provider.Channel

	chans, nextcur = paginateChannels(
		channels,
		cursor,
		limit,
	)

	ch.logger.Debug("Pagination results",
		zap.Int("returned_count", len(chans)),
		zap.Bool("has_next_page", nextcur != ""),
	)

	for _, channel := range chans {
		channelList = append(channelList, Channel{
			ID:          channel.ID,
			Name:        channel.Name,
			Topic:       channel.Topic,
			Purpose:     channel.Purpose,
			MemberCount: channel.MemberCount,
		})
	}

	switch sortType {
	case "popularity":
		ch.logger.Debug("Sorting channels by popularity (member count)")
		sort.Slice(channelList, func(i, j int) bool {
			return channelList[i].MemberCount > channelList[j].MemberCount
		})
	default:
		ch.logger.Debug("No sorting applied", zap.String("sort_type", sortType))
	}

	if len(channelList) > 0 && nextcur != "" {
		channelList[len(channelList)-1].Cursor = nextcur
		ch.logger.Debug("Added cursor to last channel", zap.String("cursor", nextcur))
	}

	csvBytes, err := gocsv.MarshalBytes(&channelList)
	if err != nil {
		ch.logger.Error("Failed to marshal channels to CSV", zap.Error(err))
		return nil, err
	}

	return mcp.NewToolResultText(string(csvBytes)), nil
}

func filterChannelsByTypes(channels map[string]provider.Channel, types []string) []provider.Channel {
	logger := zap.L()

	var result []provider.Channel
	typeSet := make(map[string]bool)

	for _, t := range types {
		typeSet[t] = true
	}

	publicCount := 0
	privateCount := 0
	imCount := 0
	mpimCount := 0

	for _, ch := range channels {
		if typeSet["public_channel"] && !ch.IsPrivate && !ch.IsIM && !ch.IsMpIM {
			result = append(result, ch)
			publicCount++
		}
		if typeSet["private_channel"] && ch.IsPrivate && !ch.IsIM && !ch.IsMpIM {
			result = append(result, ch)
			privateCount++
		}
		if typeSet["im"] && ch.IsIM {
			result = append(result, ch)
			imCount++
		}
		if typeSet["mpim"] && ch.IsMpIM {
			result = append(result, ch)
			mpimCount++
		}
	}

	logger.Debug("Channel filtering complete",
		zap.Int("total_input", len(channels)),
		zap.Int("total_output", len(result)),
		zap.Int("public_channels", publicCount),
		zap.Int("private_channels", privateCount),
		zap.Int("ims", imCount),
		zap.Int("mpims", mpimCount),
	)

	return result
}

func paginateChannels(channels []provider.Channel, cursor string, limit int) ([]provider.Channel, string) {
	logger := zap.L()

	sort.Slice(channels, func(i, j int) bool {
		return channels[i].ID < channels[j].ID
	})

	startIndex := 0
	if cursor != "" {
		if decoded, err := base64.StdEncoding.DecodeString(cursor); err == nil {
			lastID := string(decoded)
			for i, ch := range channels {
				if ch.ID > lastID {
					startIndex = i
					break
				}
			}
			logger.Debug("Decoded cursor",
				zap.String("cursor", cursor),
				zap.String("decoded_id", lastID),
				zap.Int("start_index", startIndex),
			)
		} else {
			logger.Warn("Failed to decode cursor",
				zap.String("cursor", cursor),
				zap.Error(err),
			)
		}
	}

	endIndex := startIndex + limit
	if endIndex > len(channels) {
		endIndex = len(channels)
	}

	paged := channels[startIndex:endIndex]

	var nextCursor string
	if endIndex < len(channels) {
		nextCursor = base64.StdEncoding.EncodeToString([]byte(channels[endIndex-1].ID))
		logger.Debug("Generated next cursor",
			zap.String("last_id", channels[endIndex-1].ID),
			zap.String("next_cursor", nextCursor),
		)
	}

	logger.Debug("Pagination complete",
		zap.Int("total_channels", len(channels)),
		zap.Int("start_index", startIndex),
		zap.Int("end_index", endIndex),
		zap.Int("page_size", len(paged)),
		zap.Bool("has_more", nextCursor != ""),
	)

	return paged, nextCursor
}
