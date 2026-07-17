import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import vueJsx from "@vitejs/plugin-vue-jsx";
import { nodePolyfills } from "vite-plugin-node-polyfills";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";
import fs from "fs";

// This config is an ES module (.mjs) because @vitejs/plugin-vue-jsx pulls in
// ESM-only dependencies that can't be require()'d. That means the CommonJS
// __dirname global isn't available, so reconstruct it from import.meta.url.
const __dirname = dirname(fileURLToPath(import.meta.url));

// A deployment can override the skeleton About page by placing a file at
// public/custom/components/CustomAbout.vue (mirrors the old vue.config.js
// NormalModuleReplacementPlugin behaviour).
const customAboutPath = resolve(__dirname, "public/custom/components/CustomAbout.vue");

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // `loadEnv` only reads .env files; the production Docker build and the
  // `yarn build`/`serve` scripts set VUE_APP_* (the `magic-*` placeholders and
  // VUE_APP_GIT_VERSION) as real environment variables, so merge process.env on
  // top (it wins, matching the old vue-cli/DefinePlugin precedence).
  const env = { ...loadEnv(mode, process.cwd(), ""), ...process.env };

  // Statically replace the build-time `process.env.VUE_APP_*` references used
  // throughout src/. We keep the VUE_APP_ prefix (rather than switching to
  // VITE_/import.meta.env) so that self-hosted deployments and the production
  // image's runtime `magic-*` placeholder patching (.docker/app_entrypoint.sh)
  // keep working unchanged. Unset vars are left to the `process` polyfill,
  // which resolves them to `undefined` so the existing fallbacks apply.
  const define = {
    "process.env.BASE_URL": JSON.stringify(env.BASE_URL || "/"),
  };
  for (const key of Object.keys(env)) {
    if (key.startsWith("VUE_APP_")) {
      define[`process.env.${key}`] = JSON.stringify(env[key]);
    }
  }

  const alias = [
    // Bokeh is provided as a global by the CDN <script> tags in index.html;
    // shim the bare "bokeh" import to that global (replaces webpack externals).
    { find: /^bokeh$/, replacement: resolve(__dirname, "src/bokeh-shim.js") },
  ];
  if (fs.existsSync(customAboutPath)) {
    alias.push({
      find: /^@\/components\/CustomAbout\.vue$/,
      replacement: customAboutPath,
    });
  }
  alias.push({ find: "@", replacement: resolve(__dirname, "src") });

  // Inject the `x_datalab_api_url` meta tag the old vue.config.js added via
  // html-webpack-plugin's `meta` option. This is a public contract: external
  // tooling (e.g. the datalab-api Python client) scrapes it from the served
  // webapp to auto-discover the API URL. In the production image the value is
  // the `magic-api-url` placeholder, which app_entrypoint.sh patches at runtime.
  const apiUrlMetaPlugin = {
    name: "datalab-api-url-meta",
    transformIndexHtml() {
      return [
        {
          tag: "meta",
          attrs: {
            name: "x_datalab_api_url",
            content: env.VUE_APP_API_URL || "magic-api-url",
          },
          injectTo: "head",
        },
      ];
    },
  };

  return {
    plugins: [
      vue(),
      // Compile JSX (used by the .cy.jsx Cypress component specs) as Vue JSX,
      // matching the old vue-cli/@vue/babel-plugin-jsx behaviour.
      vueJsx(),
      apiUrlMetaPlugin,
      nodePolyfills({
        globals: { Buffer: true, process: true },
        protocolImports: true,
      }),
    ],
    define,
    resolve: {
      alias,
      // Allow extensionless imports (e.g. `@/components/Navbar`) that the
      // codebase relies on, matching webpack's default resolution.
      extensions: [".mjs", ".js", ".jsx", ".json", ".vue"],
    },
    server: {
      port: 8080,
    },
    build: {
      outDir: "dist",
    },
  };
});
