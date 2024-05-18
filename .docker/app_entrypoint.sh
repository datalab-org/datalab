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

echo "Replacing env vars in Javascript files"
echo "Settings:"
echo ""
echo "  API_URL: ${VUE_APP_API_URL}"
echo "  LOGO_URL: ${VUE_APP_LOGO_URL}"
echo "  HOMEPAGE_URL: ${VUE_APP_HOMPAGE_URL}"
echo ""
echo "Patching..."

for file in $ROOT_DIR/js/app.*.js*; do
    echo "$file"
    sed -i "s|magic-api-url|${VUE_APP_API_URL}|g" $file
    sed -i "s|magic-logo-url|${VUE_APP_LOGO_URL}|g" $file
    sed -i "s|magic-homepage-url|${VUE_APP_HOMEPAGE_URL}|g" $file
    sed -i "s|magic-setting|${VUE_APP_EDITABLE_INVENTORY}|g" $file
    done

echo "Done!"

serve -s ${ROOT_DIR} -p 8081
