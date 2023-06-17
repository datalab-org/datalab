module.exports = {
  transpileDependencies: ["mermaid"],
  configureWebpack: (config) => {
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
      return args;
    });
  },
};
