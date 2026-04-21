#!/usr/bin/env bash
# Track D smoke suite.
#
# Usage:
#   bash scripts/smoke.sh pre    # baseline, run on modernization or track-d
#                                # (after the scripts commit, before the
#                                # hygiene commit)
#   bash scripts/smoke.sh post   # run on track-d/python-hygiene after the
#                                # hygiene commit
#
# Writes filtered response bodies and status codes to /tmp/td-$arg/ so that
# `diff -r /tmp/td-pre /tmp/td-post` surfaces parity violations while
# ignoring timestamps, CSRF tokens, and session ids.
#
# Prereqs:
#   - tilt / portal is up and serving at http://localhost:8000
#   - A session cookie jar file exists at $AIRAVATA_SMOKE_COOKIE_JAR
#     (or the default /tmp/airavata-smoke-cookie-jar). Capture it by
#     logging in once through the browser + copying the session cookie,
#     or by scripting the Keycloak OIDC flow.
set -euo pipefail

ARG="${1:-}"
if [[ "$ARG" != "pre" && "$ARG" != "post" ]]; then
    echo "usage: $0 pre|post" >&2
    exit 2
fi

OUT="/tmp/td-$ARG"
rm -rf "$OUT"
mkdir -p "$OUT"

COOKIE_JAR="${AIRAVATA_SMOKE_COOKIE_JAR:-/tmp/airavata-smoke-cookie-jar}"
if [[ ! -f "$COOKIE_JAR" ]]; then
    echo "missing cookie jar at $COOKIE_JAR" >&2
    echo "log in as a test user via the browser and save the cookies" >&2
    echo "(for example, export with the EditThisCookie extension)" >&2
    exit 3
fi

BASE="http://localhost:8000"

# endpoint-slug <whitespace> path
ENDPOINTS=(
    "health               /health/"
    "api-projects         /api/projects/?limit=5"
    "api-applications     /api/applications/?limit=5"
    "api-experiments      /api/experiments/?limit=5"
    "api-user-profile     /api/user-profile/"
    "api-project-profiles /api/project-profiles/"
    "pages-home           /pages/home/"
    "workspace            /workspace/"
)

canon() {
    # Strip known-dynamic values so diff -r is meaningful.
    sed -E \
        -e 's/csrftoken=[A-Za-z0-9]+/csrftoken=X/g' \
        -e 's/<meta name="csrf-token" content="[^"]+"/<meta name="csrf-token" content="X"/g' \
        -e 's/<script nonce="[^"]+"/<script nonce="X"/g' \
        -e 's/"timestamp"[[:space:]]*:[[:space:]]*"[^"]*"/"timestamp":"X"/g' \
        -e 's/"createdAt"[[:space:]]*:[[:space:]]*"[^"]*"/"createdAt":"X"/g' \
        -e 's/"updatedAt"[[:space:]]*:[[:space:]]*"[^"]*"/"updatedAt":"X"/g' \
        -e 's/sessionid=[A-Za-z0-9]+/sessionid=X/g'
}

for row in "${ENDPOINTS[@]}"; do
    slug="${row%%[[:space:]]*}"
    path="${row#*[[:space:]]}"
    # Trim leading whitespace from path.
    path="${path#"${path%%[![:space:]]*}"}"
    url="$BASE$path"
    status="$(curl -sk -o "$OUT/$slug.raw" -w "%{http_code}" \
        -b "$COOKIE_JAR" -c "$COOKIE_JAR" "$url" || echo "000")"
    canon < "$OUT/$slug.raw" > "$OUT/$slug.body"
    echo "$status" > "$OUT/$slug.status"
    rm "$OUT/$slug.raw"
done

echo "wrote $OUT"
