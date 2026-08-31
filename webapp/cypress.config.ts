import { defineConfig } from "cypress";

export default defineConfig({
  projectId: "4kqx5i",
  e2e: {
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5001",
    defaultCommandTimeout: 10000,
  },
  component: {
    // Avoid port 8080's macOS WebSocket issue and the usual local dev-server port, 8081.
    port: 8082,
    devServer: {
      framework: "vue-cli",
      bundler: "webpack",
    },
  },
});
