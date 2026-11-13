import fs from "node:fs";
import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import { defineConfig, loadEnv } from "vite";
import istanbul from "vite-plugin-istanbul";

const SETTINGS = JSON.parse(
  fs.readFileSync(new URL("./src/config.schema.json", import.meta.url), "utf-8"),
).properties;

const srcDir = fileURLToPath(new URL("./src", import.meta.url));

// Deployments can replace these components with their own, from `public/custom/components/`
// (see `docs/config.md`). Any import of a module with the same name is redirected.
const CUSTOM_COMPONENTS = {
  "CustomAbout.vue": "public/custom/components/CustomAbout.vue",
  "LoginInfo.vue": "public/custom/components/CustomLoginInfo.vue",
};

function customComponents() {
  const replacements = Object.entries(CUSTOM_COMPONENTS)
    .map(([name, path]) => [name, fileURLToPath(new URL(path, import.meta.url))])
    .filter(([, path]) => fs.existsSync(path));
  return {
    name: "datalab-custom-components",
    enforce: "pre",
    resolveId(source) {
      for (const [name, path] of replacements) {
        if (source.endsWith(`/components/${name}`)) {
          return path;
        }
      }
      return null;
    },
  };
}

// Fills in the placeholders in `index.html`. In the production image, these are overwritten
// by `.docker/app_entrypoint.sh` with the settings the container is started with.
function htmlSettings(env) {
  const escape = (value) =>
    String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
  const values = {
    DATALAB_WEBSITE_TITLE: env.VUE_APP_WEBSITE_TITLE || SETTINGS.WEBSITE_TITLE.default,
    DATALAB_API_URL: env.VUE_APP_API_URL || SETTINGS.API_URL.default,
  };
  return {
    name: "datalab-html-settings",
    transformIndexHtml: {
      order: "pre",
      handler: (html) =>
        html.replaceAll(/%(DATALAB_[A-Z_]+)%/g, (match, name) =>
          name in values ? escape(values[name]) : match,
        ),
    },
  };
}

export default defineConfig(({ mode }) => {
  // Includes the `VUE_APP_*` variables set in the environment, which take precedence
  const env = loadEnv(mode, process.cwd(), "VUE_APP_");
  // As with vue-cli, the dev server port can be set with `PORT`, also in `.env` files
  const port = Number(loadEnv(mode, process.cwd(), "PORT").PORT) || 8080;
  // Instrument the app for code coverage of the Cypress e2e tests (see `.nycrc.json`)
  const coverage = process.env.DATALAB_E2E_COVERAGE === "true";

  return {
    // The deployment settings keep the `VUE_APP_` prefix from vue-cli (see `src/config.js`)
    envPrefix: "VUE_APP_",
    plugins: [
      customComponents(),
      vue(),
      // The component tests are written in JSX
      vueJsx(),
      htmlSettings(env),
      coverage &&
        istanbul({
          include: "src/*",
          extension: [".js", ".vue"],
          requireEnv: false,
          forceBuildInstrument: true,
        }),
    ],
    resolve: {
      alias: { "@": srcDir },
      // Many imports leave out the `.vue` extension, which vue-cli resolved
      extensions: [".mjs", ".js", ".jsx", ".json", ".vue"],
    },
    server: { port },
    preview: { port },
    build: {
      rolldownOptions: {
        treeshake: {
          // Drop console output from production builds, except errors, e.g., so that invalid
          // deployment settings are still reported
          manualPureFunctions:
            mode === "production"
              ? ["console.log", "console.info", "console.debug", "console.warn", "console.trace"]
              : [],
        },
      },
    },
  };
});
