"use client";

import Image from "next/image";
import { Github } from "lucide-react";

import { DOCS_URL, REPO_URL } from "@/lib/constants";

export function Footer() {
  return (
    <footer className="relative border-t border-border bg-bg-base">
      <div className="mx-auto max-w-6xl px-6 py-14">
        <div className="flex flex-col gap-10 md:flex-row md:items-start md:justify-between">
          <div className="max-w-sm">
            <div className="flex items-center gap-2.5">
              <Image src="/logo.svg" alt="Quell" width={26} height={26} />
              <span className="text-base font-semibold tracking-tight">
                Quell
              </span>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-fg-muted">
              Open-source multi-agent incident response.  Draft PRs, never
              auto-merge. Apache 2.0.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-x-14 gap-y-10 sm:grid-cols-3">
            <FooterColumn
              title="Product"
              links={[
                { label: "How it works", href: "#how-it-works" },
                { label: "Features", href: "#features" },
                { label: "Install", href: "#install" },
                { label: "Architecture", href: "#architecture" },
              ]}
            />
            <FooterColumn
              title="Docs"
              links={[
                { label: "Getting started", href: `${DOCS_URL}/getting-started.md` },
                { label: "Commands", href: `${DOCS_URL}/commands.md` },
                { label: "Configuration", href: `${DOCS_URL}/configuration.md` },
                { label: "Extending", href: `${DOCS_URL}/extending.md` },
              ]}
            />
            <FooterColumn
              title="Project"
              links={[
                { label: "GitHub", href: REPO_URL, external: true },
                { label: "Issues", href: `${REPO_URL}/issues`, external: true },
                {
                  label: "Discussions",
                  href: `${REPO_URL}/discussions`,
                  external: true,
                },
                { label: "License (Apache 2.0)", href: `${REPO_URL}/blob/main/LICENSE`, external: true },
              ]}
            />
          </div>
        </div>

        <div className="mt-14 flex flex-col-reverse items-start justify-between gap-6 border-t border-border pt-8 text-xs text-fg-dim sm:flex-row sm:items-center">
          <p>
            Built by{" "}
            <a
              href="https://x.com/Bhartiyaanshul"
              target="_blank"
              rel="noopener noreferrer"
              className="text-fg-muted underline-offset-2 transition hover:text-fg hover:underline"
            >
              Anshul Bhartiya
            </a>
            .  Proudly Apache 2.0.
          </p>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-fg-muted transition hover:text-fg"
          >
            <Github size={13} />
            bhartiyaanshul/quell
          </a>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({
  title,
  links,
}: {
  title: string;
  links: { label: string; href: string; external?: boolean }[];
}) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-fg-dim">
        {title}
      </div>
      <ul className="mt-4 space-y-2.5 text-sm">
        {links.map((l) => (
          <li key={l.label}>
            <a
              href={l.href}
              target={l.external ? "_blank" : undefined}
              rel={l.external ? "noopener noreferrer" : undefined}
              className="text-fg-muted transition hover:text-fg"
            >
              {l.label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
