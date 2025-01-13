import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [vue()],
    define: {
      global: {},
      "process.env.VITE_APP_GIT_VERSION": JSON.stringify(env.VITE_APP_GIT_VERSION),
      "process.browser": true,
    },
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
        crypto: "crypto-browserify",
        stream: "stream-browserify",
        process: "process/browser/browser",
        buffer: "buffer/",
        util: "util/",
      },
      extensions: [".vue", ".js", ".json"],
    },

    optimizeDeps: {
      exclude: ["bokeh"],
      include: ["crypto-browserify", "stream-browserify", "buffer", "process/browser", "util"],
    },
    server: {
      port: 8080,
      proxy: {
        "/api": {
          target: env.VITE_APP_API_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
