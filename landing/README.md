# Quell landing page

Next.js + TailwindCSS + Framer Motion marketing page served at
`quell.anshulbuilds.xyz`.

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 14 (App Router), static export (`output: "export"`) |
| Language | TypeScript (strict) |
| Styling | TailwindCSS + custom tokens in `tailwind.config.ts` |
| Animation | Framer Motion |
| Icons | `lucide-react` |
| Fonts | Inter + JetBrains Mono (via `next/font/google`) |

## Develop

```bash
cd landing
npm install
npm run dev        # http://localhost:3000
```

Hot-reload is on by default.  Type-check with `npm run typecheck`, lint
with `npm run lint`.

## Build + deploy

```bash
npm run build      # produces ./out/  — static HTML + assets
```

Any static host works — Vercel, Cloudflare Pages, Netlify, or even
GitHub Pages.  For the `quell.anshulbuilds.xyz` target you probably
want a Vercel project with the root directory set to `landing/`.

## Structure

```
landing/
├── app/
│   ├── layout.tsx          # Root layout + fonts + metadata
│   ├── page.tsx            # Section orchestrator
│   └── globals.css         # Tailwind + tokens + utility classes
├── components/
│   ├── Navbar.tsx          # Sticky nav with scroll-based blur
│   ├── Hero.tsx            # Word-reveal headline + CTA + TerminalDemo
│   ├── AnimatedGrid.tsx    # Hero background (grid + drifting embers)
│   ├── TerminalDemo.tsx    # Live typing terminal, loops indefinitely
│   ├── SectionHeader.tsx   # Shared eyebrow + title + body
│   ├── HowItWorks.tsx      # 4-step pipeline with animated connector
│   ├── Features.tsx        # 6 cards with mouse-follow highlight
│   ├── InstallTabs.tsx     # 5-tab install-command selector
│   ├── Architecture.tsx    # SVG diagram with drawing path + pulse
│   ├── CTA.tsx             # Final CTA with rotating glow
│   └── Footer.tsx          # Link columns
├── lib/
│   ├── utils.ts            # cn() helper (clsx + tailwind-merge)
│   └── constants.ts        # Install commands, features copy, terminal script
└── public/
    ├── logo.svg            # 128×128 gradient Q shield
    └── favicon.svg         # 32×32 variant
```

## Design notes

- **Dark-first**.  The palette (`tailwind.config.ts`) uses a deep
  indigo-black canvas (`#0a0a0f`), ember/orange for the primary
  accent (incidents, alerts, action), and a soft violet secondary.
  Meant to feel like a calm night sky with warm lights nearby.
- **Motion budget**.  Every animation honours
  `prefers-reduced-motion` by disabling the stagger — only opacity
  remains.
- **One terminal loop**.  The hero terminal types + reveals for ~10s,
  holds for ~4s, then loops.  Feels "alive" without being distracting.
- **One content source**.  Install commands, feature copy, and the
  pipeline script all live in `lib/constants.ts`.  Don't duplicate
  strings into components.

## Adding a section

1. Add the component under `components/`.
2. Import + mount it in `app/page.tsx` in the desired position.
3. If it has new copy, put strings in `lib/constants.ts`.
4. Use the shared `<SectionHeader>` for consistent top-of-section
   motion.

## Updating install commands

Edit `lib/constants.ts` → `INSTALL_COMMANDS`.  The tab bar order and
the clipboard-copy action pick up automatically.
