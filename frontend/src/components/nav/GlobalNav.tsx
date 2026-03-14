"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import {
  Wrench,
  LayoutDashboard,
  CalendarDays,
  Briefcase,
  Search,
  FileText,
  Receipt,
  Package,
  ClipboardCheck,
  Users,
  GraduationCap,
  BarChart3,
  Settings,
  CreditCard,
  LogOut,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState, useRef, useEffect } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/schedule", label: "Schedule", icon: CalendarDays },
  { href: "/dashboard/jobs", label: "Jobs", icon: Briefcase },
  { href: "/dashboard/diagnostics", label: "Diagnostics", icon: Search },
  { href: "/dashboard/estimates", label: "Estimates", icon: FileText },
  { href: "/dashboard/invoices", label: "Invoices", icon: Receipt },
  { href: "/dashboard/inventory", label: "Inventory", icon: Package },
  { href: "/dashboard/permits", label: "Permits", icon: ClipboardCheck },
  { href: "/dashboard/customers", label: "Customers", icon: Users },
  { href: "/dashboard/training", label: "Training", icon: GraduationCap },
  { href: "/dashboard/reports", label: "Reports", icon: BarChart3 },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
];

export default function GlobalNav() {
  const pathname = usePathname();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b bg-card/95 backdrop-blur-sm">
      <div className="flex items-center justify-between h-14 px-4">
        {/* Branding */}
        <Link href="/dashboard" className="flex items-center gap-2 shrink-0">
          <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
            <Wrench className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg hidden sm:inline">PlumbPro AI</span>
        </Link>

        {/* Nav Links - horizontal scroll on mobile */}
        <nav className="flex-1 mx-4 overflow-x-auto scrollbar-hide">
          <ul className="flex items-center gap-1 min-w-max">
            {navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-sm font-medium transition-colors whitespace-nowrap",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="hidden lg:inline">{item.label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User menu */}
        <div className="relative shrink-0" ref={menuRef}>
          <Button
            variant="ghost"
            size="sm"
            className="gap-1"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
          >
            <div className="w-7 h-7 rounded-full gradient-primary flex items-center justify-center text-white text-xs font-bold">
              P
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          </Button>

          {userMenuOpen && (
            <div className="absolute right-0 top-full mt-1 w-48 bg-card rounded-lg border shadow-lg py-1 z-50">
              <Link
                href="/dashboard/settings"
                className="block px-4 py-2 text-sm hover:bg-muted transition-colors"
                onClick={() => setUserMenuOpen(false)}
              >
                <Settings className="w-4 h-4 inline mr-2" />
                Settings
              </Link>
              <button
                onClick={() => signOut({ callbackUrl: "/" })}
                className="w-full text-left px-4 py-2 text-sm hover:bg-muted transition-colors text-destructive"
              >
                <LogOut className="w-4 h-4 inline mr-2" />
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
