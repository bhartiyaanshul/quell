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
  // Plain stacking, no sticky hero, no z-index tower. The sticky-hero pattern
  // forced the compositor to keep painting the hero under every section on
  // every scroll frame — fine on a workstation, ruinous on most laptops.
  return (
    <main className="relative bg-bg-base overflow-x-clip">
      <Navbar />
      <Hero />
      <TerminalShowcase />
      <HowItWorks />
      <Features />
      <SkillsShowcase />
      <InstallTabs />
      <Architecture />
      <CTA />
      <Footer />
    </main>
  );
}
