const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  fallbacks: {
    document: "/offline",
  },
  runtimeCaching: [
    // Network-first for all API calls
    {
      urlPattern: /^https?:\/\/.*\/api\/v1\/.*/i,
      handler: "NetworkFirst",
      options: {
        cacheName: "settle-api-cache",
        expiration: {
          maxEntries: 64,
          maxAgeSeconds: 24 * 60 * 60, // 24 hours
        },
        networkTimeoutSeconds: 10,
      },
    },
    // Cache-first for Next.js static assets
    {
      urlPattern: /^\/_next\/static\/.*/i,
      handler: "CacheFirst",
      options: {
        cacheName: "next-static",
        expiration: {
          maxEntries: 128,
          maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
        },
      },
    },
    // Cache-first for images and fonts
    {
      urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico|woff|woff2|ttf|otf)$/i,
      handler: "CacheFirst",
      options: {
        cacheName: "settle-assets",
        expiration: {
          maxEntries: 64,
          maxAgeSeconds: 30 * 24 * 60 * 60,
        },
      },
    },
    // Stale-while-revalidate for static pages
    {
      urlPattern: /^https?:\/\/.*\/(?:dashboard|agreements|login|verify).*/i,
      handler: "StaleWhileRevalidate",
      options: {
        cacheName: "settle-pages",
        expiration: {
          maxEntries: 32,
          maxAgeSeconds: 24 * 60 * 60,
        },
      },
    },
  ],
});

/** @type {import('next').NextConfig} */
const nextConfig = {};

module.exports = withPWA(nextConfig);
