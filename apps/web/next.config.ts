import type { NextConfig } from 'next';
const config: NextConfig = {
  experimental: { proxyTimeout: 180_000 },
  async rewrites() { return [{ source: '/api/:path*', destination: `${process.env.API_URL || 'http://127.0.0.1:8000'}/api/:path*` }]; }
};
export default config;
