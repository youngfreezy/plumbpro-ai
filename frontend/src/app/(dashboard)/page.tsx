"use client";

import Link from "next/link";
import {
  CalendarDays,
  Briefcase,
  Package,
  ClipboardCheck,
  Plus,
  FileText,
  Search,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Users,
  ArrowRight,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";
import type { ActivityItem } from "@/lib/types";

// Placeholder data
const todaySchedule = [
  {
    id: "1",
    time: "8:00 AM",
    title: "Water heater replacement",
    customer: "Johnson Residence",
    tech: "Mike T.",
  },
  {
    id: "2",
    time: "10:30 AM",
    title: "Kitchen drain cleaning",
    customer: "Oakwood Apartments #4B",
    tech: "Sarah K.",
  },
  {
    id: "3",
    time: "1:00 PM",
    title: "Bathroom remodel rough-in",
    customer: "Chen Family",
    tech: "Mike T.",
  },
  {
    id: "4",
    time: "3:30 PM",
    title: "Sewer line inspection",
    customer: "Riverside Office Park",
    tech: "Dave R.",
  },
];

const recentActivity: (ActivityItem & { icon: typeof CheckCircle2 })[] = [
  {
    id: "1",
    type: "job_completed",
    message: "Garbage disposal install completed at Martinez home",
    timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
    icon: CheckCircle2,
  },
  {
    id: "2",
    type: "estimate_sent",
    message: "Estimate #1042 sent to Oakwood Property Mgmt — $3,450",
    timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
    icon: FileText,
  },
  {
    id: "3",
    type: "permit_approved",
    message: "Permit approved for 221B Baker St bathroom remodel",
    timestamp: new Date(Date.now() - 5 * 3600000).toISOString(),
    icon: ClipboardCheck,
  },
  {
    id: "4",
    type: "inventory_low",
    message: "Low stock alert: 3/4\" copper fittings (4 remaining)",
    timestamp: new Date(Date.now() - 8 * 3600000).toISOString(),
    icon: AlertTriangle,
  },
  {
    id: "5",
    type: "customer_added",
    message: "New customer: Pacific Heights HOA",
    timestamp: new Date(Date.now() - 24 * 3600000).toISOString(),
    icon: Users,
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/jobs">
            <Button size="sm" className="gap-1.5">
              <Plus className="w-4 h-4" />
              New Job
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Today&apos;s Jobs</p>
                <p className="text-3xl font-bold mt-1">4</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <CalendarDays className="w-5 h-5 text-primary" />
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              2 in progress, 2 upcoming
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Jobs</p>
                <p className="text-3xl font-bold mt-1">12</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Briefcase className="w-5 h-5 text-blue-500" />
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              3 scheduled for this week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Low Stock Items</p>
                <p className="text-3xl font-bold mt-1">5</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Package className="w-5 h-5 text-amber-500" />
              </div>
            </div>
            <p className="text-xs text-amber-600 mt-2 font-medium">
              2 items need immediate reorder
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending Permits</p>
                <p className="text-3xl font-bold mt-1">3</p>
              </div>
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                <ClipboardCheck className="w-5 h-5 text-purple-500" />
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              1 approved today
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Schedule */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Today&apos;s Schedule</CardTitle>
              <Link href="/dashboard/schedule">
                <Button variant="ghost" size="sm" className="gap-1 text-primary">
                  View all <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {todaySchedule.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center gap-4 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                >
                  <div className="text-sm font-medium text-primary w-20 shrink-0">
                    <Clock className="w-3.5 h-3.5 inline mr-1" />
                    {item.time}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{item.title}</p>
                    <p className="text-sm text-muted-foreground truncate">
                      {item.customer}
                    </p>
                  </div>
                  <Badge variant="secondary" className="shrink-0">
                    {item.tech}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((item) => (
                <div key={item.id} className="flex gap-3">
                  <item.icon
                    className={`w-4 h-4 mt-0.5 shrink-0 ${
                      item.type === "inventory_low"
                        ? "text-amber-500"
                        : item.type === "job_completed"
                        ? "text-green-500"
                        : "text-primary"
                    }`}
                  />
                  <div className="min-w-0">
                    <p className="text-sm leading-snug">{item.message}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {formatRelativeTime(item.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Link href="/dashboard/jobs">
              <Button variant="outline" className="gap-2">
                <Plus className="w-4 h-4" />
                New Job
              </Button>
            </Link>
            <Link href="/dashboard/estimates">
              <Button variant="outline" className="gap-2">
                <FileText className="w-4 h-4" />
                New Estimate
              </Button>
            </Link>
            <Link href="/dashboard/diagnostics">
              <Button variant="outline" className="gap-2">
                <Search className="w-4 h-4" />
                Diagnose Issue
              </Button>
            </Link>
            <Link href="/dashboard/customers">
              <Button variant="outline" className="gap-2">
                <Users className="w-4 h-4" />
                Add Customer
              </Button>
            </Link>
            <Link href="/dashboard/inventory">
              <Button variant="outline" className="gap-2">
                <Package className="w-4 h-4" />
                Check Inventory
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
