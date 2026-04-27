/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Static export — the FastAPI backend serves the ``out/`` directory
  // as package data inside the installed wheel.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // During ``next dev`` the Next dev server runs on :3001 and calls
  // the FastAPI backend on :7777.  In the production bundle, both
  // live on the same origin so the prefix is a no-op.
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:7777/api/:path*" }];
  },
};

export default nextConfig;
