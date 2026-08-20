#!/usr/bin/env bash
#
# Build the site and open it in a browser.
#
#   tools/preview.sh                 # build, serve, open the home page
#   tools/preview.sh science.html    # ... open that page instead
#   tools/preview.sh -w              # rebuild whenever a source file changes
#   tools/preview.sh -h              # all the options
#
# Stop it with ctrl-C; the server is shut down with the script.
#
# Two things this does that `python3 -m http.server` does not:
#
#   * It sends `Cache-Control: no-store`. Chrome caching a stale image or
#     stylesheet has produced two false bug reports on this site already -- a
#     figure whose height was still the pre-edit value, and a CSS change that
#     appeared not to apply. With this you never need `ctrl+shift+r`.
#   * It refuses to serve a build that failed, so you are never reading a stale
#     page while believing it is the new one.
#
# Jekyll is invoked through tools/jekyll_build.rb rather than the `jekyll`
# binary, which works around RubyGems' recursive dependency activation on this
# machine. See the comment at the top of that file.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT=8811
PAGE=""
BUILD=1
OPEN=1
WATCH=0

usage() {
  cat <<'USAGE'
Usage: tools/preview.sh [options] [page]

  page                 page to open, e.g. science.html (default: the home page)

  -p, --port N         port to serve on (default: 8811)
  -w, --watch          rebuild when a source file changes, then keep serving
  -n, --no-build       serve _site as it stands, without rebuilding
  -B, --no-open        start the server but do not open a browser
  -h, --help           this message
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    -p|--port)     PORT="${2:?--port needs a number}"; shift 2 ;;
    -w|--watch)    WATCH=1; shift ;;
    -n|--no-build) BUILD=0; shift ;;
    -B|--no-open)  OPEN=0; shift ;;
    -h|--help)     usage; exit 0 ;;
    -*)            echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)             PAGE="${1#/}"; shift ;;
  esac
done

URL="http://127.0.0.1:${PORT}/${PAGE}"

build() {
  # Build into a scratch directory and swap it in, so a failed build leaves the
  # currently-served _site untouched rather than half-replaced.
  local tmp="${ROOT}/.preview-build"
  rm -rf "$tmp"
  if ! ruby "${ROOT}/tools/jekyll_build.rb" "$ROOT" "$tmp"; then
    echo "build failed -- keeping the previous _site" >&2
    rm -rf "$tmp"
    return 1
  fi
  rm -rf "${ROOT}/_site"
  mv "$tmp" "${ROOT}/_site"
}

# A fingerprint of every source file's modification time. Changes when anything
# is edited, added or deleted. Poll-based because neither inotifywait nor entr
# is installed here, and the tree is small enough that this costs nothing.
fingerprint() {
  find "$ROOT" \
       \( -name _site -o -name .git -o -name .jekyll-cache -o -name vendor \
          -o -name __pycache__ -o -name .preview-build \) -prune -o \
       -type f -printf '%T@ %p\n' 2>/dev/null | sort | cksum
}

# Is a preview server -- ours, not some other program -- already on this port?
ours_already_running() {
  curl -fsS -m 2 -o /dev/null -D - "http://127.0.0.1:${PORT}/" 2>/dev/null \
    | grep -qi '^x-glow-preview:'
}

port_is_taken() {
  curl -fsS -m 2 -o /dev/null "http://127.0.0.1:${PORT}/" 2>/dev/null
}

serve() {
  python3 - "$PORT" "${ROOT}/_site" <<'PY' &
import http.server, socketserver, sys

port, root = int(sys.argv[1]), sys.argv[2]

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=root, **kw)

    def end_headers(self):
        # The whole point of this server: never let the browser cache anything,
        # so what you reload is what was just built.
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-GLOW-Preview", "1")
        super().end_headers()

    def log_message(self, fmt, *args):
        # 404s are worth seeing; the successful requests are noise.
        if not str(args[1] if len(args) > 1 else "").startswith("2"):
            sys.stderr.write("  %s\n" % (fmt % args))

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
    httpd.serve_forever()
PY
  SERVER_PID=$!
}

cleanup() {
  if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "${ROOT}/.preview-build"
}
trap cleanup EXIT INT TERM

open_browser() {
  for opener in xdg-open sensible-browser google-chrome firefox; do
    if command -v "$opener" >/dev/null 2>&1; then
      "$opener" "$URL" >/dev/null 2>&1 &
      return
    fi
  done
  echo "no browser opener found -- open $URL yourself" >&2
}

# ---- go ----------------------------------------------------------------

[ "$BUILD" = 1 ] && build

REUSED=0
if ours_already_running; then
  REUSED=1
elif port_is_taken; then
  echo "port ${PORT} is in use by something that is not this script." >&2
  echo "Pick another with --port, or stop whatever is using it." >&2
  exit 1
else
  serve
  for _ in $(seq 40); do
    curl -fsS -m 1 -o /dev/null "http://127.0.0.1:${PORT}/" 2>/dev/null && break
    sleep 0.25
  done
  if ! curl -fsS -m 1 -o /dev/null "http://127.0.0.1:${PORT}/" 2>/dev/null; then
    echo "the server did not come up on port ${PORT}" >&2
    exit 1
  fi
fi

echo "serving ${ROOT}/_site at ${URL}"
[ "$OPEN" = 1 ] && open_browser

# Nothing to hold the terminal open for: the server belongs to an earlier
# invocation, and killing it here would pull the rug from under that one.
if [ "$REUSED" = 1 ] && [ "$WATCH" = 0 ]; then
  echo "(a preview server was already running on port ${PORT}; leaving it be)"
  exit 0
fi

if [ "$WATCH" = 1 ]; then
  echo "watching for changes -- ctrl-C to stop"
  last="$(fingerprint)"
  while true; do
    sleep 1
    now="$(fingerprint)"
    if [ "$now" != "$last" ]; then
      last="$now"
      echo "change detected, rebuilding..."
      build || true
      # Rebuilt in place, and nothing is cached, so just reload the tab.
      last="$(fingerprint)"
    fi
  done
else
  echo "ctrl-C to stop"
  wait "$SERVER_PID"
fi
