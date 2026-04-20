/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Output as static files so it deploys to any static host
  // (Vercel, Cloudflare Pages, GitHub Pages, Netlify, …).
  output: "export",
  images: {
    // next/image needs this when output: "export".
    unoptimized: true,
  },
  trailingSlash: true,
};

export default nextConfig;
