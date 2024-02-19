#!/bin/sh

# Patch the built app to use the specified environment variables
# at runtime, then serve the app
#
# See https://stackoverflow.com/questions/53010064/pass-environment-variable-into-a-vue-app-at-runtime for inspiration.
#
set -e
ROOT_DIR=/app/dist

echo "Replacing env vars in Javascript files"
for file in $ROOT_DIR/js/app.*.js*; do
    echo "Patching $file"
    sed -i "s|magic-api-url|${VUE_APP_API_URL}|g" $file
    sed -i "s|magic-logo-url|${VUE_APP_LOGO_URL}|g" $file
    sed -i "s|magic-homepage-url|${VUE_APP_HOMEPAGE_URL}|g" $file
    done

serve -s ${ROOT_DIR} -p 8081
