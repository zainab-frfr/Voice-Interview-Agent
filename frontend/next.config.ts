import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_LIVEKIT_URL: process.env.LIVEKIT_URL,
  },
};

export default nextConfig;
