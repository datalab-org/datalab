module.exports = {
  transpileDependencies: ["mermaid"],
  configureWebpack: (config) => {
    config.resolve.fallback = {
      crypto: require.resolve("crypto-browserify"),
      stream: require.resolve("stream-browserify"),
    };
    config.externals = {
      ...config.externals,
      bokeh: "Bokeh",
    };
    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules/,
      type: "javascript/auto",
    });
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
