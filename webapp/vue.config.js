const { ProvidePlugin, NormalModuleReplacementPlugin } = require("webpack");
const fs = require("fs");
const path = require("path");
const { properties: SETTINGS } = require("./src/config.schema.json");

const customAboutPath = path.resolve(__dirname, "public/custom/components/CustomAbout.vue");
const customLoginInfoPath = path.resolve(__dirname, "public/custom/components/CustomLoginInfo.vue");

module.exports = {
  configureWebpack: (config) => {
    config.resolve.symlinks = false;

    // Opt-in persistent cache of the compiled modules (in `node_modules/.cache/webpack`), used
    // to speed up the dev server in the CI e2e tests. Webpack cannot see settings that change
    // the babel output, so these are part of the cache version.
    if (process.env.DATALAB_WEBPACK_CACHE === "true") {
      config.cache = {
        type: "filesystem",
        version: [process.env.NODE_ENV, process.env.DATALAB_E2E_COVERAGE].join("-"),
        buildDependencies: {
          config: [__filename, path.resolve(__dirname, "babel.config.js")],
        },
      };
    }

    config.resolve.fallback = {
      stream: false,
      process: require.resolve("process/browser"),
      buffer: require.resolve("buffer/"),
      vm: false,
    };
    // disable stats output in production due to bad `wrap-ansi` ESM/CommonJS interop
    if (process.env.NODE_ENV === "production") {
      config.stats = "none";
    }

    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules/,
      type: "javascript/auto",
    });
    const plugins = [
      new ProvidePlugin({
        process: "process/browser",
      }),
    ];

    // If a deployment provides a custom CustomAbout.vue, use it instead of the skeleton
    if (fs.existsSync(customAboutPath)) {
      plugins.push(
        new NormalModuleReplacementPlugin(/\/components\/CustomAbout\.vue$/, customAboutPath),
      );
    }

    // Replace the default login information with deployment-specific content when provided
    if (fs.existsSync(customLoginInfoPath)) {
      plugins.push(
        new NormalModuleReplacementPlugin(/\/components\/LoginInfo\.vue$/, customLoginInfoPath),
      );
    }

    config.plugins = [...(config.plugins || []), ...plugins];
  },
  chainWebpack: (config) => {
    config.plugin("html").tap((args) => {
      args[0].title = process.env.VUE_APP_WEBSITE_TITLE || SETTINGS.WEBSITE_TITLE.default;
      args[0].meta = {
        x_datalab_api_url: process.env.VUE_APP_API_URL || SETTINGS.API_URL.default,
      };
      return args;
    });
  },
};
