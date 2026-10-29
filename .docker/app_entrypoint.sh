#!/bin/sh

# Patch the built app to use the specified environment variables
# at runtime, then serve the app
#
# See https://stackoverflow.com/questions/53010064/pass-environment-variable-into-a-vue-app-at-runtime for inspiration.
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

# If the VUE_APP_GIT_VERSION has not been overridden, set it to the default
# from package.json; the real `.git` version, if available, should still
# take precedence.
if [ -z "$VUE_APP_GIT_VERSION" ]; then
    VUE_APP_GIT_VERSION="0.0.0-git"
fi

# If VUE_APP_WEBSITE_TITLE is unset, default to "datalab" so the sed
# substitution below doesn't blank out the title in the built app.
if [ -z "$VUE_APP_WEBSITE_TITLE" ]; then
    VUE_APP_WEBSITE_TITLE="datalab"
fi

# If VUE_APP_LOGO_WIDTH is unset, use the same default as the webapp,
# as the placeholder in the built app would otherwise be blanked out.
if [ -z "$VUE_APP_LOGO_WIDTH" ]; then
    VUE_APP_LOGO_WIDTH="100"
fi

# Replace a placeholder in the current file, escaping characters that sed
# would otherwise interpret in the replacement (e.g., `&` in URL query strings).
replace() {
    escaped=$(printf '%s' "$2" | sed -e 's/[\\&|]/\\&/g')
    sed -i "s|$1|${escaped}|g" "$file"
}

echo "Replacing env vars in Javascript files"
echo "Settings:"
echo ""
echo "  APP_VERSION: ${VUE_APP_GIT_VERSION}"
echo "  API_URL: ${VUE_APP_API_URL}"
echo "  LOGO_URL: ${VUE_APP_LOGO_URL}"
echo "  LOGO_WIDTH: ${VUE_APP_LOGO_WIDTH}"
echo "  HOMEPAGE_URL: ${VUE_APP_HOMEPAGE_URL}"
echo "  EDITABLE_INVENTORY: ${VUE_APP_EDITABLE_INVENTORY}"
echo "  WEBSITE_TITLE: ${VUE_APP_WEBSITE_TITLE}"
echo "  QR_CODE_RESOLVER_URL: ${VUE_APP_QR_CODE_RESOLVER_URL}"
echo "  AUTOMATICALLY_GENERATE_ID_DEFAULT: ${VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT}"
echo ""
echo "Patching..."

for file in $ROOT_DIR/js/app.*.js* $ROOT_DIR/*html; do
    echo "$file"
    replace "0.0.0-git" "${VUE_APP_GIT_VERSION}"
    replace "magic-api-url" "${VUE_APP_API_URL}"
    replace "magic-logo-url" "${VUE_APP_LOGO_URL}"
    replace "magic-logo-width" "${VUE_APP_LOGO_WIDTH}"
    replace "magic-homepage-url" "${VUE_APP_HOMEPAGE_URL}"
    replace "magic-setting" "${VUE_APP_EDITABLE_INVENTORY}"
    replace "magic-title" "${VUE_APP_WEBSITE_TITLE}"
    replace "magic-qr-code-resolver-url" "${VUE_APP_QR_CODE_RESOLVER_URL}"
    replace "magic-generate-id-setting" "${VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT}"
    done

echo "Done!"

serve -s ${ROOT_DIR} -p 8081
