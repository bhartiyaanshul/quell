// Render the Open Graph banner once at build time and save it as a static
// PNG. We use @vercel/og standalone instead of Next's `app/opengraph-image`
// file convention because the site is `output: "export"` (fully static),
// which can't render dynamic image routes at request time.
//
// Output: landing/public/og.png  (1200×630, PNG)

import { ImageResponse } from "@vercel/og";
import { writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import React from "react";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_PATH = resolve(__dirname, "..", "public", "og.png");

const SIZE = { width: 1200, height: 630 };

const Pill = ({ color, label }) =>
  React.createElement(
    "div",
    { style: { display: "flex", alignItems: "center", gap: "12px" } },
    React.createElement("div", {
      style: {
        display: "flex",
        width: "12px",
        height: "12px",
        borderRadius: "999px",
        background: color,
      },
    }),
    React.createElement("div", { style: { display: "flex" } }, label),
  );

const Banner = () =>
  React.createElement(
    "div",
    {
      style: {
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "72px 80px",
        background: "#0a0a0f",
        backgroundImage:
          "radial-gradient(ellipse 70% 50% at 85% 12%, rgba(251,146,60,0.32), transparent 62%), radial-gradient(ellipse 60% 55% at 10% 92%, rgba(167,139,250,0.22), transparent 62%)",
        color: "#fafafa",
        fontFamily: "Inter",
      },
    },
    // Brand row
    React.createElement(
      "div",
      { style: { display: "flex", alignItems: "center", gap: "18px" } },
      React.createElement("div", {
        style: {
          display: "flex",
          width: "44px",
          height: "44px",
          borderRadius: "12px",
          background:
            "linear-gradient(135deg, #fcd34d 0%, #fb923c 55%, #a78bfa 100%)",
        },
      }),
      React.createElement(
        "div",
        {
          style: {
            display: "flex",
            fontSize: "30px",
            fontWeight: 700,
            letterSpacing: "0.22em",
          },
        },
        "QUELL",
      ),
    ),
    // Headline (push to bottom area)
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          flexDirection: "column",
          marginTop: "auto",
          fontSize: "92px",
          fontWeight: 600,
          lineHeight: 1.04,
          letterSpacing: "-0.025em",
        },
      },
      React.createElement(
        "div",
        { style: { display: "flex" } },
        "An on-call engineer",
      ),
      React.createElement(
        "div",
        {
          style: {
            display: "flex",
            backgroundImage:
              "linear-gradient(90deg, #fcd34d 0%, #fb923c 50%, #a78bfa 100%)",
            backgroundClip: "text",
            color: "transparent",
          },
        },
        "that never sleeps.",
      ),
    ),
    // Subtitle
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          marginTop: "26px",
          fontSize: "28px",
          lineHeight: 1.4,
          color: "#a1a1aa",
          maxWidth: "960px",
        },
      },
      "Watches your logs. Investigates incidents in a Docker sandbox. Drafts the PR while you sleep.",
    ),
    // Pills
    React.createElement(
      "div",
      {
        style: {
          display: "flex",
          gap: "32px",
          marginTop: "44px",
          fontSize: "22px",
          color: "#a1a1aa",
        },
      },
      React.createElement(Pill, { color: "#fb923c", label: "Open source" }),
      React.createElement(Pill, {
        color: "#a78bfa",
        label: "Docker-sandboxed",
      }),
      React.createElement(Pill, { color: "#fcd34d", label: "Apache 2.0" }),
    ),
  );

async function main() {
  const response = new ImageResponse(React.createElement(Banner), SIZE);
  const buffer = Buffer.from(await response.arrayBuffer());

  await mkdir(dirname(OUT_PATH), { recursive: true });
  await writeFile(OUT_PATH, buffer);

  const sizeKb = (buffer.length / 1024).toFixed(1);
  console.log(`✓ Generated og.png (${SIZE.width}×${SIZE.height}, ${sizeKb} KB) → ${OUT_PATH}`);
}

main().catch((err) => {
  console.error("✗ Failed to generate og.png:", err);
  process.exit(1);
});
