import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [vue()],
    define: {
      "import.meta.env.VUE_APP_WEBSITE_TITLE": JSON.stringify(
        env.VUE_APP_WEBSITE_TITLE || "datalab",
      ),
      "import.meta.env.VUE_APP_API_URL": JSON.stringify(env.VUE_APP_API_URL),
    },
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
      },
      extensions: [".vue", ".js", ".json"],
    },
    optimizeDeps: {
      exclude: ["bokeh"],
    },
    server: {
      port: 8080,
      proxy: {
        "/api": {
          target: env.VUE_APP_API_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
