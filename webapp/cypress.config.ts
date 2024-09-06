import { defineConfig } from "cypress";

export default defineConfig({
  projectId: "4kqx5i",
  e2e: {
    // these defaults can be overwritten by environment variables in .env.test_e2e
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5000",
    experimentalMemoryManagement: true,
    defaultCommandTimeout: 10000,
  },
  component: {
    devServer: {
      framework: "vue-cli",
      bundler: "webpack",
    },
  },
});
