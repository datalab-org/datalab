module.exports = function override(api) {
  var env = api.cache(() => process.env.NODE_ENV);
  var isProd = api.cache(() => env === "production");
  let config = {};

  if (isProd) {
    config["plugins"] = [
      "@babel/plugin-transform-export-namespace-from",
      // Keep errors, e.g., so that invalid deployment settings are reported in production
      ["transform-remove-console", { exclude: ["error"] }],
      "@babel/plugin-transform-class-static-block",
    ];
  } else {
    config["plugins"] = [
      "@babel/plugin-transform-export-namespace-from",
      "@babel/plugin-transform-class-static-block",
    ];
  }
  config["presets"] = ["@vue/cli-plugin-babel/preset"];
  return config;
};
