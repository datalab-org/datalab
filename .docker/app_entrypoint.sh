#!/bin/sh
# This file was edited with the assistance of an AI model and requires human review from the contributor.

# Write the runtime configuration of the built app from the specified environment
# variables. Run by the nginx image's entrypoint (from `/docker-entrypoint.d/`)
# before nginx starts; a non-zero exit stops the container from starting.
#
# Everything written here is served publicly, so only the settings listed below are
# passed through to the app; secrets must never be added to this list.
#
set -e
ROOT_DIR=/app/dist

if [ -z "$VUE_APP_API_URL" ]; then
    echo "VUE_APP_API_URL is unset and we are in production mode. Exiting."
    echo ""
    echo "Found settings:"
    echo ""
    env
    echo ""
    exit 1
fi

# Unset or empty settings are omitted, so that the defaults in the webapp apply.
jq -nr '[
    "API_URL",
    "GIT_VERSION",
    "LOGO_URL",
    "LOGO_WIDTH",
    "HOMEPAGE_URL",
    "EDITABLE_INVENTORY",
    "WEBSITE_TITLE",
    "QR_CODE_RESOLVER_URL",
    "AUTOMATICALLY_GENERATE_ID_DEFAULT",
    "UPPY_MAX_TOTAL_FILE_SIZE",
    "UPPY_MAX_NUMBER_OF_FILES"
] | map({key: ., value: (env["VUE_APP_" + .] // "")} | select(.value != ""))
  | from_entries
  | "window.__DATALAB_CONFIG__ = \(tojson);"' > "$ROOT_DIR/config.js"

echo "Wrote $ROOT_DIR/config.js:"
cat "$ROOT_DIR/config.js"

# Escape characters that sed would otherwise interpret in the replacement
# (e.g., `&` in URL query strings).
escape() {
    printf '%s' "$1" | sed -e 's/[\\&#]/\\&/g'
}

# The API URL is also advertised in the HTML, where it is read by API clients
# such as datalab-api, and the title is shown before the app has loaded.
api_url=$(escape "$VUE_APP_API_URL")
sed -i -E "s#(<meta name=\"?x_datalab_api_url\"? content=)(\"[^\"]*\"|[^ >]*)#\1\"${api_url}\"#" "$ROOT_DIR/index.html"
if [ -n "$VUE_APP_WEBSITE_TITLE" ]; then
    title=$(escape "$VUE_APP_WEBSITE_TITLE")
    sed -i -E "s#<title>[^<]*</title>#<title>${title}</title>#" "$ROOT_DIR/index.html"
fi

echo "Done!"
