import { defineConfig } from "cypress";
import vue from "@vitejs/plugin-vue";
import { nodePolyfills } from "vite-plugin-node-polyfills";

export default defineConfig({
  projectId: "4kqx5i",
  e2e: {
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5001",
    defaultCommandTimeout: 10000,
    specPattern: "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
  },
  component: {
    devServer: {
      framework: "vue",
      bundler: "vite",
    },
    specPattern: "cypress/component/**/*.cy.{js,jsx,ts,tsx}",
    plugins: [vue(), nodePolyfills({ protocolImports: true, include: ["crypto"] })],
  },
});
