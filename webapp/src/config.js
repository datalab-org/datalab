// Resolves the deployment settings of the web app, which are defined in `config.schema.json`.
//
// Values come from `window.__DATALAB_CONFIG__` (see `public/config.js`, written by the production
// container on startup), then from the `VUE_APP_*` values compiled in from `.env` files.
//
// The production container checks its settings against the same schema and refuses to start if
// they are invalid, so the checks here mainly serve development and non-Docker builds.
//
// New settings must be added to `config.schema.json` and `BUILD_CONFIG` below (plus `PARSERS` if
// they are not strings). They must also be added to the `app` service in `docker-compose.yml`, as
// Compose only passes listed variables through, so they would otherwise be ignored in production.

import schema from "./config.schema.json";

export const SETTINGS = schema.properties;

const parseBoolean = (value) => value.toLowerCase() === "true";

const PARSERS = {
  AUTOMATICALLY_GENERATE_ID_DEFAULT: parseBoolean,
  EDITABLE_INVENTORY: parseBoolean,
  HIDE_COLLECTIONS: parseBoolean,
  LOGO_WIDTH: Number,
};

// These must be written out in full, as they are statically replaced at build time.
const BUILD_CONFIG = {
  API_URL: process.env.VUE_APP_API_URL,
  AUTOMATICALLY_GENERATE_ID_DEFAULT: process.env.VUE_APP_AUTOMATICALLY_GENERATE_ID_DEFAULT,
  EDITABLE_INVENTORY: process.env.VUE_APP_EDITABLE_INVENTORY,
  GIT_VERSION: process.env.VUE_APP_GIT_VERSION,
  HIDE_COLLECTIONS: process.env.VUE_APP_HIDE_COLLECTIONS,
  HOMEPAGE_URL: process.env.VUE_APP_HOMEPAGE_URL,
  LOGO_URL: process.env.VUE_APP_LOGO_URL,
  LOGO_WIDTH: process.env.VUE_APP_LOGO_WIDTH,
  QR_CODE_RESOLVER_URL: process.env.VUE_APP_QR_CODE_RESOLVER_URL,
  WEBSITE_TITLE: process.env.VUE_APP_WEBSITE_TITLE,
};

function isValid(setting, value) {
  return !setting.pattern || new RegExp(setting.pattern).test(value);
}

// Invalid or unknown settings are reported in the browser console rather than stopping
// the app from loading, with invalid settings falling back to their defaults.
export function resolveConfig(runtimeConfig, buildConfig) {
  for (const name of Object.keys(runtimeConfig)) {
    if (!(name in SETTINGS)) {
      console.error(`Ignoring unknown datalab setting ${name}.`);
    }
  }

  const config = {};
  for (const [name, setting] of Object.entries(SETTINGS)) {
    let value = runtimeConfig[name] ?? buildConfig[name];
    // Empty values count as unset
    if (value == null || value === "") {
      value = setting.default;
    } else if (!isValid(setting, String(value))) {
      console.error(
        `Invalid value "${value}" for datalab setting ${name}, using the default ` +
          `(${setting.default}): ${setting.description}`,
      );
      value = setting.default;
    }
    const parse = PARSERS[name] ?? String;
    config[name] = value == null ? undefined : parse(String(value));
  }
  return config;
}

export const CONFIG = resolveConfig(window.__DATALAB_CONFIG__ || {}, BUILD_CONFIG);
