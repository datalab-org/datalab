import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5001",
    experimentalMemoryManagement: true,
    projectId: "4kqx5i",
    defaultCommandTimeout: 10000,
  },
  component: {
    projectId: "4kqx5i",
    devServer: {
      framework: "vue-cli",
      bundler: "webpack",
    },
  },
});
