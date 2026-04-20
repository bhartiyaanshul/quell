import { Architecture } from "@/components/Architecture";
import { CTA } from "@/components/CTA";
import { Features } from "@/components/Features";
import { Footer } from "@/components/Footer";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { InstallTabs } from "@/components/InstallTabs";
import { Navbar } from "@/components/Navbar";

export default function Page() {
  return (
    <main className="relative overflow-x-hidden">
      <Navbar />
      <Hero />
      <HowItWorks />
      <Features />
      <InstallTabs />
      <Architecture />
      <CTA />
      <Footer />
    </main>
  );
}
