import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";

import { ExtensionErrorFilter } from "@/components/ExtensionErrorFilter";
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

// Synchronous filter installed before any other JS runs.
//
// MetaMask's inpage.js fires its unhandledrejection during page load,
// which is BEFORE React hydrates — so a React useEffect filter misses
// the first event.  This inline script installs capture-phase
// listeners immediately, so Next's dev-overlay handler never sees
// errors originating from chrome-extension:// URLs.
const EXTENSION_FILTER_SCRIPT = `
(function(){
  var MARKERS=["chrome-extension://","moz-extension://","safari-web-extension://"];
  function isExt(t){if(typeof t!=="string")return false;for(var i=0;i<MARKERS.length;i++){if(t.indexOf(MARKERS[i])!==-1)return true;}return false;}
  function text(r){if(!r)return "";if(typeof r==="string")return r;try{return (r.stack||"")+" "+(r.message||"")+" "+String(r);}catch(e){return "";}}
  window.addEventListener("error",function(e){
    var s=(e.filename||"")+" "+(e.message||"")+" "+text(e.error);
    if(isExt(s)){e.preventDefault();e.stopImmediatePropagation();e.stopPropagation();return false;}
  },true);
  window.addEventListener("unhandledrejection",function(e){
    var t=text(e.reason);
    if(isExt(t)||t.toLowerCase().indexOf("metamask")!==-1){e.preventDefault();e.stopImmediatePropagation();e.stopPropagation();}
  },true);
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <head>
        {/* Inline — runs synchronously as the HTML parser encounters it,
            before any bundled JS (including Next's dev overlay) loads. */}
        <script
          dangerouslySetInnerHTML={{ __html: EXTENSION_FILTER_SCRIPT }}
        />
        {/* Preload the cinematic hero photo so it lands before the
            scramble + GSAP timeline kicks in. */}
        <link rel="preload" as="image" href="/bg/hero.jpg" />
      </head>
      <body className="bg-bg-base font-sans text-fg antialiased selection:bg-accent/30">
        <ExtensionErrorFilter />
        {children}
        <Analytics />
      </body>
    </html>
  );
}
