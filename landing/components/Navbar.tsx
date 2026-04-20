"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { Github } from "lucide-react";
import Image from "next/image";

import { REPO_URL } from "@/lib/constants";

export function Navbar() {
  const { scrollY } = useScroll();
  // Bg goes from transparent to blurred as the user scrolls past the hero.
  const bg = useTransform(
    scrollY,
    [0, 120],
    ["rgba(10,10,15,0)", "rgba(10,10,15,0.75)"],
  );
  const borderOpacity = useTransform(scrollY, [0, 120], [0, 1]);

  return (
    <motion.header
      style={{ backgroundColor: bg }}
      className="fixed inset-x-0 top-0 z-50 backdrop-blur-[6px]"
    >
      <motion.div
        style={{ opacity: borderOpacity }}
        className="absolute inset-x-0 bottom-0 h-px bg-border"
      />
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="#top" className="group flex items-center gap-2.5">
          <Image
            src="/logo.svg"
            alt="Quell logo"
            width={28}
            height={28}
            className="transition-transform duration-500 group-hover:rotate-12"
          />
          <span className="text-lg font-semibold tracking-tight">Quell</span>
        </a>

        <div className="hidden items-center gap-8 text-sm text-fg-muted md:flex">
          <a
            href="#how-it-works"
            className="transition hover:text-fg"
          >
            How it works
          </a>
          <a href="#features" className="transition hover:text-fg">
            Features
          </a>
          <a href="#install" className="transition hover:text-fg">
            Install
          </a>
          <a href="#architecture" className="transition hover:text-fg">
            Architecture
          </a>
        </div>

        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="group inline-flex items-center gap-2 rounded-full border border-border bg-bg-raised/60 px-4 py-1.5 text-sm font-medium text-fg-muted transition hover:border-border-bright hover:text-fg"
        >
          <Github size={15} className="transition group-hover:text-accent" />
          <span>GitHub</span>
        </a>
      </nav>
    </motion.header>
  );
}
