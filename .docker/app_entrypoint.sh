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

echo "Replacing env vars in Javascript files"
echo "Settings:"
echo ""
echo "  APP_VERSION: ${VUE_APP_GIT_VERSION}"
echo "  API_URL: ${VUE_APP_API_URL}"
echo "  LOGO_URL: ${VUE_APP_LOGO_URL}"
echo "  HOMEPAGE_URL: ${VUE_APP_HOMPAGE_URL}"
echo "  EDITABLE_INVENTORY: ${VUE_APP_EDITABLE_INVENTORY}"
echo "  WEBSITE_TITLE: ${VUE_APP_WEBSITE_TITLE}"
echo "  QR_CODE_RESOLVER_URL: ${VUE_APP_QR_CODE_RESOLVER_URL}"
echo "  AUTOMATICALLY_GENERATE_ID_DEFAULT: ${VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT}"
echo ""
echo "Patching..."

for file in $ROOT_DIR/js/app.*.js* $ROOT_DIR/*html; do
    echo "$file"
    sed -i "s|0.0.0-git|${VUE_APP_GIT_VERSION}|g" $file
    sed -i "s|magic-api-url|${VUE_APP_API_URL}|g" $file
    sed -i "s|magic-logo-url|${VUE_APP_LOGO_URL}|g" $file
    sed -i "s|magic-homepage-url|${VUE_APP_HOMEPAGE_URL}|g" $file
    sed -i "s|magic-setting|${VUE_APP_EDITABLE_INVENTORY}|g" $file
    sed -i "s|magic-title|${VUE_APP_WEBSITE_TITLE}|g" $file
    sed -i "s|magic-qr-code-resolver-url|${VUE_APP_QR_CODE_RESOLVER_URL}|g" $file
    sed -i "s|magic-generate-id-setting|${VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT}|g" $file
    done

echo "Done!"

serve -s ${ROOT_DIR} -p 8081
