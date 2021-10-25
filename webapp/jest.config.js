module.exports = {
  preset: "@vue/cli-plugin-unit-jest",
  setupFiles: ["<rootDir>/tests/setupTests.js"],
  transform: {
    "^.+\\.vue$": "vue-jest",
    "^.+\\.js$": "babel-jest",
  },
  transformIgnorePatterns: ["<rootDir>/node_modules/(?!vue-select)"],
};
