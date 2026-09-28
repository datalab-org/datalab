import { execSync } from "node:child_process";
import { defineConfig } from "cypress";

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

export default defineConfig({
  projectId: "4kqx5i",
  e2e: {
    baseUrl: "http://localhost:8080",
    apiUrl: "http://localhost:5001",
    defaultCommandTimeout: 10000,
    setupNodeEvents(on, config) {
      on("task", {
        e2eLoginTokens: () => getLoginTokens(config.projectRoot),
      });
    },
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
