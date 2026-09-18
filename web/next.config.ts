import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    // Pin the project root explicitly. Without this, Turbopack can pick the
    // wrong root when it finds an unrelated lockfile in a parent folder
    // (e.g. a stray package-lock.json sitting on the Desktop), which makes
    // Tailwind scan the wrong directory for classes and silently produce an
    // almost-empty stylesheet.
    root: path.join(__dirname),
  },
};

export default nextConfig;