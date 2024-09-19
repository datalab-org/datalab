module.exports = function override(api) {
  var env = api.cache(() => process.env.NODE_ENV);
  var isProd = api.cache(() => env === "production");
  let config = {};

  if (isProd) {
    config["plugins"] = [
      "@babel/plugin-transform-export-namespace-from",
      "transform-remove-console",
    ];
  } else {
    config["plugins"] = ["@babel/plugin-transform-export-namespace-from", "istanbul"];
  }
  config["presets"] = ["@vue/cli-plugin-babel/preset"];
  return config;
};
