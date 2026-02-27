package edge

import (
	"context"
	"errors"

	"github.com/korotovsky/slack-mcp-server/pkg/limiter"
	"github.com/rusq/slack"
	"golang.org/x/sync/errgroup"
)

type UsersListRequest struct {
	BaseRequest
	Channels                []string `json:"channels"`
	PresentFirst            bool     `json:"present_first,omitempty"`
	Filter                  string   `json:"filter"`
	Index                   string   `json:"index,omitempty"`
	Locale                  string   `json:"locale,omitempty"`
	IncludeProfileOnlyUsers bool     `json:"include_profile_only_users,omitempty"`
	Marker                  string   `json:"marker,omitempty"` // pagination, it must contain the next_marker from the previous response
	Count                   int      `json:"count"`
}

type UsersListResponse struct {
	Results    []User `json:"results"`
	NextMarker string `json:"next_marker"` // pagination, marker value which must be used in the next request, if not empty.
	baseResponse
}

type User struct {
	ID                     string         `json:"id"`
	TeamID                 string         `json:"team_id"`
	Name                   string         `json:"name"`
	Deleted                bool           `json:"deleted"`
	Color                  string         `json:"color"`
	RealName               string         `json:"real_name"`
	Tz                     string         `json:"tz"`
	TzLabel                string         `json:"tz_label"`
	TzOffset               int64          `json:"tz_offset"`
	Profile                Profile        `json:"profile"`
	IsAdmin                bool           `json:"is_admin"`
	IsOwner                bool           `json:"is_owner"`
	IsPrimaryOwner         bool           `json:"is_primary_owner"`
	IsRestricted           bool           `json:"is_restricted"`
	IsUltraRestricted      bool           `json:"is_ultra_restricted"`
	IsBot                  bool           `json:"is_bot"`
	IsAppUser              bool           `json:"is_app_user"`
	Updated                slack.JSONTime `json:"updated"`
	IsEmailConfirmed       bool           `json:"is_email_confirmed"`
	WhoCanShareContactCard string         `json:"who_can_share_contact_card"`
	Has2Fa                 *bool          `json:"has_2fa,omitempty"`
}

type Profile struct {
	Title                  string  `json:"title"`
	Phone                  string  `json:"phone"`
	Skype                  string  `json:"skype"`
	RealName               string  `json:"real_name"`
	RealNameNormalized     string  `json:"real_name_normalized"`
	DisplayName            string  `json:"display_name"`
	DisplayNameNormalized  string  `json:"display_name_normalized"`
	Fields                 any     `json:"fields"`
	StatusText             string  `json:"status_text"`
	StatusEmoji            string  `json:"status_emoji"`
	StatusEmojiDisplayInfo []any   `json:"status_emoji_display_info"`
	StatusExpiration       int64   `json:"status_expiration"`
	AvatarHash             string  `json:"avatar_hash"`
	GuestInvitedBy         string  `json:"guest_invited_by"`
	ImageOriginal          *string `json:"image_original,omitempty"`
	IsCustomImage          *bool   `json:"is_custom_image,omitempty"`
	Email                  string  `json:"email"`
	FirstName              *string `json:"first_name,omitempty"`
	LastName               *string `json:"last_name,omitempty"`
	StatusTextCanonical    string  `json:"status_text_canonical"`
	Team                   string  `json:"team"`
}

type UsersInfoRequest struct {
	BaseRequest
	CheckInteraction        bool             `json:"check_interaction"`
	IncludeProfileOnlyUsers bool             `json:"include_profile_only_users"`
	UpdatedIDS              map[string]int64 `json:"updated_ids"`
}

type UserInfoResponse struct {
	Results     []UserInfo      `json:"results"`
	FailedIDS   []string        `json:"failed_ids"`
	PendingIDS  []string        `json:"pending_ids"`
	CanInteract map[string]bool `json:"can_interact"`
	baseResponse
}

type UserInfo struct {
	ID                     string  `json:"id"`
	TeamID                 string  `json:"team_id"`
	Name                   string  `json:"name"`
	Color                  string  `json:"color"`
	IsBot                  bool    `json:"is_bot"`
	IsAppUser              bool    `json:"is_app_user"`
	Deleted                bool    `json:"deleted"`
	Profile                Profile `json:"profile"`
	IsStranger             bool    `json:"is_stranger"`
	Updated                int64   `json:"updated"`
	WhoCanShareContactCard string  `json:"who_can_share_contact_card"`
}

var ErrNotOK = errors.New("server returned NOT OK")

// GetUsers returns users from the slack edge api for the channel.  User IDs
// should be provided by the caller.  If ids is empty, does nothing.
//
// This tries to replicate the logic of the Slack client, when it fetches
// the channel users while being logged in as a guest user.
func (cl *Client) GetUsers(ctx context.Context, userID ...string) ([]UserInfo, error) {
	if len(userID) == 0 {
		return []UserInfo{}, nil
	}
	updatedIds := make(map[string]int64, len(userID))
	for _, id := range userID {
		updatedIds[id] = 0
	}

	lim := limiter.Tier3.Limiter()
	var users []UserInfo
	for {
		uiresp, err := cl.UsersInfo(ctx, &UsersInfoRequest{
			CheckInteraction:        true,
			IncludeProfileOnlyUsers: true,
			UpdatedIDS:              updatedIds,
		})
		if err != nil {
			return nil, err
		}
		if !uiresp.Ok {
			return nil, ErrNotOK
		}
		if len(uiresp.Results) > 0 {
			users = append(users, uiresp.Results...)
		}
		if len(uiresp.PendingIDS) == 0 {
			break
		}
		for _, ui := range uiresp.Results {
			updatedIds[ui.ID] = ui.Updated
		}
		if err := lim.Wait(ctx); err != nil {
			return nil, err
		}
	}
	return users, nil
}

// UsersInfo calls a users.info endpoint.  This endpoint does not return results
// straight away.  It may return "pending ids", and when it does, it should be
// called again to get the actual user info (see [Client.GetUsers]).
func (cl *Client) UsersInfo(ctx context.Context, req *UsersInfoRequest) (*UserInfoResponse, error) {
	var ui UserInfoResponse
	if err := cl.callEdgeAPI(ctx, &ui, "users/info", req); err != nil {
		return nil, err
	}
	return &ui, nil
}

type ChannelsMembershipRequest struct {
	BaseRequest
	Channel string   `json:"channel"`
	Users   []string `json:"users"`
	AsAdmin bool     `json:"as_admin"`
}

type ChannelsMembershipResponse struct {
	Channel    string   `json:"channel"`
	NonMembers []string `json:"non_members"`
	baseResponse
}

// ChannelsMembership calls channels/membership endpoint.
func (cl *Client) ChannelsMembership(ctx context.Context, req *ChannelsMembershipRequest) (*ChannelsMembershipResponse, error) {
	var um ChannelsMembershipResponse
	if err := cl.callEdgeAPI(ctx, &um, "channels/membership", req); err != nil {
		return nil, err
	}
	return &um, nil
}

// UserList lists users in the conversation(s).
func (cl *Client) UsersList(ctx context.Context, channelIDs ...string) ([]User, error) {
	if len(channelIDs) == 0 {
		return nil, errors.New("no channel IDs provided")
	}
	channelIDs, dmIDs := splitDMs(channelIDs)
	var uu []User
	eg, ctx := errgroup.WithContext(ctx)
	if len(channelIDs) > 0 {
		eg.Go(func() error {
			u, err := cl.publicUserList(ctx, channelIDs)
			if err != nil {
				return err
			}
			uu = append(uu, u...)
			return nil
		})
	}
	if len(dmIDs) > 0 {
		eg.Go(func() error {
			u, err := cl.directUserList(ctx, dmIDs)
			if err != nil {
				return err
			}
			uu = append(uu, u...)
			return nil
		})
	}
	if err := eg.Wait(); err != nil {
		return nil, err
	}
	return uu, nil
}

func (cl *Client) publicUserList(ctx context.Context, channelIDs []string) ([]User, error) {
	const (
		// everyone = "everyone AND NOT bots AND NOT apps"
		everyone = "everyone"
		filter   = "people"
		index    = "users_by_display_name"

		count = 50
	)
	req := UsersListRequest{
		Channels:     channelIDs,
		Filter:       everyone,
		PresentFirst: false,
		Index:        index,
		Locale:       "en-US",
		Marker:       "",
		Count:        count,
	}
	uu := make([]User, 0, count)
	lim := limiter.Tier3.Limiter()
	for {
		var ur UsersListResponse
		if err := cl.callEdgeAPI(ctx, &ur, "users/list", &req); err != nil {
			return nil, err
		}
		if len(ur.Results) == 0 && ur.NextMarker == "" {
			break
		}
		uu = append(uu, ur.Results...)
		if ur.NextMarker == "" {
			break
		}
		req.Marker = ur.NextMarker
		if err := lim.Wait(ctx); err != nil {
			return nil, err
		}
	}
	return uu, nil
}

// directUserList tries to get users from the direct message channels.  It is
// much slower than getting users from the public channels, as it uses
// conversations.view endpoint.
func (cl *Client) directUserList(ctx context.Context, dmIDs []string) ([]User, error) {
	if len(dmIDs) == 0 {
		return nil, errors.New("no direct message IDs provided")
	}
	var ret []User
	lim := limiter.Tier3.Limiter()
	for _, id := range dmIDs {
		resp, err := cl.ConversationsView(ctx, id)
		if err != nil {
			return nil, err
		}
		ret = append(ret, resp.Users...)
		if err := lim.Wait(ctx); err != nil {
			return nil, err
		}
	}
	return ret, nil
}

func splitDMs(IDs []string) (chans []string, dms []string) {
	for _, id := range IDs {
		if len(id) == 0 {
			continue
		}
		if len(id) > 0 && id[0] == 'D' {
			dms = append(dms, id)
		} else {
			chans = append(chans, id)
		}
	}
	return chans, dms
}
