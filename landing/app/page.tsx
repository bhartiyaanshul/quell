import { Architecture } from "@/components/Architecture";
import { CTA } from "@/components/CTA";
import { Features } from "@/components/Features";
import { Footer } from "@/components/Footer";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { InstallTabs } from "@/components/InstallTabs";
import { Navbar } from "@/components/Navbar";
import { SkillsShowcase } from "@/components/SkillsShowcase";
import { TerminalShowcase } from "@/components/TerminalShowcase";

export default function Page() {
  return (
    <main className="relative bg-bg-base overflow-x-clip">
      <Navbar />
      {/* Hero — sticky, GSAP tilts it back as the user scrolls */}
      <div className="sticky top-0 z-0">
        <Hero />
      </div>
      {/* Stacked sections — each opaque so they cover the hero cleanly */}
      <div className="relative z-10 bg-bg-base">
        <TerminalShowcase />
      </div>
      <div className="relative z-20 bg-bg-base">
        <HowItWorks />
      </div>
      <div className="relative z-30 bg-bg-base">
        <Features />
      </div>
      <div className="relative z-40 bg-bg-base">
        <SkillsShowcase />
      </div>
      <div className="relative z-50 bg-bg-base">
        <InstallTabs />
      </div>
      <div className="relative z-[60] bg-bg-base">
        <Architecture />
      </div>
      <div className="relative z-[70] bg-bg-base">
        <CTA />
      </div>
      <div className="relative z-[80] bg-bg-base">
        <Footer />
      </div>
    </main>
  );
}
