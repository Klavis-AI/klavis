package provider

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/slack-go/slack"
)

// cachedClient implements SlackAPI by serving data from a static Slack export directory.
type cachedClient struct {
	channels      []slack.Channel
	users         []slack.User
	messages      map[string][]slack.Message // channelID -> messages sorted by ts
	channelByName map[string]string          // name -> channelID
}

type exportChannel struct {
	ID         string   `json:"id"`
	Name       string   `json:"name"`
	IsArchived bool     `json:"is_archived"`
	IsGeneral  bool     `json:"is_general"`
	Members    []string `json:"members"`
	Topic      struct {
		Value string `json:"value"`
	} `json:"topic"`
	Purpose struct {
		Value string `json:"value"`
	} `json:"purpose"`
}

type exportUser struct {
	ID       string  `json:"id"`
	Name     string  `json:"name"`
	RealName *string `json:"real_name"`
	Profile  struct {
		RealName    string `json:"real_name"`
		DisplayName string `json:"display_name"`
	} `json:"profile"`
	Deleted bool `json:"deleted"`
	IsBot   bool `json:"is_bot"`
}

// LoadCache reads a Slack export directory and returns a cachedClient.
func LoadCache(dataDir string) (*cachedClient, error) {
	c := &cachedClient{
		messages:      make(map[string][]slack.Message),
		channelByName: make(map[string]string),
	}

	data, err := os.ReadFile(filepath.Join(dataDir, "channels.json"))
	if err != nil {
		return nil, fmt.Errorf("read channels.json: %w", err)
	}
	var exportChans []exportChannel
	if err := json.Unmarshal(data, &exportChans); err != nil {
		return nil, fmt.Errorf("parse channels.json: %w", err)
	}

	for _, ec := range exportChans {
		var ch slack.Channel
		ch.ID = ec.ID
		ch.Name = ec.Name
		ch.NameNormalized = ec.Name
		ch.NumMembers = len(ec.Members)
		ch.Topic.Value = ec.Topic.Value
		ch.Purpose.Value = ec.Purpose.Value
		ch.IsArchived = ec.IsArchived
		ch.IsGeneral = ec.IsGeneral
		c.channels = append(c.channels, ch)
		c.channelByName[ec.Name] = ec.ID

		chanDir := filepath.Join(dataDir, ec.Name)
		files, _ := filepath.Glob(filepath.Join(chanDir, "*.json"))
		for _, f := range files {
			msgData, err := os.ReadFile(f)
			if err != nil {
				continue
			}
			var msgs []slack.Message
			if err := json.Unmarshal(msgData, &msgs); err != nil {
				continue
			}
			c.messages[ec.ID] = append(c.messages[ec.ID], msgs...)
		}
		sort.Slice(c.messages[ec.ID], func(i, j int) bool {
			return c.messages[ec.ID][i].Timestamp < c.messages[ec.ID][j].Timestamp
		})
	}

	data, err = os.ReadFile(filepath.Join(dataDir, "users.json"))
	if err != nil {
		return nil, fmt.Errorf("read users.json: %w", err)
	}
	var exportUsers []exportUser
	if err := json.Unmarshal(data, &exportUsers); err != nil {
		return nil, fmt.Errorf("parse users.json: %w", err)
	}
	for _, eu := range exportUsers {
		u := slack.User{ID: eu.ID, Name: eu.Name, Deleted: eu.Deleted, IsBot: eu.IsBot}
		if eu.RealName != nil {
			u.RealName = *eu.RealName
		} else {
			u.RealName = eu.Profile.RealName
		}
		u.Profile.RealName = eu.Profile.RealName
		u.Profile.DisplayName = eu.Profile.DisplayName
		c.users = append(c.users, u)
	}

	return c, nil
}

func (c *cachedClient) AuthTest() (*slack.AuthTestResponse, error) {
	return &slack.AuthTestResponse{
		URL:    "https://dumleservers.slack.com/",
		Team:   "dumleservers",
		User:   "bot",
		UserID: "U000000000",
	}, nil
}

func (c *cachedClient) GetUsersContext(_ context.Context, _ ...slack.GetUsersOption) ([]slack.User, error) {
	return c.users, nil
}

func (c *cachedClient) GetConversationsContext(_ context.Context, params *slack.GetConversationsParameters) ([]slack.Channel, string, error) {
	typeSet := make(map[string]bool, len(params.Types))
	for _, t := range params.Types {
		typeSet[t] = true
	}

	var filtered []slack.Channel
	for _, ch := range c.channels {
		if params.ExcludeArchived && ch.IsArchived {
			continue
		}
		if typeSet["public_channel"] {
			filtered = append(filtered, ch)
		}
	}

	start := 0
	if params.Cursor != "" {
		start, _ = strconv.Atoi(params.Cursor)
	}
	if start >= len(filtered) {
		return nil, "", nil
	}

	limit := params.Limit
	if limit == 0 {
		limit = 100
	}
	end := start + limit
	nextCursor := ""
	if end < len(filtered) {
		nextCursor = strconv.Itoa(end)
	} else {
		end = len(filtered)
	}
	return filtered[start:end], nextCursor, nil
}

func (c *cachedClient) GetConversationHistoryContext(_ context.Context, params *slack.GetConversationHistoryParameters) (*slack.GetConversationHistoryResponse, error) {
	msgs := c.messages[params.ChannelID]

	var filtered []slack.Message
	for _, m := range msgs {
		ts := m.Timestamp
		if params.Oldest != "" {
			if params.Inclusive && ts < params.Oldest {
				continue
			}
			if !params.Inclusive && ts <= params.Oldest {
				continue
			}
		}
		if params.Latest != "" {
			if params.Inclusive && ts > params.Latest {
				continue
			}
			if !params.Inclusive && ts >= params.Latest {
				continue
			}
		}
		filtered = append(filtered, m)
	}

	start := 0
	if params.Cursor != "" {
		start, _ = strconv.Atoi(params.Cursor)
	}
	if start >= len(filtered) {
		return &slack.GetConversationHistoryResponse{}, nil
	}

	limit := params.Limit
	if limit == 0 {
		limit = 100
	}
	end := start + limit
	hasMore := end < len(filtered)
	nextCursor := ""
	if hasMore {
		nextCursor = strconv.Itoa(end)
	} else {
		end = len(filtered)
	}

	resp := &slack.GetConversationHistoryResponse{
		HasMore:  hasMore,
		Messages: filtered[start:end],
	}
	resp.ResponseMetaData.NextCursor = nextCursor
	return resp, nil
}

func (c *cachedClient) GetConversationRepliesContext(_ context.Context, params *slack.GetConversationRepliesParameters) ([]slack.Message, bool, string, error) {
	var replies []slack.Message
	for _, m := range c.messages[params.ChannelID] {
		if m.ThreadTimestamp == params.Timestamp || m.Timestamp == params.Timestamp {
			replies = append(replies, m)
		}
	}
	return replies, false, "", nil
}

func (c *cachedClient) SearchContext(_ context.Context, query string, params slack.SearchParameters) (*slack.SearchMessages, *slack.SearchFiles, error) {
	freeText, filters := parseCacheQuery(query)

	// Determine channels to search
	var channelIDs []string
	if inVals, ok := filters["in"]; ok {
		for _, name := range inVals {
			name = strings.TrimPrefix(name, "#")
			if id, ok := c.channelByName[name]; ok {
				channelIDs = append(channelIDs, id)
			}
		}
	} else {
		for _, ch := range c.channels {
			channelIDs = append(channelIDs, ch.ID)
		}
	}

	var fromUser string
	if vals, ok := filters["from"]; ok && len(vals) > 0 {
		fromUser = strings.Trim(vals[0], "<@>")
	}

	threadOnly := false
	if vals, ok := filters["is"]; ok {
		for _, v := range vals {
			if v == "thread" {
				threadOnly = true
			}
		}
	}

	beforeDate, _ := filterVal(filters, "before")
	afterDate, _ := filterVal(filters, "after")
	onDate, hasOn := filterVal(filters, "on")
	if !hasOn {
		onDate, _ = filterVal(filters, "during")
	}

	lowerFreeText := strings.ToLower(freeText)

	var allMatches []slack.SearchMessage
	for _, chID := range channelIDs {
		chName := c.channelName(chID)
		for _, m := range c.messages[chID] {
			if fromUser != "" && m.User != fromUser {
				continue
			}
			if threadOnly && m.ThreadTimestamp == "" {
				continue
			}
			if lowerFreeText != "" && !strings.Contains(strings.ToLower(m.Text), lowerFreeText) {
				continue
			}
			msgDate := tsToDate(m.Timestamp)
			if onDate != "" && !strings.HasPrefix(msgDate, onDate) {
				continue
			}
			if beforeDate != "" && msgDate >= beforeDate {
				continue
			}
			if afterDate != "" && msgDate <= afterDate {
				continue
			}
			allMatches = append(allMatches, slack.SearchMessage{
				Type:      "message",
				Channel:   slack.CtxChannel{ID: chID, Name: chName},
				User:      m.User,
				Username:  m.Username,
				Timestamp: m.Timestamp,
				Text:      m.Text,
			})
		}
	}

	page := params.Page
	if page < 1 {
		page = 1
	}
	perPage := params.Count
	if perPage == 0 {
		perPage = 20
	}
	total := len(allMatches)
	start := (page - 1) * perPage
	if start > total {
		start = total
	}
	end := start + perPage
	if end > total {
		end = total
	}

	return &slack.SearchMessages{
		Matches: allMatches[start:end],
		Paging: slack.Paging{
			Count: perPage,
			Total: total,
			Page:  page,
			Pages: (total + perPage - 1) / perPage,
		},
		Pagination: slack.Pagination{
			TotalCount: total,
			Page:       page,
			PerPage:    perPage,
			PageCount:  page,
			First:      start + 1,
			Last:       end,
		},
		Total: total,
	}, nil, nil
}

func (c *cachedClient) PostMessageContext(_ context.Context, _ string, _ ...slack.MsgOption) (string, string, error) {
	return "", "", fmt.Errorf("write permission not allowed")
}

func (c *cachedClient) MarkConversationContext(_ context.Context, _, _ string) error {
	return nil
}

func (c *cachedClient) channelName(id string) string {
	for _, ch := range c.channels {
		if ch.ID == id {
			return ch.Name
		}
	}
	return ""
}

func filterVal(filters map[string][]string, key string) (string, bool) {
	if vals, ok := filters[key]; ok && len(vals) > 0 {
		return vals[0], true
	}
	return "", false
}

func parseCacheQuery(q string) (string, map[string][]string) {
	filters := make(map[string][]string)
	var freeText []string
	for _, tok := range strings.Fields(q) {
		if idx := strings.Index(tok, ":"); idx > 0 {
			key := strings.ToLower(tok[:idx])
			val := tok[idx+1:]
			switch key {
			case "in", "from", "with", "before", "after", "on", "during", "is":
				filters[key] = append(filters[key], val)
				continue
			}
		}
		freeText = append(freeText, tok)
	}
	return strings.Join(freeText, " "), filters
}

func tsToDate(ts string) string {
	parts := strings.SplitN(ts, ".", 2)
	sec, err := strconv.ParseInt(parts[0], 10, 64)
	if err != nil {
		return ""
	}
	return time.Unix(sec, 0).UTC().Format("2006-01-02")
}
