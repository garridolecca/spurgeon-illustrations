import { defineConfig } from "vite";
import preact from "@preact/preset-vite";

// Served from https://<user>.github.io/spurgeon-illustrations/
export default defineConfig({
  base: process.env.BASE_PATH ?? "/spurgeon-illustrations/",
  plugins: [preact()],
  worker: { format: "es" },
  build: { target: "es2022", chunkSizeWarningLimit: 1200 },
  optimizeDeps: { exclude: ["@huggingface/transformers"] },
});
