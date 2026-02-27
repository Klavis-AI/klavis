package edge

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"runtime/trace"

	"github.com/google/uuid"
	"github.com/korotovsky/slack-mcp-server/pkg/limiter"
	"github.com/rusq/slack"
)

// search.* API

const perPage = 100

var ErrPagination = errors.New("pagination fault")

type Channel struct {
	slack.GroupConversation
	IsChannel  bool              `json:"is_channel"`
	IsGeneral  bool              `json:"is_general"`
	IsMember   bool              `json:"is_member"`
	NumMembers int               `json:"member_count"`
	Locale     string            `json:"locale"`
	Properties *slack.Properties `json:"properties"`
}

type SearchResponse[T any] struct {
	baseResponse
	Module     string          `json:"module"`
	Query      string          `json:"query"`
	Filters    json.RawMessage `json:"filters"`
	Pagination Pagination      `json:"pagination"`
	Items      []T             `json:"items"`
}

// searchForm is the form to be sent to the search endpoint.
type searchForm struct {
	BaseRequest
	Cursor               string            `json:"cursor,omitempty"`
	Module               string            `json:"module"`
	Query                string            `json:"query"`
	Page                 int               `json:"page,omitempty"`
	ClientReqID          string            `json:"client_req_id"`
	BrowseID             string            `json:"browse_session_id"`
	Extracts             int               `json:"extracts"`
	Highlight            int               `json:"highlight"`
	ExtraMsg             int               `json:"extra_message_data"`
	NoUserProfile        int               `json:"no_user_profile"`
	Count                int               `json:"count"`
	FileTitleOnly        bool              `json:"file_title_only"`
	QueryRewriteDisabled bool              `json:"query_rewrite_disabled"`
	IncludeFilesShares   int               `json:"include_files_shares"`
	Browse               string            `json:"browse"`
	SearchContext        string            `json:"search_context"`
	MaxFilterSuggestions int               `json:"max_filter_suggestions"`
	Sort                 searchSortType    `json:"sort"`
	SortDir              searchSortDir     `json:"sort_dir"`
	ChannelType          searchChannelType `json:"channel_type"`
	ExcludeMyChannels    int               `json:"exclude_my_channels"`
	SearchOnlyMyChannels bool              `json:"search_only_my_channels"`
	RecommendSource      string            `json:"recommend_source"`
	WebClientFields
}

type searchChannelType string

const (
	sctPublic          searchChannelType = "public"
	sctPrivate         searchChannelType = "private"
	scpArchived        searchChannelType = "archived"
	scpExternalShared  searchChannelType = "external_shared"
	scpExcludeArchived searchChannelType = "exclude_archived"
	scpPrivateExclude  searchChannelType = "private_exclude"
	scpAll             searchChannelType = ""
)

type searchSortDir string

const (
	ssdEmpty searchSortDir = ""
	ssdAsc   searchSortDir = "asc"
	ssdDesc  searchSortDir = "desc"
)

type searchSortType string

const (
	sstRecommended searchSortType = "recommended"
	sstName        searchSortType = "name"
)

func (cl *Client) SearchChannels(ctx context.Context, query string) ([]slack.Channel, error) {
	ctx, task := trace.NewTask(ctx, "SearchChannels")
	defer task.End()
	lg := slog.With("in", "SearchChannels", "query", query)

	trace.Logf(ctx, "params", "query=%q", query)

	clientReq, err := uuid.NewRandom()
	if err != nil {
		return nil, err
	}
	browseID, err := uuid.NewRandom()
	if err != nil {
		return nil, err
	}
	form := searchForm{
		BaseRequest:          BaseRequest{Token: cl.token},
		Module:               "channels",
		Query:                query,
		Page:                 0,
		ClientReqID:          clientReq.String(),
		BrowseID:             browseID.String(),
		Extracts:             0,
		Highlight:            0,
		Cursor:               "*",
		ExtraMsg:             0,
		NoUserProfile:        1,
		Count:                perPage,
		FileTitleOnly:        false,
		QueryRewriteDisabled: false,
		IncludeFilesShares:   1,
		Browse:               "standard",
		SearchContext:        "desktop_channel_browser",
		MaxFilterSuggestions: 10,
		Sort:                 sstName,
		SortDir:              ssdAsc,
		ChannelType:          scpAll,
		ExcludeMyChannels:    0,
		SearchOnlyMyChannels: false,
		RecommendSource:      "channel-browser",
		WebClientFields: WebClientFields{
			XReason:  "browser-query",
			XMode:    "online",
			XSonic:   true,
			XAppName: "client",
		},
	}

	const ep = "search.modules.channels"
	lim := limiter.Tier2boost.Limiter()
	var cc []slack.Channel
	for {
		resp, err := cl.PostForm(ctx, ep, values(form, true))
		if err != nil {
			return nil, err
		}
		var sr SearchResponse[Channel]
		if err := cl.ParseResponse(&sr, resp); err != nil {
			return nil, err
		}
		if err := sr.validate(ep); err != nil {
			return nil, err
		}

		// fix for the members count, mapping is incorrect in the slack.Channel
		// if the object is being used for search.modules.channels ep
		for _, c := range sr.Items {
			obj := slack.Channel{
				GroupConversation: c.GroupConversation,
				IsChannel:         true,
				IsGeneral:         c.IsGeneral,
				IsMember:          c.IsMember,
				Locale:            c.Locale,
				Properties:        c.Properties,
			}
			obj.NumMembers = c.NumMembers
			if obj.NumMembers == 0 {
				obj.IsArchived = true
			}

			cc = append(cc, obj)
		}
		if sr.Pagination.NextCursor == "" {
			lg.Debug("no more channels")
			break
		}
		lg.DebugContext(ctx, "pagination", "next_cursor", sr.Pagination.NextCursor)
		form.Cursor = sr.Pagination.NextCursor
		if err := lim.Wait(ctx); err != nil {
			return nil, err
		}
	}
	trace.Logf(ctx, "info", "channels found=%d", len(cc))
	lg.DebugContext(ctx, "channels", "count", len(cc))
	return cc, nil
}
