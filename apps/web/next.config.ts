import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Produces a minimal, self-contained server bundle (node_modules
  // pruned to only what's actually imported) for a leaner Docker image.
  output: "standalone",
};

export default nextConfig;
