#!/bin/bash
set -euo pipefail

readonly PANEL_SOURCE="/opt/datalab-plugin-panels"
readonly PANEL_DESTINATION="/app/src/plugins"

mkdir -p "${PANEL_DESTINATION}"

# Everything beside the committed index.js loader is generated. Clear it so
# removing a plugin cannot leave a stale component in the bind-mounted source.
find "${PANEL_DESTINATION}" -mindepth 1 -maxdepth 1 ! -name index.js -exec rm -rf -- {} +

# Preserve the checkout's committed index.js rather than overwriting it with
# the copy captured when the image was built.
while IFS= read -r -d '' generated_path; do
  cp -a "${generated_path}" "${PANEL_DESTINATION}/"
done < <(find "${PANEL_SOURCE}" -mindepth 1 -maxdepth 1 ! -name index.js -print0)

exec /node_modules/.bin/vue-cli-service serve --host 0.0.0.0 --port 8081
