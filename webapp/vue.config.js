const { ProvidePlugin, NormalModuleReplacementPlugin } = require("webpack");
const fs = require("fs");
const path = require("path");

const customAboutPath = path.resolve(__dirname, "public/custom/components/CustomAbout.vue");

module.exports = {
  transpileDependencies: ["mermaid"],
  configureWebpack: (config) => {
    config.resolve.symlinks = false;

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

    config.externals = {
      ...config.externals,
      bokeh: "Bokeh",
    };
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

    config.plugins = [...(config.plugins || []), ...plugins];
  },
  chainWebpack: (config) => {
    config.plugin("html").tap((args) => {
      args[0].title = process.env.VUE_APP_WEBSITE_TITLE || "datalab";
      args[0].meta = {
        x_datalab_api_url: process.env.VUE_APP_API_URL,
      };
      return args;
    });
  },
};
