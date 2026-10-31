#!/bin/sh

# Write the runtime configuration of the built app from the specified environment
# variables. Run by the nginx image's entrypoint (from `/docker-entrypoint.d/`)
# before nginx starts; a non-zero exit stops the container from starting.
#
# Everything written here is served publicly, so only the settings defined in
# `webapp/src/config.schema.json` are passed through; it must never contain secrets.
#
set -e
ROOT_DIR=/app/dist

SCHEMA=/app/config.schema.json

# Refuse to start with settings that do not match the schema; empty values count as unset.
errors=$(jq -r '
    .required as $required
    | .properties | to_entries[]
    | .key as $name | .value as $setting
    | (env["VUE_APP_" + $name] // "") as $value
    | if $value == "" then
        if ($required | index($name)) then "VUE_APP_\($name) must be set: \($setting.description)" else empty end
      elif ($setting.pattern and ($value | test($setting.pattern) | not)) then
        "Invalid value \"\($value)\" for VUE_APP_\($name): \($setting.description)"
      else empty end
' "$SCHEMA")
if [ -n "$errors" ]; then
    echo "Invalid web app settings, see $SCHEMA. Exiting." >&2
    echo "$errors" >&2
    exit 1
fi

# Settings that are not in the schema are not passed on to the app, so may be typos.
jq -r '
    .properties as $settings
    | env | keys[]
    | select(startswith("VUE_APP_") and (ltrimstr("VUE_APP_") as $name | $settings | has($name) | not))
    | "WARNING: ignoring unknown setting \(.)"
' "$SCHEMA"

jq -r '
    .properties | keys
    | map({key: ., value: (env["VUE_APP_" + .] // "")} | select(.value != ""))
    | from_entries
    | "window.__DATALAB_CONFIG__ = \(tojson);"
' "$SCHEMA" > "$ROOT_DIR/config.js"

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
