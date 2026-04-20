# Media directory

This directory holds the demo GIFs, screenshots, and architecture
diagrams referenced from the top-level README and the landing page.
Files are committed as-is (no Git LFS).  Keep them small — prefer
animated PNG or WebP over MP4 where possible, and cap any recording at
~3 MB.

## Expected files

| File | Used by | How to capture |
|------|---------|----------------|
| `hero-demo.gif` | [`README.md`](../../README.md) hero section | `quell watch` running against `fixtures/sample_logs/app_error.log`; record the first ~15s with an incident firing |
| `quell-init.gif` | README "Getting started" section | `quell init` interactive wizard — full flow, ~25s |
| `quell-doctor.png` | README "Getting started" | Terminal screenshot of a successful `quell doctor` run |
| `quell-history.png` | README "Inspect" section | `quell history` output after a couple of incidents |
| `architecture.svg` | README "Architecture" section | Export the animated SVG from the landing page or hand-draw one |
| `og-banner.png` | OpenGraph / Twitter card (1200×630) | Landing hero screenshot with the logo overlaid |

## Recording tips

- macOS: [Kap](https://getkap.co/) for animated recordings, `Cmd-Shift-5`
  for static screenshots.  Record at 2x the final size, then downscale
  with [gifski](https://gif.ski/) or `ffmpeg -vf scale=720:-1`.
- Use a dark terminal theme (matches the landing's aesthetic).  The
  system default on macOS 14+ is fine; or use iTerm2 with a subtle
  dark theme and ~20pt JetBrains Mono.
- Cap recordings at 15 fps — the eye doesn't need more and it
  halves file size.
- After `gifski`, run through [ImageOptim](https://imageoptim.com/) or
  `gifsicle -O3`.

## Size targets

- `hero-demo.gif`: ≤ 3 MB (aim for 1.5 MB).
- Static screenshots: ≤ 400 KB each.
- `og-banner.png`: ≤ 800 KB; 1200×630 exactly.

## Placeholder fallback

Until the real media lands, the top-level README renders a code-block
"storyboard" for each placeholder path.  That means the README is
readable on GitHub *today* even with no binaries committed.
