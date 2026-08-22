#!/usr/bin/env bash
#
# Build the site and publish it to the access-controlled review host, so
# collaborators can read it before anything is public.
#
#   tools/deploy_review.sh              # build, check, upload
#   tools/deploy_review.sh -n           # build and check only, no upload
#   tools/deploy_review.sh -h           # options
#
# The site goes to Cloudflare Pages as a *preview* deployment, at
#
#     https://<branch>.<project>.pages.dev
#
# and Cloudflare Access sits in front of it: a reader has to be on an email
# allowlist and confirm a one-time code before Cloudflare serves them a single
# byte. That is real authentication at the edge, not a JavaScript password
# prompt -- which would be worthless here, since a static site has already
# shipped its prose to the browser by the time any prompt could appear.
#
# Preview rather than production because Cloudflare's one-click Access toggle in
# the Pages dashboard covers preview deployments on *.pages.dev; protecting the
# production hostname means attaching a custom domain first. Nothing here needs
# a domain, which is the point -- glow-erc.org stays unspent while the naming
# question is open.
#
# This uploads the BUILT SITE only -- no source, no git history, no CI. The
# repository does have a remote now (glow-astro/website, private), but it is a
# backup and nothing here depends on it: the review host is fed from the local
# build, so a deploy never needs a push first, and never sees the ODT review
# documents or anything else outside the build directory.
#
# See §11 of docs/SITE_CONVENTIONS.md for the one-time setup.

if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Both overridable from the environment, because the project name is only fixed
# once someone creates it -- *.pages.dev is a single global namespace, so the
# obvious name may be taken. Whatever is chosen, set it here and it will match.
PROJECT="${GLOW_PAGES_PROJECT:-glow-erc-review}"
BRANCH="${GLOW_REVIEW_BRANCH:-review}"

# Cloudflare's one-click Access toggle covers PREVIEW deployments -- every
# *.<project>.pages.dev host. It does not cover the production hostname,
# <project>.pages.dev, which is a separate origin with no policy on it.
# Deploying to the production branch would therefore publish the site.
case "$BRANCH" in
  main|master|production|prod)
    echo "deploy_review: '$BRANCH' is a production branch name." >&2
    echo "  A production deployment lands on ${PROJECT}.pages.dev, which the" >&2
    echo "  preview Access policy does NOT protect -- the site would be public." >&2
    echo "  Use a preview branch (the default is 'review')." >&2
    exit 1 ;;
esac

BUILD_DIR="$ROOT/_review_site"
URL="https://${BRANCH}.${PROJECT}.pages.dev"
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage: tools/deploy_review.sh [options]

  -n, --dry-run        build and run the checks, but do not upload
  -h, --help           this message

Environment:
  GLOW_PAGES_PROJECT   Cloudflare Pages project name (default: glow-erc-review)
  GLOW_REVIEW_BRANCH   preview branch name        (default: review)
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    -n|--dry-run) DRY_RUN=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    *)            echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

die() { echo "deploy_review: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
# A separate directory from _site on purpose. The review build carries a
# different `url:` and a Disallow-everything robots.txt, and leaving that
# sitting in _site is how someone eventually publishes it.
echo "==> building review site"
rm -rf "$BUILD_DIR"
SITE_URL="$URL" ruby "$ROOT/tools/jekyll_build.rb" \
  "$ROOT" "$BUILD_DIR" _config.review.yml

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
# Each of these has a specific failure in mind. They cost a second and they run
# before anything leaves the machine.
echo "==> checking the build"

[ -f "$BUILD_DIR/index.html" ] || die "no index.html -- the build produced nothing"

# The production domain must not appear anywhere. If SITE_URL failed to take,
# every canonical link, the OpenGraph image and the JSON-LD would advertise
# glow-erc.org -- seeding the wrong canonical for a site that is not there yet,
# and handing anyone who copies a link an address that will not resolve.
if grep -rl "glow-erc\.org" "$BUILD_DIR" >/dev/null 2>&1; then
  echo "   files mentioning the production domain:" >&2
  grep -rl "glow-erc\.org" "$BUILD_DIR" | sed 's/^/     /' >&2
  die "production domain leaked into the review build"
fi

# ... and the review address must actually be in there, which is the same check
# from the other side: a typo'd SITE_URL would pass the test above by accident.
grep -q "$URL" "$BUILD_DIR/index.html" \
  || die "review URL $URL not found in index.html"

# Belt and braces for the window before Access is switched on.
grep -q "^Disallow: /$" "$BUILD_DIR/robots.txt" \
  || die "robots.txt does not disallow crawling -- is _config.review.yml applied?"

# The review ODTs are the whole site's prose in one file, with open questions
# and tracked changes in it. _config.yml excludes them; verify rather than trust.
if find "$BUILD_DIR" \( -name 'glow-site-text*' -o -name '*.odt' \) -print -quit | grep -q .; then
  die "a review document reached the build directory"
fi

PAGES="$(find "$BUILD_DIR" -name '*.html' | wc -l)"
echo "   ok -- $PAGES html files, url $URL, crawling disallowed"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "==> dry run, not uploading. Built site is in $BUILD_DIR"
  exit 0
fi

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
# Pinned, not @latest: wrangler 4.87.0 raised its floor to Node 22 and this
# machine has Node 20.20.2, so `wrangler@latest` aborts before it does anything
# -- including before `login` can open a browser, which looks exactly like the
# browser failing to open. 4.86.0 is the last release that accepts Node 20, and
# it accepts Node 22 too, so the pin is safe to keep after an upgrade; drop it
# once `node --version` is 22 or later and you want the newer releases.
WRANGLER_VERSION="4.86.0"

if command -v wrangler >/dev/null 2>&1; then
  WRANGLER=(wrangler)
elif command -v npx >/dev/null 2>&1; then
  # No global install needed; npx fetches it into its own cache.
  WRANGLER=(npx --yes "wrangler@${WRANGLER_VERSION}")
else
  die "neither wrangler nor npx found. Install Node, or see §11 of docs/SITE_CONVENTIONS.md"
fi

# Cloudflare credentials live in ~/.config/.wrangler, written by `wrangler login`.
if [ ! -d "$HOME/.config/.wrangler" ] && [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  die "not logged in to Cloudflare. Run:
    npx --yes wrangler@${WRANGLER_VERSION} login"
fi

echo "==> uploading to Cloudflare Pages project '$PROJECT', branch '$BRANCH'"
# --commit-dirty because this repo's working tree is often mid-edit and the
# warning is noise: what is uploaded is $BUILD_DIR, not the checkout.
"${WRANGLER[@]}" pages deploy "$BUILD_DIR" \
  --project-name "$PROJECT" \
  --branch "$BRANCH" \
  --commit-dirty=true

# Verify rather than assume. This is the only check that tests the thing that
# actually matters -- that a signed-out stranger cannot read the site -- and it
# tests it from outside, against the live URL, rather than inferring it from a
# dashboard setting. An unauthenticated request must be bounced to the Access
# login; a 200 means the prose is being served to anyone who has the link.
echo "==> checking that Access is in front of it"
sleep 2
redirect="$(curl -s -o /dev/null -w '%{redirect_url}' "$URL/")"
status="$(curl -s -o /dev/null -w '%{http_code}' "$URL/")"

case "$redirect" in
  *cloudflareaccess.com*)
    echo "   ok -- signed-out requests are sent to the Access login" ;;
  *)
    cat >&2 <<WARN

   ############################################################
   #  WARNING: THE REVIEW SITE IS PUBLIC                      #
   ############################################################

   $URL/ answered HTTP $status without an Access challenge.
   Anyone with the link can read the whole site right now.

   Turn Access on:
     dashboard -> Workers & Pages -> $PROJECT
       -> Settings -> General -> Access policy -> Enable

   Or roll it back immediately:
     npx --yes wrangler@${WRANGLER_VERSION} pages deployment list \\
       --project-name $PROJECT

WARN
    exit 1 ;;
esac

# The check above proves a stranger is locked out. It cannot prove the right
# people are let IN -- that is the policy's email list, and it is only visible
# to a token with Zero Trust scope, which the wrangler OAuth token is not.
cat <<EOF

==> done. The site is at
      $URL

    Collaborators must be on the Access policy by email:
      Zero Trust -> Access -> Applications -> the $PROJECT preview app
    Someone not on that list gets refused, not a login they can complete.
EOF
