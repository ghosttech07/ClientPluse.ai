import type { NextConfig } from 'next';
const config: NextConfig = {
  async headers() { return [{ source: '/fonts/:file*', headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }] }]; },
  experimental: { proxyTimeout: 180_000 },
  async rewrites() { return [{ source: '/api/:path*', destination: `${process.env.API_URL || 'http://127.0.0.1:8000'}/api/:path*` }]; }
};
export default config;
