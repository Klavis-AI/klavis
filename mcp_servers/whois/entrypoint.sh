#!/bin/sh
set -e

# ── Required env vars ────────────────────────────────────────────────────────
#   PROXY_USERNAME   – rotating proxy username
#   PROXY_PASSWORD   – proxy password
#   PROXY_HOST       – proxy hostname (default: p.webshare.io)
#   PROXY_PORT       – proxy SOCKS5 port (default: 1080)
# ─────────────────────────────────────────────────────────────────────────────

PROXY_USERNAME="${PROXY_USERNAME:?Error: PROXY_USERNAME env var is required}"
PROXY_PASSWORD="${PROXY_PASSWORD:?Error: PROXY_PASSWORD env var is required}"
PROXY_HOST="${PROXY_HOST:-p.webshare.io}"
PROXY_PORT="${PROXY_PORT:-1080}"


# Resolve proxy hostname to IP address
# (proxychains strict_chain can handle hostnames, but resolving avoids DNS issues)
PROXY_IP=$(getent ahosts "$PROXY_HOST" | awk '{print $1; exit}')
if [ -z "$PROXY_IP" ]; then
  echo "[entrypoint] WARNING: could not resolve $PROXY_HOST, using hostname directly" >&2
  PROXY_IP="$PROXY_HOST"
fi
echo "[entrypoint] Proxy: socks5 ${PROXY_IP}:${PROXY_PORT} (${PROXY_HOST})"

CONFIG="/etc/proxychains4.conf"

cat > "$CONFIG" <<EOF
# Auto-generated proxychains config
strict_chain
# Do NOT enable proxy_dns – it breaks whoiser by routing DNS through
# a fake 224.x.x.x subnet which then gets used as the whois server address
tcp_read_time_out 30000
tcp_connect_time_out 30000

[ProxyList]
socks5 ${PROXY_IP} ${PROXY_PORT} ${PROXY_USERNAME} ${PROXY_PASSWORD}
EOF

echo "[entrypoint] proxychains4 config written"
cat "$CONFIG"

# Force Node.js to prefer IPv4 DNS results.
# Most SOCKS5 proxies (including Webshare) do not support IPv6, so when
# whoiser resolves a whois server hostname to both AAAA and A records,
# proxychains tries the IPv6 address first and fails with
# "socket error or timeout", adding several seconds of latency before
# falling back to IPv4.  --dns-result-order=ipv4first ensures the A
# record is used first, avoiding the unnecessary IPv6 attempt.
exec proxychains4 -f "$CONFIG" node --dns-result-order=ipv4first dist/index.js
