"use client";

import Link from "next/link";
import {
  CalendarDays,
  Search,
  FileText,
  ClipboardCheck,
  Package,
  MessageSquare,
  GraduationCap,
  BookOpen,
  Wrench,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: CalendarDays,
    title: "Smart Scheduling",
    description:
      "AI-optimized scheduling that accounts for travel time, skill matching, and job priority to maximize your crew's efficiency.",
  },
  {
    icon: Search,
    title: "AI Diagnostics",
    description:
      "Describe symptoms or upload photos, and the AI agent diagnoses plumbing issues with recommended repair procedures.",
  },
  {
    icon: FileText,
    title: "Instant Estimates",
    description:
      "Generate accurate, professional estimates in seconds based on job scope, materials, and local labor rates.",
  },
  {
    icon: ClipboardCheck,
    title: "Permit Management",
    description:
      "Auto-identify required permits, generate applications, and track approval status for every job.",
  },
  {
    icon: Package,
    title: "Inventory Tracking",
    description:
      "Real-time stock levels, automatic reorder alerts, and per-job material allocation to eliminate waste.",
  },
  {
    icon: MessageSquare,
    title: "Customer Communication",
    description:
      "Automated appointment reminders, status updates, and follow-ups that keep customers informed and happy.",
  },
  {
    icon: GraduationCap,
    title: "Tech Training",
    description:
      "AI-generated training guides and code reference for your team, tailored to the jobs you handle most.",
  },
  {
    icon: BookOpen,
    title: "Documentation",
    description:
      "Auto-generate job reports, inspection documents, and compliance records with photos and notes.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto flex items-center justify-between h-16 px-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Wrench className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">PlumbPro AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 gradient-hero opacity-5" />
        <div className="container mx-auto px-4 py-24 md:py-32 relative">
          <div className="max-w-3xl mx-auto text-center animate-fade-in-up">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              AI-Powered Plumbing{" "}
              <span className="text-gradient">Business Management</span>
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              From scheduling and diagnostics to estimates and permits, PlumbPro AI
              handles the business side so you can focus on the work. One intelligent
              platform for your entire operation.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="gap-2 text-base">
                  Get Started Free
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="text-base">
                  Sign In to Your Account
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold mb-3">
              Everything Your Plumbing Business Needs
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Eight powerful modules powered by AI agents that work together to
              streamline every aspect of your operations.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group bg-card rounded-xl border p-6 hover:shadow-lg hover:border-primary/30 transition-all duration-200"
              >
                <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-4">
              Ready to Modernize Your Plumbing Business?
            </h2>
            <p className="text-muted-foreground mb-8">
              Join plumbing companies that are saving hours every week with AI-powered
              management. Set up takes less than 5 minutes.
            </p>
            <Link href="/register">
              <Button size="lg" className="gap-2">
                Start Your Free Trial
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded gradient-primary flex items-center justify-center">
              <Wrench className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-semibold">PlumbPro AI</span>
          </div>
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} PlumbPro AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
