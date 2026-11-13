const { execSync } = require("node:child_process");
const { defineConfig } = require("cypress");

// The e2e tests log in with tokens minted by `invoke dev.seed-e2e-users`, which must use the
// same database and secret key as the API under test. Set `DATALAB_E2E_SEED_COMMAND` to run it
// elsewhere, e.g., inside the API container in CI.
const SEED_COMMAND =
  process.env.DATALAB_E2E_SEED_COMMAND ||
  "uv run --directory ../pydatalab invoke dev.seed-e2e-users";
// Tokens are valid for an hour, so mint new ones well before they expire
const TOKEN_MAX_AGE_MS = 45 * 60 * 1000;

let loginTokens = null;
let loginTokensMintedAt = 0;

function getLoginTokens(projectRoot) {
  if (!loginTokens || Date.now() - loginTokensMintedAt > TOKEN_MAX_AGE_MS) {
    const output = execSync(SEED_COMMAND, {
      cwd: projectRoot,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "inherit"],
    });
    // The tokens are printed as JSON on the final line of output
    loginTokens = JSON.parse(output.trim().split("\n").pop() ?? "{}");
    loginTokensMintedAt = Date.now();
  }
  return loginTokens;
}

module.exports = defineConfig({
  projectId: "4kqx5i",
  e2e: {
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5001",
    defaultCommandTimeout: 10000,
    env: {
      // Collect coverage only from an app built with `DATALAB_E2E_COVERAGE=true` (see
      // `vite.config.mjs`), as `@cypress/code-coverage` warns on every test otherwise
      coverage: process.env.DATALAB_E2E_COVERAGE === "true",
    },
    setupNodeEvents(on, config) {
      require("@cypress/code-coverage/task")(on, config);
      on("task", {
        e2eLoginTokens: () => getLoginTokens(config.projectRoot),
      });
      return config;
    },
  },
  component: {
    // Avoid port 8080's macOS WebSocket issue and the usual local dev-server port, 8081.
    port: 8082,
    setupNodeEvents(on) {
      // Lets component tests print to the terminal output, e.g., measured DOM sizes
      on("task", {
        log(message) {
          console.log(message);
          return null;
        },
      });
    },
    devServer: {
      framework: "vue",
      bundler: "vite",
    },
  },
});
