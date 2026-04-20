# Media directory

Every image, GIF, video, and SVG referenced from the top-level README
and the landing page lives here.  Files are committed as-is (no Git
LFS) — keep them small.

## File inventory

### Already committed (no capture needed)

| File | Used by | Shape |
|------|---------|-------|
| `banner.svg` | README hero | 1280×400 header banner with logo + tagline |
| `flow-diagram.svg` | README "How it works" | 1100×220 four-node pipeline |

### To capture (placeholders in the README are image/video tags)

| File | Used by | How to capture |
|------|---------|----------------|
| `hero-demo.gif` | README hero (under the banner) | `quell watch` reacting to `fixtures/sample_logs/app_error.log`.  ~15s, ≤1.5 MB. |
| `hero-demo.mp4` | Same slot (served via HTML5 `<video>` when GitHub supports it) | Same content, encoded as H.264 + AAC MP4.  ≤3 MB. |
| `quell-init.gif` | "Quick start" section | Full `quell init` wizard flow.  ~25s, ≤2 MB. |
| `quell-doctor.png` | "Quick start" | Static screenshot — every row green. ≤200 KB. |
| `quell-history.png` | "Quick start" | `quell history` table after a few incidents. ≤200 KB. |
| `quell-show.png` | "Quick start" | `quell show <id>` detailed view. ≤200 KB. |
| `feature-sandboxed.png` | Features grid | Screenshot of a tool running inside the Docker sandbox (terminal w/ bearer token). ≤250 KB. |
| `feature-subagents.png` | Features grid | `view_graph` tool output with parent + 2 children. ≤200 KB. |
| `feature-skills.png` | Features grid | Render of `quell/skills/incidents/stripe-webhook-timeout.md`. ≤200 KB. |
| `arch-detailed.svg` | "Architecture" deep-dive | Optional hand-drawn architecture diagram. |
| `og-banner.png` | OpenGraph / Twitter card | 1200×630, lands in Twitter/Slack/LinkedIn unfurls. |

## Recording tips

- **macOS** — [Kap](https://getkap.co/) for GIFs, `Cmd-Shift-5` for PNGs.
- **Cross-platform** — OBS Studio → ffmpeg pipeline.
- Record at **2× target size**, then downscale with
  [gifski](https://gif.ski/) or `ffmpeg -vf scale=720:-1`.
- Cap GIFs at **15 fps** — the eye doesn't need more.
- Pipe through [ImageOptim](https://imageoptim.com/) or `gifsicle -O3`
  after export.
- Use a **dark terminal theme** (matches the README + landing).
  iTerm2 or macOS Terminal.app default.  ~20pt JetBrains Mono.
- Set the window to **exactly 720px wide** — the README renders at
  that size, so don't waste pixels.

## Size budget

| Asset type | Target | Hard cap |
|------------|--------|----------|
| Hero GIF | 1.5 MB | 3 MB |
| MP4 alt | 2.5 MB | 4 MB |
| Feature GIFs | 800 KB | 2 MB |
| PNG screenshots | 150 KB | 400 KB |
| OG banner | 500 KB | 800 KB |

## If a file isn't committed yet

The top-level README uses `<img>` / `<video>` tags that silently fail
when the file is missing — GitHub will render the alt text and the
surrounding prose stays readable.  Every visual block is followed by
a `<details>` storyboard that shows the equivalent terminal output in
a code block, so the README is fully useful on day one even with zero
media committed.
