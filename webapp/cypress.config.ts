import { defineConfig } from "cypress";

export default defineConfig({
  projectId: "4kqx5i",
  e2e: {
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5001",
    defaultCommandTimeout: 10000,
    setupNodeEvents(on, config) {
      require("@cypress/code-coverage/task")(on, config);
      return config;
    },
  },
  component: {
    devServer: {
      framework: "vue-cli",
      bundler: "webpack",
    },
    setupNodeEvents(on, config) {
      require("@cypress/code-coverage/task")(on, config);
      return config;
    },
  },
});
