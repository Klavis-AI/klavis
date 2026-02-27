// Package edge provides a limited implementation of undocumented Slack Edge
// API necessary to get the data from a slack workspace.
//
// It handles rate limit retries internally (but only once).
package edge

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"os"
	"runtime/trace"
	"strings"
	"time"

	"github.com/rusq/slackauth"
	"github.com/rusq/slackdump/v3/auth"
	"github.com/rusq/tagops"
	"github.com/slack-go/slack"
)

type httpClient interface {
	Do(*http.Request) (*http.Response, error)
}

type Client struct {
	// cl is the http client to use
	cl httpClient
	// edgeAPI is the edge API endpoint
	edgeAPI string
	// webclientAPI is the webclient APIs endpoint
	webclientAPI string
	// token is the slack token
	token string

	// teamID is the team ID
	teamID string
	tape   io.WriteCloser
}

type Option func(*Client)

func WithTape(tape io.WriteCloser) Option {
	return func(cl *Client) {
		cl.tape = tape
	}
}

// OptionHTTPClient - provide a custom http client to the slack client.
func OptionHTTPClient(client httpClient) func(*Client) {
	return func(cl *Client) {
		cl.cl = client
	}
}

var (
	ErrNoTeamID = errors.New("teamID is empty")
	ErrNoToken  = errors.New("token is empty")
)

func NewWithClient(workspaceName string, teamID string, token string, cl *http.Client, opt ...Option) (*Client, error) {
	if teamID == "" {
		return nil, ErrNoTeamID
	}
	if token == "" {
		return nil, ErrNoToken
	}
	tape, err := os.Create("tape.txt")
	if err != nil {
		return nil, err
	}
	return &Client{
		cl:           cl,
		token:        token,
		teamID:       teamID,
		webclientAPI: fmt.Sprintf("https://%s.slack.com/api/", workspaceName),
		edgeAPI:      fmt.Sprintf("https://edgeapi.slack.com/cache/%s/", teamID),
		tape:         tape,
	}, nil
}

func NewWithToken(ctx context.Context, token string, cookies []*http.Cookie) (*Client, error) {
	if token == "" {
		return nil, ErrNoToken
	}
	prov, err := auth.NewValueCookiesAuth(token, cookies)
	if err != nil {
		return nil, err
	}
	return New(ctx, prov)
}

type nopTape struct{}

func (nopTape) Write(p []byte) (n int, err error) {
	return len(p), nil
}

func (nopTape) Close() error {
	return nil
}

// NewWithInfo is the same as New, but doesn't call the AuthTest on
// initialisation.  Caller must ensure that the token is valid.
func NewWithInfo(info *slack.AuthTestResponse, prov auth.Provider, opt ...Option) (*Client, error) {
	hcl, err := prov.HTTPClient()
	if err != nil {
		return nil, err
	}
	c := &Client{
		cl:           hcl,
		token:        prov.SlackToken(),
		teamID:       info.TeamID,
		webclientAPI: info.URL + "api/",
		edgeAPI:      fmt.Sprintf("https://edgeapi.slack.com/cache/%s/", info.TeamID),
		tape:         nopTape{},
	}

	for _, o := range opt {
		o(c)
	}
	return c, nil
}

func New(ctx context.Context, prov auth.Provider, opt ...Option) (*Client, error) {
	info, err := prov.Test(ctx)
	if err != nil {
		return nil, err
	}
	return NewWithInfo(&slack.AuthTestResponse{
		URL:          info.URL,
		Team:         info.Team,
		User:         info.User,
		TeamID:       info.TeamID,
		UserID:       info.UserID,
		EnterpriseID: info.EnterpriseID,
		BotID:        info.BotID,
	}, prov, opt...)
}

func (cl *Client) Raw() httpClient {
	return cl.cl
}

func (cl *Client) Close() error {
	if cl.tape != nil {
		return cl.tape.Close()
	}
	return nil
}

type BaseRequest struct {
	Token string `json:"token"`
}

type baseResponse struct {
	Ok               bool             `json:"ok"`
	Error            string           `json:"error,omitempty"`
	ResponseMetadata ResponseMetadata `json:"response_metadata,omitempty"`
}

func (r baseResponse) validate(ep string) error {
	if !r.Ok {
		return &APIError{Err: r.Error, Metadata: r.ResponseMetadata, Endpoint: ep}
	}
	return nil
}

type ResponseMetadata struct {
	Messages   []string `json:"messages,omitempty"`
	NextCursor string   `json:"next_cursor,omitempty"`
}

func (r *BaseRequest) SetToken(token string) {
	r.Token = token
}

func (r *BaseRequest) IsTokenSet() bool {
	return len(r.Token) > 0
}

type PostRequest interface {
	SetToken(string)
	IsTokenSet() bool
}

const (
	hdrContentType = "Content-Type"
)

// PostJSON posts a request to the edge API.  The request is marshalled to
// JSON and the response is unmarshalled to the req, which must be a pointer
// to a struct.
func (cl *Client) PostJSON(ctx context.Context, path string, req PostRequest) (*http.Response, error) {
	if !req.IsTokenSet() {
		req.SetToken(cl.token)
	}
	data, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	tape := cl.recorder(bytes.NewReader(data))
	defer cl.record([]byte("\n\n"))
	r, err := http.NewRequestWithContext(ctx, http.MethodPost, cl.edgeAPI+path, tape)
	if err != nil {
		return nil, err
	}
	r.Header.Set(hdrContentType, "application/json")

	return do(ctx, cl.cl, r)
}

// callEdgeAPI calls the edge API.
func (cl *Client) callEdgeAPI(ctx context.Context, v any, endpoint string, req PostRequest) error {
	r, err := cl.PostJSON(ctx, endpoint, req)
	if err != nil && !errors.Is(err, io.EOF) {
		return err
	}
	return cl.ParseResponse(v, r)
}

// PostForm sends a POST request to a webclient API, it marshals the form
// values to url.Values, omitting empty fields, and sends the request.
func (cl *Client) Post(ctx context.Context, path string, a any) (*http.Response, error) {
	return cl.PostFormRaw(ctx, cl.webclientAPI+path, values(a, true))
}

// PostForm sends a POST request to a webclient API with form values.
func (cl *Client) PostForm(ctx context.Context, path string, form url.Values) (*http.Response, error) {
	return cl.PostFormRaw(ctx, cl.webclientAPI+path, form)
}

func (cl *Client) record(b []byte) {
	if cl.tape != nil {
		if _, err := cl.tape.Write(b); err != nil {
			slog.Default().Error("error writing to tape", "error", err)
		}
	}
}

func (cl *Client) PostFormRaw(ctx context.Context, url string, form url.Values) (*http.Response, error) {
	if form["token"] == nil {
		form.Set("token", cl.token)
	}
	r := cl.recorder(strings.NewReader(form.Encode()))
	defer cl.record([]byte("\n\n"))
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, r)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	return do(ctx, cl.cl, req)
}

func (cl *Client) ParseResponse(req any, r *http.Response) error {
	if r.StatusCode < http.StatusOK || http.StatusMultipleChoices <= r.StatusCode {
		return fmt.Errorf("error: status code: %s", r.Status)
	}
	defer r.Body.Close()
	bodyBytes, err := io.ReadAll(cl.recorder(r.Body))
	if err != nil {
		return err
	}
	if err := json.Unmarshal(bodyBytes, req); err != nil {
		return err
	}
	return nil
}

// do is a helper function to do the request and handle rate limiting.  it
// tries to handle the rate limiting by waiting for the Retry-After only once,
// if it receives another rate limit error, it returns slack.RateLimitedError
// to let the caller handle it.
func do(ctx context.Context, cl httpClient, req *http.Request) (*http.Response, error) {
	ctx, task := trace.NewTask(ctx, "edge.do")
	defer task.End()

	lg := slog.Default()
	req.Header.Set("Accept-Language", "en-NZ,en-AU;q=0.9,en;q=0.8")
	req.Header.Set("User-Agent", slackauth.DefaultUserAgent)

	rgn := trace.StartRegion(ctx, "http.Do")
	resp, err := cl.Do(req)
	rgn.End()
	if err != nil {
		return nil, err
	}
	if resp.StatusCode == http.StatusTooManyRequests {
		wait, err := parseRetryAfter(resp)
		if err != nil {
			return nil, err
		}
		lg.InfoContext(ctx, "got rate limited, waiting", "delay", wait)

		time.Sleep(wait)
		resp, err = cl.Do(req)
		if err != nil {
			return nil, err
		}
		// if we are still rate limited, then we are in trouble
		if resp.StatusCode == http.StatusTooManyRequests {
			lg.DebugContext(ctx, "edge.do: did my best, but still rate limited, giving up, not my problem")
			wait, err = parseRetryAfter(resp)
			if err != nil {
				return nil, err
			}
			return nil, &slack.RateLimitedError{RetryAfter: wait}
		}
	}
	if resp.StatusCode < http.StatusOK || http.StatusMultipleChoices <= resp.StatusCode {
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		return nil, slack.StatusCodeError{Code: resp.StatusCode, Status: string(body)}
	}
	return resp, err
}

func parseRetryAfter(resp *http.Response) (time.Duration, error) {
	strWait := resp.Header.Get("Retry-After")
	if strWait == "" {
		return 0, errors.New("got rate limited, but did not get a Retry-After header")
	}
	wait, err := time.ParseDuration(strWait + "s")
	if err != nil {
		return 0, err
	}
	return wait, nil
}

// values returns url.Values from a struct.  If omitempty is true, then the
// empty values are omitted for the fields that have the `omitempty` tag.
func values(s any, omitempty bool) url.Values {
	var v = make(url.Values)
	m := tagops.ToMap(s, "json", omitempty, true)
	for k, val := range m {
		v.Set(k, fmt.Sprint(val))
	}
	return v
}

func (cl *Client) webapiURL(endpoint string) string {
	return cl.webclientAPI + endpoint
}

type APIError struct {
	Err      string
	Metadata ResponseMetadata
	Endpoint string
}

func (e *APIError) Error() string {
	if len(e.Metadata.Messages) > 0 {
		return e.Err + ": " + e.Metadata.Messages[0]
	}
	return e.Err
}

type WebClientFields struct {
	XReason  string `json:"_x_reason,omitempty"`
	XMode    string `json:"_x_mode,omitempty"`
	XSonic   bool   `json:"_x_sonic"`
	XAppName string `json:"_x_app_name"`
}

func webclientReason(reason string) WebClientFields {
	return WebClientFields{
		XReason:  reason,
		XMode:    "online",
		XSonic:   true,
		XAppName: "client",
	}
}

func (cl *Client) recorder(r io.Reader) io.Reader {
	if cl.tape == nil {
		return r
	}
	return io.TeeReader(r, cl.tape)
}

// Pagination contains the pagination information.  It is truly fucked, Slack
// does not allow to seek past Page 100, when page > 100 requested, Slack
// returns the first page (Page=1).  Seems to be an internal limitation.  The
// workaround would be to use the Query parameter, to be more specific about
// the channel names, but to get all channels, this would require iterating
// through all 65536 runes of unicode give or take the special characters.
//
// For now, this doesn't work as a replacement for conversation.list (202403).
type Pagination struct {
	TotalCount int64  `json:"total_count"`
	Page       int    `json:"page"`
	PerPage    int    `json:"per_page"`
	PageCount  int    `json:"page_count"`
	First      int64  `json:"first"`
	Last       int64  `json:"last"`
	NextCursor string `json:"next_cursor,omitempty"`
}
