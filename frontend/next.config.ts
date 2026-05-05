import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";
const basePath = isProd ? "/dashboard-financeiro" : "";

const nextConfig: NextConfig = {
  output: isProd ? "export" : undefined,
  basePath,
  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
    NEXT_PUBLIC_STATIC: isProd ? "true" : "false",
  },
  images: {
    unoptimized: true, // necessário para export estático
  },
};

export default nextConfig;
