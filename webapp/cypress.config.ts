import { defineConfig } from "cypress";

export default defineConfig({
  projectId: "4kqx5i",
  e2e: {
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5001",
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
