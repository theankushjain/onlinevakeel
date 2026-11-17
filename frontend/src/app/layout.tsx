import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OnlineVakeel.com | AI Legal Guidance & Verified Advocates — India",
  description:
    "Get instant AI-powered legal guidance in Hindi & English. Verified Bare Act citations (BNS, NI Act, RERA, CPA), automatic legal notice drafting, and direct matching with Bar Council verified Indian advocates.",
  keywords: [
    "online vakeel", "indian legal ai", "cheque bounce notice 138",
    "rera lawyer", "consumer forum complaint", "free legal aid india", "nalsa helpline",
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
