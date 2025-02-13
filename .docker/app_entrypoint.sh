#!/bin/sh

# Patch the built app to use the specified environment variables
# at runtime, then serve the app
#
# See https://stackoverflow.com/questions/53010064/pass-environment-variable-into-a-vue-app-at-runtime for inspiration.
#
set -e
ROOT_DIR=/app/dist

if [ -z "$VITE_APP_API_URL" ]; then
    echo "VITE_APP_API_URL is unset and we are in production mode. Exiting."
    echo ""
    echo "Found settings:"
    echo ""
    env
    echo ""
    exit 1
fi

# If the VITE_APP_GIT_VERSION has not been overridden, set it to the default
# from package.json; the real `.git` version, if available, should still
# take precedence.
if [ -z "$VITE_APP_GIT_VERSION" ]; then
    VITE_APP_GIT_VERSION="0.0.0-git"
fi

echo "Replacing env vars in Javascript files"
echo "Settings:"
echo ""
echo "  APP_VERSION: ${VITE_APP_GIT_VERSION}"
echo "  API_URL: ${VITE_APP_API_URL}"
echo "  LOGO_URL: ${VITE_APP_LOGO_URL}"
echo "  HOMEPAGE_URL: ${VITE_APP_HOMPAGE_URL}"
echo "  EDITABLE_INVENTORY: ${VITE_APP_EDITABLE_INVENTORY}"
echo "  WEBSITE_TITLE: ${VITE_APP_WEBSITE_TITLE}"
echo "  QR_CODE_RESOLVER_URL: ${VITE_APP_QR_CODE_RESOLVER_URL}"
echo "  AUTOMATICALLY_GENERATE_ID_DEFAULT: ${VITE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT}"
echo ""
echo "Patching..."

for file in $ROOT_DIR/assets/index*.js* $ROOT_DIR/*html; do
    echo "$file"
    sed -i "s|0.0.0-git|${VITE_APP_GIT_VERSION}|g" $file
    sed -i "s|magic-api-url|${VITE_APP_API_URL}|g" $file
    sed -i "s|magic-logo-url|${VITE_APP_LOGO_URL}|g" $file
    sed -i "s|magic-homepage-url|${VITE_APP_HOMEPAGE_URL}|g" $file
    sed -i "s|magic-setting|${VITE_APP_EDITABLE_INVENTORY}|g" $file
    sed -i "s|magic-title|${VITE_APP_WEBSITE_TITLE}|g" $file
    sed -i "s|magic-qr-code-resolver-url|${VITE_APP_QR_CODE_RESOLVER_URL}|g" $file
    sed -i "s|magic-generate-id-setting|${VITE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT}|g" $file
    done

echo "Done!"

serve -s ${ROOT_DIR} -p 8081
