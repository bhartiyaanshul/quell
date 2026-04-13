import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Frisk — Frisk your vibe-coded app before someone else does",
  description:
    "Zero-config CLI security scanner for apps built with Cursor, Lovable, Bolt, v0, Replit. One command. 60 seconds. Severity-ranked findings with plain-English fixes.",
  keywords: [
    "security",
    "scanner",
    "vibe coding",
    "ai",
    "vulnerability",
    "audit",
    "cli",
    "cursor",
    "lovable",
    "bolt",
  ],
  authors: [{ name: "Anshul Bhartiya", url: "https://anshulbuilds.xyz" }],
  openGraph: {
    title: "Frisk — Frisk your vibe-coded app before someone else does",
    description:
      "Zero-config CLI security scanner for vibe-coded apps. One command. 60 seconds. A report card with fixes.",
    type: "website",
    url: "https://frisk.anshulbuilds.xyz",
  },
  twitter: {
    card: "summary_large_image",
    title: "Frisk — Security scanner for vibe-coded apps",
    description:
      "One command. 60 seconds. A report card with severity-ranked findings and a plain-English fix for each one.",
    creator: "@Bhartiyaanshul",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-va-bg text-va-text font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
