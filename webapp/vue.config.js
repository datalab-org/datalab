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
};
