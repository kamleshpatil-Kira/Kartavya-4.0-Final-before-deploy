/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  allowedDevOrigins: [
    "localhost",
    "127.0.0.1",
    "192.168.1.10",
    "localhost:3000",
    "127.0.0.1:3000",
    "192.168.1.10:3000",
    "192.168.13.225:3000",
    "192.168.13.225",
  ],
};

module.exports = nextConfig;
