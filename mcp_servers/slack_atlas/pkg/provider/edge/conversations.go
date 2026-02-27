package edge

import (
	"context"
	"encoding/json"
	"runtime/trace"

	"github.com/rusq/slack"
)

// conversations.* API

// conversationsGenericInfoForm is the request to conversations.genericInfo
type conversationsGenericInfoForm struct {
	BaseRequest
	UpdatedChannels string `json:"updated_channels"` // i.e. {"C065H568ZAT":0}
	WebClientFields
}

type conversationsGenericInfoResponse struct {
	baseResponse
	Channels            []slack.Channel `json:"channels"`
	UnchangedChannelIDs []string        `json:"unchanged_channel_ids"`
}

func (cl *Client) ConversationsGenericInfo(ctx context.Context, channelID ...string) ([]slack.Channel, error) {
	ctx, task := trace.NewTask(ctx, "ConversationsGenericInfo")
	defer task.End()
	trace.Logf(ctx, "params", "channelID=%v", channelID)

	updChannel := make(map[string]int, len(channelID))
	for _, id := range channelID {
		updChannel[id] = 0
	}
	b, err := json.Marshal(updChannel)
	if err != nil {
		return nil, err
	}
	form := conversationsGenericInfoForm{
		BaseRequest: BaseRequest{
			Token: cl.token,
		},
		UpdatedChannels: string(b),
		WebClientFields: webclientReason("fallback:UnknownFetchManager"),
	}
	resp, err := cl.PostForm(ctx, "conversations.genericInfo", values(form, true))
	if err != nil {
		return nil, err
	}
	var r conversationsGenericInfoResponse
	if err := cl.ParseResponse(&r, resp); err != nil {
		return nil, err
	}
	return r.Channels, nil
}

type conversationsViewForm struct {
	BaseRequest
	CanonicalAvatars             bool   `json:"canonical_avatars"`
	NoUserProfile                bool   `json:"no_user_profile"`
	IgnoreReplies                bool   `json:"ignore_replies"`
	NoSelf                       bool   `json:"no_self"`
	IncludeFullUsers             bool   `json:"include_full_users"`
	IncludeUseCases              bool   `json:"include_use_cases"`
	IncludeStories               bool   `json:"include_stories"`
	NoMembers                    bool   `json:"no_members"`
	IncludeMutationTimestamps    bool   `json:"include_mutation_timestamps"`
	Count                        int    `json:"count"`
	Channel                      string `json:"channel"`
	IncludeFreeTeamExtraMessages bool   `json:"include_free_team_extra_messages"`
	WebClientFields
}

type ConversationsViewResponse struct {
	Users  []User            `json:"users"`
	IM     IM                `json:"im"`
	Emojis map[string]string `json:"emojis"`
	// we don't care about the rest of the response
}

func (cl *Client) ConversationsView(ctx context.Context, channelID string) (ConversationsViewResponse, error) {
	ctx, task := trace.NewTask(ctx, "ConversationsView")
	defer task.End()
	trace.Logf(ctx, "params", "channelID=%v", channelID)

	form := conversationsViewForm{
		BaseRequest: BaseRequest{
			Token: cl.token,
		},
		CanonicalAvatars:          true,
		NoUserProfile:             true,
		IgnoreReplies:             true,
		NoSelf:                    true,
		IncludeFullUsers:          false,
		IncludeUseCases:           false,
		IncludeStories:            false,
		NoMembers:                 true,
		IncludeMutationTimestamps: false,
		Count:                     50,
		Channel:                   channelID,
		WebClientFields:           webclientReason(""),
	}
	resp, err := cl.PostForm(ctx, "conversations.view", values(form, true))
	if err != nil {
		return ConversationsViewResponse{}, err
	}
	var r = struct {
		baseResponse
		ConversationsViewResponse
	}{}
	if err := cl.ParseResponse(&r, resp); err != nil {
		return ConversationsViewResponse{}, err
	}
	return r.ConversationsViewResponse, nil
}
