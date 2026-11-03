module.exports = function override(api) {
  var env = api.cache(() => process.env.NODE_ENV);
  var isProd = api.cache(() => env === "production");
  // Instrument the app for code coverage of the Cypress e2e tests (see `.nycrc.json`)
  var coverage = api.cache(() => process.env.DATALAB_E2E_COVERAGE === "true");
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
  if (coverage) {
    config["plugins"].push("istanbul");
  }
  config["presets"] = ["@vue/cli-plugin-babel/preset"];
  return config;
};
