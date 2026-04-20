import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Quell — Your production's autonomous on-call",
  description:
    "Open-source multi-agent incident response. Quell watches production, investigates incidents via LLM-backed agents in a Docker sandbox, and produces a structured report for human review — all while you sleep.",
  openGraph: {
    title: "Quell — Your production's autonomous on-call",
    description:
      "Watch production. Investigate incidents. Draft the fix. All while you sleep.",
    url: "https://quell.anshulbuilds.xyz",
    siteName: "Quell",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Quell — Your production's autonomous on-call",
    description:
      "Watch production. Investigate incidents. Draft the fix. All while you sleep.",
    creator: "@Bhartiyaanshul",
  },
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body className="bg-bg-base font-sans text-fg antialiased selection:bg-accent/30">
        {children}
      </body>
    </html>
  );
}
