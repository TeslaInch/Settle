import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#1B4332",
};

export const metadata: Metadata = {
  title: "Settle",
  description: "Your agreements. Witnessed. Sealed. Safe.",
  applicationName: "Settle",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Settle",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: "/icons/icon-192.svg", sizes: "192x192", type: "image/svg+xml" },
      { url: "/icons/icon-512.svg", sizes: "512x512", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/icons/icon-192.svg", sizes: "192x192" },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* PWA / Apple-specific tags not covered by Next.js metadata API */}
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Settle" />
        <link rel="apple-touch-icon" href="/icons/icon-192.svg" />
        <link rel="apple-touch-icon" sizes="192x192" href="/icons/icon-192.svg" />
        <link rel="apple-touch-icon" sizes="512x512" href="/icons/icon-512.svg" />
        <meta name="msapplication-TileColor" content="#1B4332" />
        <meta name="msapplication-tap-highlight" content="no" />
      </head>
      <body>{children}</body>
    </html>
  );
}
