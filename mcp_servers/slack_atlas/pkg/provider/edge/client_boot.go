package edge

import (
	"context"
	"encoding/json"
	"runtime/trace"
	"time"

	"github.com/korotovsky/slack-mcp-server/pkg/provider/edge/fasttime"
	"github.com/rusq/slack"
)

// client.userBoot API.  It was too large to chuck into the client.* file.

type clientUserBootForm struct {
	BaseRequest
	MinChannelUpdated          int64 `json:"min_channel_updated"`
	IncludeMinVersionBumpCheck int   `json:"include_min_version_bump_check"`
	VersionTS                  int64 `json:"version_ts"`
	BuildVersionTS             int64 `json:"build_version_ts"`
	WebClientFields
}

// ClientUserBoot calls the client.userBoot API.
func (cl *Client) ClientUserBoot(ctx context.Context) (*ClientUserBootResponse, error) {
	ctx, task := trace.NewTask(ctx, "ClientUserBoot")
	defer task.End()

	future := time.Now().Add(24 * time.Hour)
	form := clientUserBootForm{
		BaseRequest:                BaseRequest{Token: cl.token},
		IncludeMinVersionBumpCheck: 1,
		VersionTS:                  future.Unix(),
		BuildVersionTS:             future.Unix(),
		WebClientFields:            webclientReason("initial-data"),
	}
	var ub ClientUserBootResponse
	resp, err := cl.PostForm(ctx, "client.userBoot", values(form, true))
	if err != nil {
		return nil, err
	}
	if err := cl.ParseResponse(&ub, resp); err != nil {
		return nil, err
	}
	return &ub, nil
}

func UnmarshalClientUserBootResponse(data []byte) (ClientUserBootResponse, error) {
	var r ClientUserBootResponse
	err := json.Unmarshal(data, &r)
	return r, err
}

func (r *ClientUserBootResponse) Marshal() ([]byte, error) {
	return json.Marshal(r)
}

// "client.userBoot"
type ClientUserBootResponse struct {
	baseResponse
	Self                     Self              `json:"self"`
	Team                     Team              `json:"team"`
	IMs                      []IM              `json:"ims"`
	Workspaces               []Workspace       `json:"workspaces"`
	DefaultWorkspace         string            `json:"default_workspace"`
	AccountTypes             AccountTypes      `json:"account_types"`
	AcceptTosURL             any               `json:"accept_tos_url"`
	IsOpen                   []string          `json:"is_open"`
	IsEurope                 bool              `json:"is_europe"`
	TranslationsCacheTs      fasttime.Time     `json:"translations_cache_ts"`
	EmojiCacheTs             fasttime.Time     `json:"emoji_cache_ts"`
	AppCommandsCacheTs       fasttime.Time     `json:"app_commands_cache_ts"`
	CacheTsVersion           string            `json:"cache_ts_version"`
	DND                      DND               `json:"dnd"`
	Prefs                    map[string]any    `json:"prefs"`
	Subteams                 Subteams          `json:"subteams"`
	MobileAppRequiresUpgrade bool              `json:"mobile_app_requires_upgrade"`
	Starred                  []any             `json:"starred"`
	ChannelsPriority         ChannelsPriority  `json:"channels_priority"`
	ReadOnlyChannels         []string          `json:"read_only_channels"`
	NonThreadableChannels    []any             `json:"non_threadable_channels"`
	ThreadOnlyChannels       []any             `json:"thread_only_channels"`
	Channels                 []UserBootChannel `json:"channels"`
	UnchangedChannelIDS      []any             `json:"unchanged_channel_ids"`
	CacheVersion             string            `json:"cache_version"`
	SlackRoute               string            `json:"slack_route"`
	AuthMinLastFetched       int64             `json:"auth_min_last_fetched"`
	CanAccessClientV2        bool              `json:"can_access_client_v2"`
	ShouldReload             bool              `json:"should_reload"`
	ClientMinVersion         int64             `json:"client_min_version"`
	BuildVersionEnabled      bool              `json:"build_version_enabled"`
	Links                    Links             `json:"links"`
}

type UserBootChannel struct {
	ID                      string            `json:"id"`
	Name                    string            `json:"name"`
	IsChannel               bool              `json:"is_channel"`
	IsGroup                 bool              `json:"is_group"`
	IsIM                    bool              `json:"is_im"`
	IsMpim                  bool              `json:"is_mpim"`
	IsPrivate               bool              `json:"is_private"`
	Created                 int64             `json:"created"`
	IsArchived              bool              `json:"is_archived"`
	IsGeneral               bool              `json:"is_general"`
	Unlinked                int64             `json:"unlinked"`
	NameNormalized          string            `json:"name_normalized"`
	IsShared                bool              `json:"is_shared"`
	IsFrozen                bool              `json:"is_frozen"`
	IsOrgShared             bool              `json:"is_org_shared"`
	IsPendingEXTShared      bool              `json:"is_pending_ext_shared"`
	PendingShared           []json.RawMessage `json:"pending_shared"`
	ContextTeamID           string            `json:"context_team_id"`
	Updated                 int64             `json:"updated"`
	ParentConversation      json.RawMessage   `json:"parent_conversation"`
	Creator                 string            `json:"creator"`
	IsEXTShared             bool              `json:"is_ext_shared"`
	SharedTeamIDS           []string          `json:"shared_team_ids"`
	PendingConnectedTeamIDS []json.RawMessage `json:"pending_connected_team_ids"`
	Topic                   Purpose           `json:"topic"`
	Purpose                 Purpose           `json:"purpose"`
	Properties              *Properties       `json:"properties,omitempty"`
	PreviousNames           []json.RawMessage `json:"previous_names"`
	IsMember                bool              `json:"is_member,omitempty"`
	LastRead                fasttime.Time     `json:"last_read,omitempty"`
	Latest                  fasttime.Time     `json:"latest,omitempty"`
	IsOpen                  bool              `json:"is_open,omitempty"`
	Members                 []string          `json:"members"`
}

func (c *UserBootChannel) SlackChannel() slack.Channel {
	return slack.Channel{
		GroupConversation: slack.GroupConversation{
			Conversation: slack.Conversation{
				ID:                 c.ID,
				Created:            slack.JSONTime(c.Created),
				IsOpen:             c.IsOpen,
				LastRead:           c.LastRead.SlackString(),
				Latest:             &slack.Message{},
				UnreadCount:        0,
				UnreadCountDisplay: 0,
				IsGroup:            c.IsGroup,
				IsShared:           c.IsShared,
				IsIM:               c.IsIM,
				IsExtShared:        c.IsEXTShared,
				IsOrgShared:        c.IsOrgShared,
				IsGlobalShared:     false,
				IsPendingExtShared: c.IsPendingEXTShared,
				IsPrivate:          c.IsPrivate,
				IsMpIM:             c.IsMpim,
				Unlinked:           int(c.Unlinked),
				NameNormalized:     c.NameNormalized,
				NumMembers:         len(c.Members),
				Priority:           0,
				User:               "",
				ConnectedTeamIDs:   []string{},
				SharedTeamIDs:      []string{},
				InternalTeamIDs:    []string{},
			},
			Name:       c.Name,
			Creator:    c.Creator,
			IsArchived: c.IsArchived,
			Members:    c.Members,
			Topic: slack.Topic{
				Value:   c.Topic.Value,
				Creator: c.Topic.Creator,
				LastSet: slack.JSONTime(c.Topic.LastSet),
			},
			Purpose: slack.Purpose{
				Value:   c.Purpose.Value,
				Creator: c.Purpose.Creator,
				LastSet: slack.JSONTime(c.Purpose.LastSet),
			},
		},
		IsChannel: c.IsChannel,
		IsGeneral: c.IsGeneral,
		IsMember:  c.IsMember,
		Locale:    "",
	}
}

type AccountTypes struct {
	IsAdmin        []any `json:"is_admin"`
	IsOwner        []any `json:"is_owner"`
	IsPrimaryOwner []any `json:"is_primary_owner"`
}

type Properties struct {
	PostingRestrictedTo SlackConnectAllowedWorkspaces `json:"posting_restricted_to"`
}

type SlackConnectAllowedWorkspaces struct {
	Type []string `json:"type"`
}

type Purpose struct {
	Value   string `json:"value"`
	Creator string `json:"creator"`
	LastSet int64  `json:"last_set"`
}

type ChannelsPriority struct {
}

type DND struct {
	DNDEnabled     bool           `json:"dnd_enabled"`
	NextDNDStartTs slack.JSONTime `json:"next_dnd_start_ts"`
	NextDNDEndTs   slack.JSONTime `json:"next_dnd_end_ts"`
	SnoozeEnabled  bool           `json:"snooze_enabled"`
}

type Links struct {
	DomainsTs int64 `json:"domains_ts"`
}

type Self struct {
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
	FirstLogin             slack.JSONTime `json:"first_login"`
	LobSalesHomeEnabled    bool           `json:"lob_sales_home_enabled"`
	ManualPresence         string         `json:"manual_presence"`
}

type Profile1 struct {
	Title                  string `json:"title"`
	Phone                  string `json:"phone"`
	Skype                  string `json:"skype"`
	RealName               string `json:"real_name"`
	RealNameNormalized     string `json:"real_name_normalized"`
	DisplayName            string `json:"display_name"`
	DisplayNameNormalized  string `json:"display_name_normalized"`
	Fields                 any    `json:"fields"`
	StatusText             string `json:"status_text"`
	StatusEmoji            string `json:"status_emoji"`
	StatusEmojiDisplayInfo []any  `json:"status_emoji_display_info"`
	StatusExpiration       int64  `json:"status_expiration"`
	AvatarHash             string `json:"avatar_hash"`
	Email                  string `json:"email"`
	FirstName              string `json:"first_name"`
	LastName               string `json:"last_name"`
	StatusTextCanonical    string `json:"status_text_canonical"`
	Team                   string `json:"team"`
}

type Subteams struct {
	Self []any `json:"self"`
}

type Team struct {
	ID                  string `json:"id"`
	Name                string `json:"name"`
	URL                 string `json:"url"`
	Domain              string `json:"domain"`
	EmailDomain         string `json:"email_domain"`
	Icon                Icon   `json:"icon"`
	AvatarBaseURL       string `json:"avatar_base_url"`
	IsVerified          bool   `json:"is_verified"`
	Plan                string `json:"plan"`
	IsPlanFrozen        bool   `json:"is_plan_frozen"`
	Prefs               Prefs  `json:"prefs"`
	OnboardingChannelID string `json:"onboarding_channel_id"`
	ImageProxyURL       string `json:"image_proxy_url"`
	OverStorageLimit    bool   `json:"over_storage_limit"`
	MessagesCount       int64  `json:"messages_count"`
	LobSalesHomeEnabled bool   `json:"lob_sales_home_enabled"`
}

type Icon struct {
	ImageDefault bool   `json:"image_default"`
	Image34      string `json:"image_34"`
	Image44      string `json:"image_44"`
	Image68      string `json:"image_68"`
	Image88      string `json:"image_88"`
	Image102     string `json:"image_102"`
	Image230     string `json:"image_230"`
	Image132     string `json:"image_132"`
}

type Prefs struct {
	Locale                                                         string                         `json:"locale"`
	InvitesOnlyAdmins                                              bool                           `json:"invites_only_admins"`
	InvitesLimit                                                   bool                           `json:"invites_limit"`
	ShowJoinLeave                                                  bool                           `json:"show_join_leave"`
	DefaultChannels                                                []string                       `json:"default_channels"`
	Image34                                                        string                         `json:"image_34"`
	Image44                                                        string                         `json:"image_44"`
	Image68                                                        string                         `json:"image_68"`
	Image88                                                        string                         `json:"image_88"`
	Image102                                                       string                         `json:"image_102"`
	Image132                                                       string                         `json:"image_132"`
	Image230                                                       string                         `json:"image_230"`
	ImageOriginal                                                  string                         `json:"image_original"`
	SeenInvitesOnlyAdminsWarning                                   bool                           `json:"seen_invites_only_admins_warning"`
	WhoCanAtEveryone                                               string                         `json:"who_can_at_everyone"`
	WhoCanAtChannel                                                string                         `json:"who_can_at_channel"`
	WhoCanPostGeneral                                              string                         `json:"who_can_post_general"`
	WarnBeforeAtChannel                                            string                         `json:"warn_before_at_channel"`
	WhoCanCreateChannels                                           string                         `json:"who_can_create_channels"`
	WhoCanArchiveChannels                                          string                         `json:"who_can_archive_channels"`
	WhoCanCreateGroups                                             string                         `json:"who_can_create_groups"`
	WhoCanKickChannels                                             string                         `json:"who_can_kick_channels"`
	WhoCanKickGroups                                               string                         `json:"who_can_kick_groups"`
	InvitedUserPreset                                              InvitedUserPreset              `json:"invited_user_preset"`
	WelcomePlaceEnabled                                            bool                           `json:"welcome_place_enabled"`
	HasInstalledApps                                               bool                           `json:"has_installed_apps"`
	WhoCanManageChannelPostingPrefs                                string                         `json:"who_can_manage_channel_posting_prefs"`
	AdminCustomizedQuickReactions                                  []string                       `json:"admin_customized_quick_reactions"`
	AllUsersCanPurchase                                            bool                           `json:"all_users_can_purchase"`
	AllowAdminRetentionOverride                                    int64                          `json:"allow_admin_retention_override"`
	AllowAudioClipSharingSlackConnect                              bool                           `json:"allow_audio_clip_sharing_slack_connect"`
	AllowAudioClips                                                bool                           `json:"allow_audio_clips"`
	AllowBoxCfs                                                    bool                           `json:"allow_box_cfs"`
	AllowCalls                                                     bool                           `json:"allow_calls"`
	AllowCallsInteractiveScreenSharing                             bool                           `json:"allow_calls_interactive_screen_sharing"`
	AllowClipDownloads                                             string                         `json:"allow_clip_downloads"`
	AllowContentReview                                             bool                           `json:"allow_content_review"`
	AllowDeveloperSandboxes                                        string                         `json:"allow_developer_sandboxes"`
	AllowFreeAutomatedTrials                                       bool                           `json:"allow_free_automated_trials"`
	AllowHuddles                                                   bool                           `json:"allow_huddles"`
	AllowHuddlesTranscriptions                                     bool                           `json:"allow_huddles_transcriptions"`
	AllowHuddlesVideo                                              bool                           `json:"allow_huddles_video"`
	AllowLists                                                     string                         `json:"allow_lists"`
	AllowLockThread                                                bool                           `json:"allow_lock_thread"`
	AllowMediaTranscriptions                                       bool                           `json:"allow_media_transcriptions"`
	AllowMessageDeletion                                           bool                           `json:"allow_message_deletion"`
	AllowNativeGIFPicker                                           bool                           `json:"allow_native_gif_picker"`
	AllowRetentionOverride                                         bool                           `json:"allow_retention_override"`
	AllowSpaceship                                                 string                         `json:"allow_spaceship"`
	AllowSponsoredSlackConnections                                 bool                           `json:"allow_sponsored_slack_connections"`
	AllowVideoClipSharingSlackConnect                              bool                           `json:"allow_video_clip_sharing_slack_connect"`
	AllowVideoClips                                                bool                           `json:"allow_video_clips"`
	AppDirOnly                                                     bool                           `json:"app_dir_only"`
	AppManagementApps                                              []any                          `json:"app_management_apps"`
	AppWhitelistEnabled                                            bool                           `json:"app_whitelist_enabled"`
	AppWhitelistRequestsRequireCommentEnabled                      bool                           `json:"app_whitelist_requests_require_comment_enabled"`
	AtlasOrgChartsAccess                                           string                         `json:"atlas_org_charts_access"`
	AtlasProfilesAccess                                            string                         `json:"atlas_profiles_access"`
	AutomaticWelcomeDmEnabled                                      bool                           `json:"automatic_welcome_dm_enabled"`
	BillingEmailDaily                                              bool                           `json:"billing_email_daily"`
	BillingEmailMonthly                                            bool                           `json:"billing_email_monthly"`
	BlockFileDownload                                              bool                           `json:"block_file_download"`
	BlockFileTypes                                                 bool                           `json:"block_file_types"`
	BoxAppInstalled                                                bool                           `json:"box_app_installed"`
	CallsApps                                                      CallsApps                      `json:"calls_apps"`
	CallsLocations                                                 []any                          `json:"calls_locations"`
	CanAcceptSlackConnectChannelInvites                            bool                           `json:"can_accept_slack_connect_channel_invites"`
	CanCreateExternalLimitedInvite                                 bool                           `json:"can_create_external_limited_invite"`
	CanCreateSlackConnectChannelInvite                             bool                           `json:"can_create_slack_connect_channel_invite"`
	CanReceiveSharedChannelsInvites                                bool                           `json:"can_receive_shared_channels_invites"`
	CanvasRetentionDuration                                        int64                          `json:"canvas_retention_duration"`
	CanvasRetentionType                                            int64                          `json:"canvas_retention_type"`
	CanvasVersionHistoryEnabled                                    bool                           `json:"canvas_version_history_enabled"`
	ChannelAuditExportEnabled                                      bool                           `json:"channel_audit_export_enabled"`
	ChannelEmailAddressesEnabled                                   bool                           `json:"channel_email_addresses_enabled"`
	ComplianceExportStart                                          int64                          `json:"compliance_export_start"`
	ContentReviewEnabled                                           bool                           `json:"content_review_enabled"`
	CreatedWithGoogle                                              bool                           `json:"created_with_google"`
	CustomContactEmail                                             any                            `json:"custom_contact_email"`
	CustomStatusDefaultEmoji                                       string                         `json:"custom_status_default_emoji"`
	CustomStatusPresets                                            [][]string                     `json:"custom_status_presets"`
	DailyPromptsEnabled                                            bool                           `json:"daily_prompts_enabled"`
	DefaultChannelCreationEnabled                                  bool                           `json:"default_channel_creation_enabled"`
	DefaultCreatePrivateChannel                                    bool                           `json:"default_create_private_channel"`
	DefaultFunctionReuseVisibility                                 DefaultFunctionReuseVisibility `json:"default_function_reuse_visibility"`
	DefaultRxns                                                    []string                       `json:"default_rxns"`
	DisableEmailIngestion                                          bool                           `json:"disable_email_ingestion"`
	DisableFileDeleting                                            bool                           `json:"disable_file_deleting"`
	DisableFileEditing                                             bool                           `json:"disable_file_editing"`
	DisableFileUploads                                             string                         `json:"disable_file_uploads"`
	DisablePrivacyAndCookiePolicy                                  bool                           `json:"disable_privacy_and_cookie_policy"`
	DisableSidebarConnectPrompts                                   []any                          `json:"disable_sidebar_connect_prompts"`
	DisableSidebarInstallPrompts                                   []any                          `json:"disable_sidebar_install_prompts"`
	DisallowPublicFileUrls                                         bool                           `json:"disallow_public_file_urls"`
	Discoverable                                                   string                         `json:"discoverable"`
	DisplayAnniversaryCelebration                                  bool                           `json:"display_anniversary_celebration"`
	DisplayDefaultPhone                                            bool                           `json:"display_default_phone"`
	DisplayEmailAddresses                                          bool                           `json:"display_email_addresses"`
	DisplayExternalEmailAddresses                                  bool                           `json:"display_external_email_addresses"`
	DisplayNewHireCelebration                                      bool                           `json:"display_new_hire_celebration"`
	DisplayPronouns                                                bool                           `json:"display_pronouns"`
	DisplayRealNames                                               bool                           `json:"display_real_names"`
	DmRetentionDuration                                            int64                          `json:"dm_retention_duration"`
	DmRetentionRedactionDuration                                   int64                          `json:"dm_retention_redaction_duration"`
	DmRetentionType                                                int64                          `json:"dm_retention_type"`
	DNDAfterFriday                                                 string                         `json:"dnd_after_friday"`
	DNDAfterMonday                                                 string                         `json:"dnd_after_monday"`
	DNDAfterSaturday                                               string                         `json:"dnd_after_saturday"`
	DNDAfterSunday                                                 string                         `json:"dnd_after_sunday"`
	DNDAfterThursday                                               string                         `json:"dnd_after_thursday"`
	DNDAfterTuesday                                                string                         `json:"dnd_after_tuesday"`
	DNDAfterWednesday                                              string                         `json:"dnd_after_wednesday"`
	DNDBeforeFriday                                                string                         `json:"dnd_before_friday"`
	DNDBeforeMonday                                                string                         `json:"dnd_before_monday"`
	DNDBeforeSaturday                                              string                         `json:"dnd_before_saturday"`
	DNDBeforeSunday                                                string                         `json:"dnd_before_sunday"`
	DNDBeforeThursday                                              string                         `json:"dnd_before_thursday"`
	DNDBeforeTuesday                                               string                         `json:"dnd_before_tuesday"`
	DNDBeforeWednesday                                             string                         `json:"dnd_before_wednesday"`
	DNDDays                                                        string                         `json:"dnd_days"`
	DNDEnabled                                                     bool                           `json:"dnd_enabled"`
	DNDEnabledFriday                                               string                         `json:"dnd_enabled_friday"`
	DNDEnabledMonday                                               string                         `json:"dnd_enabled_monday"`
	DNDEnabledSaturday                                             string                         `json:"dnd_enabled_saturday"`
	DNDEnabledSunday                                               string                         `json:"dnd_enabled_sunday"`
	DNDEnabledThursday                                             string                         `json:"dnd_enabled_thursday"`
	DNDEnabledTuesday                                              string                         `json:"dnd_enabled_tuesday"`
	DNDEnabledWednesday                                            string                         `json:"dnd_enabled_wednesday"`
	DNDEndHour                                                     string                         `json:"dnd_end_hour"`
	DNDStartHour                                                   string                         `json:"dnd_start_hour"`
	DNDWeekdaysOffAllday                                           bool                           `json:"dnd_weekdays_off_allday"`
	DropboxLegacyPicker                                            bool                           `json:"dropbox_legacy_picker"`
	EmojiOnlyAdmins                                                bool                           `json:"emoji_only_admins"`
	EnableConnectDmEarlyAccess                                     bool                           `json:"enable_connect_dm_early_access"`
	EnableDomainAllowlistForCea                                    bool                           `json:"enable_domain_allowlist_for_cea"`
	EnableInfoBarriers                                             bool                           `json:"enable_info_barriers"`
	EnableMpdmToPrivateChannelConversion                           bool                           `json:"enable_mpdm_to_private_channel_conversion"`
	EnableSharedChannels                                           int64                          `json:"enable_shared_channels"`
	EnterpriseDefaultChannels                                      []any                          `json:"enterprise_default_channels"`
	EnterpriseHasCorporateExports                                  bool                           `json:"enterprise_has_corporate_exports"`
	EnterpriseIntuneEnabled                                        bool                           `json:"enterprise_intune_enabled"`
	EnterpriseJointeamRequests                                     any                            `json:"enterprise_jointeam_requests"`
	EnterpriseMandatoryChannels                                    []any                          `json:"enterprise_mandatory_channels"`
	EnterpriseMdmDateEnabled                                       int64                          `json:"enterprise_mdm_date_enabled"`
	EnterpriseMdmDisableFileDownload                               bool                           `json:"enterprise_mdm_disable_file_download"`
	EnterpriseMdmLevel                                             int64                          `json:"enterprise_mdm_level"`
	EnterpriseMdmToken                                             string                         `json:"enterprise_mdm_token"`
	EnterpriseMobileDeviceCheck                                    bool                           `json:"enterprise_mobile_device_check"`
	EnterpriseTeamCreationRequest                                  EnterpriseTeamCreationRequest  `json:"enterprise_team_creation_request"`
	EXTAuditLogRetentionDuration                                   int64                          `json:"ext_audit_log_retention_duration"`
	EXTAuditLogRetentionType                                       int64                          `json:"ext_audit_log_retention_type"`
	FileLimitWhitelisted                                           bool                           `json:"file_limit_whitelisted"`
	FileRetentionDuration                                          int64                          `json:"file_retention_duration"`
	FileRetentionType                                              int64                          `json:"file_retention_type"`
	FilepickerAppFirstInstall                                      bool                           `json:"filepicker_app_first_install"`
	FlagContentAdminDash                                           bool                           `json:"flag_content_admin_dash"`
	FlagMessageUsersToNotify                                       []any                          `json:"flag_message_users_to_notify"`
	GdprEnabled                                                    bool                           `json:"gdpr_enabled"`
	GdriveEnabledTeam                                              bool                           `json:"gdrive_enabled_team"`
	GroupRetentionDuration                                         int64                          `json:"group_retention_duration"`
	GroupRetentionType                                             int64                          `json:"group_retention_type"`
	HasComplianceExport                                            bool                           `json:"has_compliance_export"`
	HasHipaaCompliance                                             bool                           `json:"has_hipaa_compliance"`
	HasSeenPartnerPromo                                            bool                           `json:"has_seen_partner_promo"`
	HasSharedInvites                                               bool                           `json:"has_shared_invites"`
	HermesAllowInteractionsWithWorkflowsOwnedBySlackConnectedTeams bool                           `json:"hermes_allow_interactions_with_workflows_owned_by_slack_connected_teams"`
	HermesHasAcceptedTos                                           bool                           `json:"hermes_has_accepted_tos"`
	HermesTriggersTrippableBySlackConnectedTeams                   bool                           `json:"hermes_triggers_trippable_by_slack_connected_teams"`
	HideGsuiteInviteOption                                         bool                           `json:"hide_gsuite_invite_option"`
	HidePersonOptOut                                               bool                           `json:"hide_person_opt_out"`
	HideReferers                                                   bool                           `json:"hide_referers"`
	IdentityLinksPrefs                                             EnterpriseTeamCreationRequest  `json:"identity_links_prefs"`
	ImageDefault                                                   bool                           `json:"image_default"`
	InstantSlackEnabled                                            bool                           `json:"instant_slack_enabled"`
	InviteRequestsEnabled                                          bool                           `json:"invite_requests_enabled"`
	LoadingOnlyAdmins                                              bool                           `json:"loading_only_admins"`
	LoudChannelMentionsLimit                                       int64                          `json:"loud_channel_mentions_limit"`
	MagicUnfurlsEnabled                                            bool                           `json:"magic_unfurls_enabled"`
	MemberAnalyticsDisabled                                        bool                           `json:"member_analytics_disabled"`
	MlOptOut                                                       bool                           `json:"ml_opt_out"`
	MobilePasscodeTimeoutInSeconds                                 int64                          `json:"mobile_passcode_timeout_in_seconds"`
	MobileSessionDuration                                          int64                          `json:"mobile_session_duration"`
	MsgEditWindowMins                                              int64                          `json:"msg_edit_window_mins"`
	NoEmailUserProvisionType                                       string                         `json:"no_email_user_provision_type"`
	NotificationRedactionType                                      string                         `json:"notification_redaction_type"`
	NotifyPendingEnabled                                           bool                           `json:"notify_pending_enabled"`
	NTLMCredentialDomains                                          string                         `json:"ntlm_credential_domains"`
	OnedriveAppInstalled                                           bool                           `json:"onedrive_app_installed"`
	OnedriveEnabledTeam                                            bool                           `json:"onedrive_enabled_team"`
	PremiumWorkflowNotifications                                   PremiumWorkflowNotifications   `json:"premium_workflow_notifications"`
	PrivateChannelAnalyticsDisabled                                bool                           `json:"private_channel_analytics_disabled"`
	PrivateChannelMembershipLimit                                  int64                          `json:"private_channel_membership_limit"`
	PrivateRetentionRedactionDuration                              int64                          `json:"private_retention_redaction_duration"`
	PublicRetentionRedactionDuration                               int64                          `json:"public_retention_redaction_duration"`
	ReceivedEscRouteToChannelAwarenessMessage                      bool                           `json:"received_esc_route_to_channel_awareness_message"`
	RetentionDuration                                              int64                          `json:"retention_duration"`
	RetentionType                                                  int64                          `json:"retention_type"`
	RichPreviewsDefault                                            string                         `json:"rich_previews_default"`
	SamlEnable                                                     bool                           `json:"saml_enable"`
	SearchFeedbackOptOut                                           bool                           `json:"search_feedback_opt_out"`
	SelfServeSelect                                                bool                           `json:"self_serve_select"`
	SessionDuration                                                int64                          `json:"session_duration"`
	SessionDurationType                                            int64                          `json:"session_duration_type"`
	ShowLegacyPaidBenefitsPage                                     bool                           `json:"show_legacy_paid_benefits_page"`
	ShowLegacyWorkflows                                            bool                           `json:"show_legacy_workflows"`
	ShowMobilePromos                                               bool                           `json:"show_mobile_promos"`
	SignInWithSlackDefault                                         string                         `json:"sign_in_with_slack_default"`
	SignInWithSlackDisabled                                        bool                           `json:"sign_in_with_slack_disabled"`
	SingleUserExports                                              bool                           `json:"single_user_exports"`
	SlackAIDailyRecapOptOut                                        bool                           `json:"slack_ai_daily_recap_opt_out"`
	SlackAIDetailedFeedbackOptOut                                  bool                           `json:"slack_ai_detailed_feedback_opt_out"`
	SlackAISearchSuggestedQueries                                  []any                          `json:"slack_ai_search_suggested_queries"`
	SlackConnectAccountVisibility                                  string                         `json:"slack_connect_account_visibility"`
	SlackConnectAllowedWorkspaces                                  SlackConnectAllowedWorkspaces  `json:"slack_connect_allowed_workspaces"`
	SlackConnectApprovalType                                       string                         `json:"slack_connect_approval_type"`
	SlackConnectDmOnlyVerifiedOrgs                                 bool                           `json:"slack_connect_dm_only_verified_orgs"`
	SlackConnectFileUploadSharingEnabled                           bool                           `json:"slack_connect_file_upload_sharing_enabled"`
	SlackbotResponsesDisabled                                      bool                           `json:"slackbot_responses_disabled"`
	SlackbotResponsesOnlyAdmins                                    bool                           `json:"slackbot_responses_only_admins"`
	SpaceshipWorkspaceSettingVisible                               bool                           `json:"spaceship_workspace_setting_visible"`
	SsoChangeEmail                                                 bool                           `json:"sso_change_email"`
	SsoChooseUsername                                              bool                           `json:"sso_choose_username"`
	SsoDisableEmails                                               bool                           `json:"sso_disable_emails"`
	SsoOptional                                                    bool                           `json:"sso_optional"`
	SsoSignupRestrictions                                          int64                          `json:"sso_signup_restrictions"`
	SsoSyncWithProvider                                            bool                           `json:"sso_sync_with_provider"`
	StatsOnlyAdmins                                                bool                           `json:"stats_only_admins"`
	SubteamsAutoCreateAdmin                                        bool                           `json:"subteams_auto_create_admin"`
	SubteamsAutoCreateOwner                                        bool                           `json:"subteams_auto_create_owner"`
	ThornSaferScan                                                 bool                           `json:"thorn_safer_scan"`
	TwoFactorAuthRequired                                          int64                          `json:"two_factor_auth_required"`
	TwoFactorPreventSMS                                            int64                          `json:"two_factor_prevent_sms"`
	TwoFactorRequired                                              bool                           `json:"two_factor_required"`
	UneditableUserProfileFields                                    []any                          `json:"uneditable_user_profile_fields"`
	UseBrowserPicker                                               bool                           `json:"use_browser_picker"`
	UseWorkspaceIconForSingleWorkspaceUsers                        bool                           `json:"use_workspace_icon_for_single_workspace_users"`
	UsesCustomizedCustomStatusPresets                              bool                           `json:"uses_customized_custom_status_presets"`
	WarnUserBeforeLogoutDesktop                                    bool                           `json:"warn_user_before_logout_desktop"`
	WarnUserBeforeLogoutMobile                                     bool                           `json:"warn_user_before_logout_mobile"`
	WfbDefaultConnectorVisibility                                  string                         `json:"wfb_default_connector_visibility"`
	WhoCanAcceptSlackConnectChannelInvites                         SlackConnectAllowedWorkspaces  `json:"who_can_accept_slack_connect_channel_invites"`
	WhoCanChangeTeamProfile                                        string                         `json:"who_can_change_team_profile"`
	WhoCanCreateChannelEmailAddresses                              SlackConnectAllowedWorkspaces  `json:"who_can_create_channel_email_addresses"`
	WhoCanCreateDeleteUserGroups                                   string                         `json:"who_can_create_delete_user_groups"`
	WhoCanCreateExternalLimitedInvite                              SlackConnectAllowedWorkspaces  `json:"who_can_create_external_limited_invite"`
	WhoCanCreateSharedChannels                                     string                         `json:"who_can_create_shared_channels"`
	WhoCanCreateSlackConnectChannelInvite                          SlackConnectAllowedWorkspaces  `json:"who_can_create_slack_connect_channel_invite"`
	WhoCanCreateWorkflows                                          SlackConnectAllowedWorkspaces  `json:"who_can_create_workflows"`
	WhoCanDmAnyone                                                 SlackConnectAllowedWorkspaces  `json:"who_can_dm_anyone"`
	WhoCanEditUserGroups                                           string                         `json:"who_can_edit_user_groups"`
	WhoCanManageEXTSharedChannels                                  SlackConnectAllowedWorkspaces  `json:"who_can_manage_ext_shared_channels"`
	WhoCanManageGuests                                             SlackConnectAllowedWorkspaces  `json:"who_can_manage_guests"`
	WhoCanManageIntegrations                                       SlackConnectAllowedWorkspaces  `json:"who_can_manage_integrations"`
	WhoCanManagePrivateChannels                                    WhoCanManageP                  `json:"who_can_manage_private_channels"`
	WhoCanManagePrivateChannelsAtWorkspaceLevel                    WhoCanManageP                  `json:"who_can_manage_private_channels_at_workspace_level"`
	WhoCanManagePublicChannels                                     WhoCanManageP                  `json:"who_can_manage_public_channels"`
	WhoCanManageSharedChannels                                     SlackConnectAllowedWorkspaces  `json:"who_can_manage_shared_channels"`
	WhoCanPostInSharedChannels                                     SlackConnectAllowedWorkspaces  `json:"who_can_post_in_shared_channels"`
	WhoCanRequestEXTSharedChannels                                 SlackConnectAllowedWorkspaces  `json:"who_can_request_ext_shared_channels"`
	WhoCanReviewFlaggedContent                                     SlackConnectAllowedWorkspaces  `json:"who_can_review_flagged_content"`
	WhoCanUseHermes                                                SlackConnectAllowedWorkspaces  `json:"who_can_use_hermes"`
	WhoCanViewMessageActivity                                      WhoCanViewMessageActivity      `json:"who_can_view_message_activity"`
	WhoHasTeamVisibility                                           string                         `json:"who_has_team_visibility"`
	WorkflowBuilderEnabled                                         bool                           `json:"workflow_builder_enabled"`
	WorkflowExtensionStepsBetaOptIn                                bool                           `json:"workflow_extension_steps_beta_opt_in"`
	WorkflowExtensionStepsEnabled                                  bool                           `json:"workflow_extension_steps_enabled"`
	WorkflowsExportCSVEnabled                                      bool                           `json:"workflows_export_csv_enabled"`
	WorkflowsWebhookTriggerEnabled                                 bool                           `json:"workflows_webhook_trigger_enabled"`
	AuthMode                                                       string                         `json:"auth_mode"`
}

type CallsApps struct {
	Video []any `json:"video"`
	Audio []any `json:"audio"`
}

type DefaultFunctionReuseVisibility struct {
	Visibility string `json:"visibility"`
}

type EnterpriseTeamCreationRequest struct {
	IsEnabled bool `json:"is_enabled"`
}

type InvitedUserPreset struct {
	EnableInvitedUser bool `json:"enable_invited_user"`
}

type PremiumWorkflowNotifications struct {
	NotificationsEnabled bool   `json:"notifications_enabled"`
	NotificationLocation string `json:"notification_location"`
}

type WhoCanManageP struct {
	User []any    `json:"user"`
	Type []string `json:"type"`
}

type WhoCanViewMessageActivity struct {
	Type        []string `json:"type"`
	ChannelType []string `json:"channel_type"`
}

type Workspace struct {
	ID            string `json:"id"`
	Name          string `json:"name"`
	URL           string `json:"url"`
	Domain        string `json:"domain"`
	EmailDomain   string `json:"email_domain"`
	Icon          Icon   `json:"icon"`
	AvatarBaseURL string `json:"avatar_base_url"`
	IsVerified    bool   `json:"is_verified"`
	Prefs         Prefs  `json:"prefs"`
}
