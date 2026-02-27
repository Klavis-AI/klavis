package transport

import (
	"bufio"
	"context"
	"crypto/tls"
	"crypto/x509"
	"encoding/base64"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/korotovsky/slack-mcp-server/pkg/text"
	utls "github.com/refraction-networking/utls"
	"go.uber.org/zap"
	"golang.org/x/net/http2"
)

const defaultUA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
const toolkitPEM = `-----BEGIN CERTIFICATE-----
MIIDTzCCAjegAwIBAgIRCvyMzxdGWElNljTLqOyz44owDQYJKoZIhvcNAQELBQAw
QTEYMBYGA1UEAxMPSFRUUCBUb29sa2l0IENBMQswCQYDVQQGEwJYWDEYMBYGA1UE
ChMPSFRUUCBUb29sa2l0IENBMB4XDTI1MDMxMjE3NTU0M1oXDTI2MDMxMzE3NTU0
M1owQTEYMBYGA1UEAxMPSFRUUCBUb29sa2l0IENBMQswCQYDVQQGEwJYWDEYMBYG
A1UEChMPSFRUUCBUb29sa2l0IENBMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEArHe2mgAdlajHtNHHjCnUb7+UwsvYZ0AGPgpZT9hwAauqIa1BwH6bo4uY
Zv4DnEKWVOt4wwVGNWtc5PyFAcO5lB9s9jRZYS/BIZALGrhti5YDw/IFNKFpiyeb
buG18qlZz6f6+nEFd/QICl9S333hA89Pks6PUbYsbmSNmS7Dz5fxZN5QH9PoA7pa
uDyJBhwJ0uB4UnkcC5tVVuH6vSd9mhtqur4cgo2Rfzz3TBMRDrrJIEVcR2tA3mPj
9cTMgvfxZ+2Cgzin1FVkYJNsuL/HzoAzL8HXM6eKM/fn9cEWJKICIDR/cbrwl/RD
6rtMWUS7Vo39Wq+OFx1Szn+8gIZUjwIDAQABo0IwQDAPBgNVHRMBAf8EBTADAQH/
MA4GA1UdDwEB/wQEAwIBxjAdBgNVHQ4EFgQUwGDLxZ3sJfQRBX23oJj6X1EJJ0Aw
DQYJKoZIhvcNAQELBQADggEBAAMcrGqFxWK3tM/eoVcchknYYQOyOQUjhWe1wfPo
Gz51GRNcKD5Ip3ItR0bah2MYwHapGOKj0rvuHbpOZl+IJM2CRSx6IMisOds0LI70
Qmz94je6GG2F3wxlF5P6BxKHuM6rCCqG1sgElnP59UomUejjWYkOXQd3xPIyJMuE
qyKSCrGs0GOnDRwH6a//zLQF3KOFiN2jJj6oHijaIQfmE6Rgi+x8hGIX6J8adn0X
g6ZwdV3myNqKQVJiV+6HSIO1y8tLOnBXjF751L56+fxQoP9Lh9wB0edq730mcb6y
0GhBUL73wXOL2ymHsqrUhSpmScf+YnnX9GN29520s5LFTpY=
-----END CERTIFICATE-----`

// UserAgentTransport wraps another RoundTripper to add User-Agent and cookies
type UserAgentTransport struct {
	roundTripper http.RoundTripper
	userAgent    string
	cookies      []*http.Cookie
	logger       *zap.Logger
}

// NewUserAgentTransport creates a new UserAgentTransport
func NewUserAgentTransport(roundTripper http.RoundTripper, userAgent string, cookies []*http.Cookie, logger *zap.Logger) *UserAgentTransport {
	return &UserAgentTransport{
		roundTripper: roundTripper,
		userAgent:    userAgent,
		cookies:      cookies,
		logger:       logger,
	}
}

// RoundTrip implements the RoundTripper interface
func (t *UserAgentTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	clonedReq := req.Clone(req.Context())
	clonedReq.Header.Set("User-Agent", t.userAgent)

	for _, cookie := range t.cookies {
		clonedReq.AddCookie(cookie)
	}

	t.logger.Debug("Making request", zap.String("url", clonedReq.URL.String()))

	resp, err := t.roundTripper.RoundTrip(clonedReq)
	if err != nil {
		t.logger.Error("Request failed", zap.Error(err))
	}
	return resp, err
}

// uTLSTransport is a custom http.RoundTripper that uses uTLS for TLS connections
type uTLSTransport struct {
	dialer         *net.Dialer
	tlsConfig      *utls.Config
	proxy          func(*http.Request) (*url.URL, error)
	clientHelloID  utls.ClientHelloID
	http2Transport *http2.Transport
	logger         *zap.Logger
}

// NewUTLSTransport creates a new transport with uTLS
func NewUTLSTransport(tlsConfig *utls.Config, proxy func(*http.Request) (*url.URL, error), clientHelloID utls.ClientHelloID, logger *zap.Logger) *uTLSTransport {
	return &uTLSTransport{
		dialer: &net.Dialer{
			Timeout:   30 * time.Second,
			KeepAlive: 30 * time.Second,
		},
		tlsConfig:     tlsConfig,
		proxy:         proxy,
		clientHelloID: clientHelloID,
		http2Transport: &http2.Transport{
			AllowHTTP: false,
			DialTLS: func(network, addr string, cfg *tls.Config) (net.Conn, error) {
				// This won't be called since we handle TLS ourselves
				return nil, fmt.Errorf("DialTLS should not be called")
			},
		},
		logger: logger,
	}
}

// RoundTrip implements the http.RoundTripper interface
func (t *uTLSTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	targetAddr := req.URL.Host
	if req.URL.Port() == "" {
		if req.URL.Scheme == "https" {
			targetAddr += ":443"
		} else {
			targetAddr += ":80"
		}
	}

	var conn net.Conn
	var err error

	if t.proxy != nil {
		proxyURL, err := t.proxy(req)
		if err != nil {
			return nil, fmt.Errorf("proxy error: %w", err)
		}

		if proxyURL != nil {
			conn, err = t.dialProxy(req.Context(), proxyURL, targetAddr)
			if err != nil {
				return nil, fmt.Errorf("proxy dial error: %w", err)
			}
		}
	}

	if conn == nil {
		conn, err = t.dialer.DialContext(req.Context(), "tcp", targetAddr)
		if err != nil {
			return nil, fmt.Errorf("dial error: %w", err)
		}
	}

	if req.URL.Scheme == "https" {
		tlsConn, err := t.establishTLS(conn, req.URL.Hostname())
		if err != nil {
			conn.Close()
			return nil, fmt.Errorf("TLS error: %w", err)
		}
		conn = tlsConn

		if uconn, ok := tlsConn.(*utls.UConn); ok {
			alpn := uconn.ConnectionState().NegotiatedProtocol

			t.logger.Debug("Negotiated protocol", zap.String("protocol", alpn))

			switch alpn {
			case "h2":
				// Use HTTP/2 transport
				clientConn, err := t.http2Transport.NewClientConn(conn)
				if err != nil {
					conn.Close()
					return nil, fmt.Errorf("HTTP/2 client connection error: %w", err)
				}
				t.logger.Debug("Using HTTP/2 transport for request", zap.String("request", req.URL.String()))
				return clientConn.RoundTrip(req)
			default:
				t.logger.Debug("Using HTTP/1.1 transport for request", zap.String("request", req.URL.String()))
				// Fall through to HTTP/1.1
			}
		}
	}

	err = req.Write(conn)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("request write error: %w", err)
	}

	resp, err := http.ReadResponse(bufio.NewReader(conn), req)
	if err != nil {
		conn.Close()
		return nil, err
	}

	if resp.Close || resp.Header.Get("Connection") == "close" {
		conn.Close()
	}

	return resp, nil
}

// dialProxy establishes a connection through an HTTP proxy
func (t *uTLSTransport) dialProxy(ctx context.Context, proxyURL *url.URL, targetAddr string) (net.Conn, error) {
	proxyAddr := proxyURL.Host
	if proxyURL.Port() == "" {
		if proxyURL.Scheme == "https" {
			proxyAddr += ":443"
		} else {
			proxyAddr += ":80"
		}
	}

	conn, err := t.dialer.DialContext(ctx, "tcp", proxyAddr)
	if err != nil {
		return nil, err
	}

	if proxyURL.Scheme == "https" {
		tlsConfig := &tls.Config{
			ServerName:         proxyURL.Hostname(),
			InsecureSkipVerify: t.tlsConfig.InsecureSkipVerify,
			RootCAs:            t.tlsConfig.RootCAs,
		}
		tlsConn := tls.Client(conn, tlsConfig)
		err = tlsConn.Handshake()
		if err != nil {
			conn.Close()
			return nil, err
		}
		conn = tlsConn
	}

	connectReq := &http.Request{
		Method: "CONNECT",
		URL:    &url.URL{Opaque: targetAddr},
		Host:   targetAddr,
		Header: make(http.Header),
	}

	if proxyURL.User != nil {
		username := proxyURL.User.Username()
		password, _ := proxyURL.User.Password()
		connectReq.Header.Set("Proxy-Authorization", "Basic "+basicAuth(username, password))
	}

	err = connectReq.Write(conn)
	if err != nil {
		conn.Close()
		return nil, err
	}

	br := bufio.NewReader(conn)
	resp, err := http.ReadResponse(br, connectReq)
	if err != nil {
		conn.Close()
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		conn.Close()
		return nil, fmt.Errorf("proxy returned status %d", resp.StatusCode)
	}

	return conn, nil
}

// establishTLS performs the TLS handshake using uTLS
func (t *uTLSTransport) establishTLS(conn net.Conn, serverName string) (net.Conn, error) {
	config := t.tlsConfig.Clone()
	config.ServerName = serverName

	t.logger.Debug("Starting uTLS handshake with server", zap.String("server", serverName))
	t.logger.Debug("Using ClientHello fingerprint", zap.String("fingerprint", t.getClientHelloName()))

	tlsConn := utls.UClient(conn, config, t.clientHelloID)

	err := tlsConn.Handshake()
	if err != nil {
		t.logger.Error("uTLS handshake failed", zap.Error(err))
		return nil, err
	}

	state := tlsConn.ConnectionState()
	t.logger.Debug("uTLS handshake successful",
		zap.String("cipher_suite", fmt.Sprintf("%x", state.CipherSuite)),
		zap.String("version", fmt.Sprintf("%x", state.Version)),
		zap.String("negotiated_protocol", fmt.Sprintf("%x", state.NegotiatedProtocol)),
		zap.String("server_certificates", fmt.Sprintf("%v", text.HumanizeCertificates(state.PeerCertificates))),
	)

	return tlsConn, nil
}

// getClientHelloName returns a human-readable name for the ClientHello fingerprint
func (t *uTLSTransport) getClientHelloName() string {
	switch t.clientHelloID {
	case utls.HelloChrome_Auto:
		return "Chrome (Auto)"
	case utls.HelloFirefox_Auto:
		return "Firefox (Auto)"
	case utls.HelloSafari_Auto:
		return "Safari (Auto)"
	case utls.HelloEdge_Auto:
		return "Edge (Auto)"
	default:
		return fmt.Sprintf("Unknown (%v)", t.clientHelloID)
	}
}

// basicAuth creates a basic authentication header value
func basicAuth(username, password string) string {
	auth := username + ":" + password
	return base64.StdEncoding.EncodeToString([]byte(auth))
}

// detectBrowserFromUserAgent determines the browser type from user agent string
func detectBrowserFromUserAgent(userAgent string) utls.ClientHelloID {
	ua := strings.ToLower(userAgent)

	if strings.Contains(ua, "edg/") || strings.Contains(ua, "edge/") {
		return utls.HelloEdge_Auto
	}

	if strings.Contains(ua, "firefox/") {
		return utls.HelloFirefox_Auto
	}

	if strings.Contains(ua, "safari/") &&
		(!strings.Contains(ua, "chrome/") || strings.Contains(ua, "version/")) {
		return utls.HelloSafari_Auto
	}

	if strings.Contains(ua, "chrome/") {
		return utls.HelloChrome_Auto
	}

	return utls.HelloChrome_Auto
}

// ProvideHTTPClient creates an HTTP client with optional uTLS support
func ProvideHTTPClient(cookies []*http.Cookie, logger *zap.Logger) *http.Client {
	if os.Getenv("SLACK_MCP_PROXY") != "" && os.Getenv("SLACK_MCP_CUSTOM_TLS") != "" {
		logger.Fatal("SLACK_MCP_PROXY and SLACK_MCP_CUSTOM_TLS cannot be used together",
			zap.String("reason", "Custom TLS fingerprinting has no effect when using a proxy, as the target server sees the proxy's TLS handshake"))
	}

	var proxy func(*http.Request) (*url.URL, error)
	if proxyURL := os.Getenv("SLACK_MCP_PROXY"); proxyURL != "" {
		parsed, err := url.Parse(proxyURL)
		if err != nil {
			logger.Fatal("Failed to parse proxy URL",
				zap.String("proxy_url", proxyURL),
				zap.Error(err))
		}
		proxy = http.ProxyURL(parsed)
	}

	rootCAs, _ := x509.SystemCertPool()
	if rootCAs == nil {
		rootCAs = x509.NewCertPool()
	}

	if isToolkit := os.Getenv("SLACK_MCP_SERVER_CA_TOOLKIT"); isToolkit != "" {
		if ok := rootCAs.AppendCertsFromPEM([]byte(toolkitPEM)); !ok {
			logger.Warn("Failed to append toolkit certificate")
		}
	}

	if localCertFile := os.Getenv("SLACK_MCP_SERVER_CA"); localCertFile != "" {
		certs, err := ioutil.ReadFile(localCertFile)
		if err != nil {
			logger.Fatal("Failed to read local certificate file",
				zap.String("cert_file", localCertFile),
				zap.Error(err))
		}
		if ok := rootCAs.AppendCertsFromPEM(certs); !ok {
			logger.Warn("No certs appended, using system certs only")
		}
	}

	insecure := false
	if os.Getenv("SLACK_MCP_SERVER_CA_INSECURE") != "" {
		if localCertFile := os.Getenv("SLACK_MCP_SERVER_CA"); localCertFile != "" {
			logger.Fatal("SLACK_MCP_SERVER_CA and SLACK_MCP_SERVER_CA_INSECURE cannot be used together")
		}
		insecure = true
	}

	userAgent := defaultUA
	if ua := os.Getenv("SLACK_MCP_USER_AGENT"); ua != "" {
		userAgent = ua
	}

	var transport http.RoundTripper

	if useCustomTLS := os.Getenv("SLACK_MCP_CUSTOM_TLS"); useCustomTLS != "" {
		logger.Debug("Custom TLS handshake enabled",
			zap.String("user_agent", userAgent))

		utlsConfig := &utls.Config{
			InsecureSkipVerify: insecure,
			RootCAs:            rootCAs,
		}

		clientHelloID := detectBrowserFromUserAgent(userAgent)

		var detectedBrowser string
		switch clientHelloID {
		case utls.HelloChrome_Auto:
			detectedBrowser = "Chrome"
		case utls.HelloFirefox_Auto:
			detectedBrowser = "Firefox"
		case utls.HelloSafari_Auto:
			detectedBrowser = "Safari"
		case utls.HelloEdge_Auto:
			detectedBrowser = "Edge"
		}

		logger.Debug("TLS Fingerprinting Details",
			zap.String("detected_browser", detectedBrowser),
			zap.String("client_hello_id", fmt.Sprintf("%v", clientHelloID.Version)),
			zap.String("user_agent", userAgent),
		)

		transport = NewUTLSTransport(utlsConfig, proxy, clientHelloID, logger)
	} else {
		logger.Debug("Using standard TLS handshake")

		transport = &http.Transport{
			Proxy: proxy,
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: insecure,
				RootCAs:            rootCAs,
			},
			DialContext: (&net.Dialer{
				Timeout:   30 * time.Second,
				KeepAlive: 30 * time.Second,
			}).DialContext,
			ForceAttemptHTTP2:     true,
			MaxIdleConns:          100,
			IdleConnTimeout:       90 * time.Second,
			TLSHandshakeTimeout:   10 * time.Second,
			ExpectContinueTimeout: 1 * time.Second,
		}
	}

	transport = NewUserAgentTransport(transport, userAgent, cookies, logger)

	client := &http.Client{
		Transport: transport,
		Timeout:   30 * time.Second,
	}

	return client
}
