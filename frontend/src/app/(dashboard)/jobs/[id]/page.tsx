"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  MapPin,
  Clock,
  User,
  FileText,
  ClipboardCheck,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import ChatPanel from "@/components/chat/ChatPanel";
import { cn } from "@/lib/utils";
import type { JobStatus, JobPriority } from "@/lib/types";

// Placeholder job detail
const JOB = {
  id: "j1",
  title: "Water heater replacement",
  description:
    "Replace existing 50-gallon gas water heater with new Rinnai RU199iN tankless unit. Includes gas line modification and new venting.",
  status: "in_progress" as JobStatus,
  priority: "high" as JobPriority,
  customer_name: "Johnson Residence",
  customer_phone: "(555) 123-4567",
  customer_email: "johnson@email.com",
  address: "1234 Oak Street, Springfield, IL 62701",
  assigned_tech_name: "Mike Torres",
  scheduled_start: "2026-03-14T08:00:00",
  scheduled_end: "2026-03-14T12:00:00",
  estimated_duration_hours: 4,
  created_at: "2026-03-12T10:00:00",
};

const timeline = [
  {
    time: "Mar 12, 10:00 AM",
    event: "Job created",
    detail: "Created from customer request via phone call",
  },
  {
    time: "Mar 12, 10:15 AM",
    event: "Estimate sent",
    detail: "Estimate #1038 sent to customer — $4,200",
  },
  {
    time: "Mar 12, 2:30 PM",
    event: "Estimate accepted",
    detail: "Customer approved estimate via email",
  },
  {
    time: "Mar 13, 9:00 AM",
    event: "Permit applied",
    detail: "Plumbing permit application submitted to city",
  },
  {
    time: "Mar 14, 7:45 AM",
    event: "Job started",
    detail: "Mike Torres checked in on site",
  },
];

const linkedItems = [
  {
    type: "Estimate",
    label: "Estimate #1038",
    status: "Accepted",
    icon: FileText,
  },
  {
    type: "Permit",
    label: "Plumbing Permit",
    status: "Applied",
    icon: ClipboardCheck,
  },
];

const statusColors: Record<JobStatus, string> = {
  pending: "bg-gray-100 text-gray-700",
  scheduled: "bg-blue-50 text-blue-700",
  in_progress: "bg-amber-50 text-amber-700",
  completed: "bg-green-50 text-green-700",
  cancelled: "bg-red-50 text-red-700",
};

const statusTransitions: Record<JobStatus, { label: string; next: JobStatus }[]> = {
  pending: [{ label: "Schedule", next: "scheduled" }],
  scheduled: [
    { label: "Start Job", next: "in_progress" },
    { label: "Cancel", next: "cancelled" },
  ],
  in_progress: [{ label: "Complete Job", next: "completed" }],
  completed: [],
  cancelled: [],
};

export default function JobDetailPage() {
  const [status, setStatus] = useState<JobStatus>(JOB.status);

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/dashboard/jobs"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Jobs
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job header */}
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-2xl font-bold">{JOB.title}</h1>
                    <Badge
                      className={cn(
                        "text-xs",
                        statusColors[status]
                      )}
                    >
                      {status.replace("_", " ")}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground mb-4">
                    {JOB.description}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-muted-foreground" />
                      <div>
                        <span className="font-medium">{JOB.customer_name}</span>
                        <p className="text-muted-foreground text-xs">
                          {JOB.customer_phone}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-muted-foreground" />
                      <span>{JOB.address}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span>
                        {new Date(JOB.scheduled_start).toLocaleString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "numeric",
                          minute: "2-digit",
                        })}{" "}
                        -{" "}
                        {new Date(JOB.scheduled_end).toLocaleString("en-US", {
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-muted-foreground" />
                      <span>Tech: {JOB.assigned_tech_name}</span>
                    </div>
                  </div>
                </div>

                <Badge
                  className={cn(
                    "text-xs shrink-0",
                    JOB.priority === "emergency"
                      ? "bg-red-100 text-red-700"
                      : JOB.priority === "high"
                      ? "bg-amber-100 text-amber-700"
                      : "bg-blue-100 text-blue-700"
                  )}
                >
                  {JOB.priority} priority
                </Badge>
              </div>

              {/* Status transitions */}
              {statusTransitions[status].length > 0 && (
                <div className="flex gap-2 mt-6 pt-4 border-t">
                  {statusTransitions[status].map((t) => (
                    <Button
                      key={t.next}
                      variant={t.next === "cancelled" ? "outline" : "default"}
                      size="sm"
                      onClick={() => setStatus(t.next)}
                    >
                      {t.label}
                    </Button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {timeline.map((entry, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-2.5 h-2.5 rounded-full bg-primary mt-1.5" />
                      {i < timeline.length - 1 && (
                        <div className="w-px flex-1 bg-border mt-1" />
                      )}
                    </div>
                    <div className="pb-4">
                      <p className="text-xs text-muted-foreground">
                        {entry.time}
                      </p>
                      <p className="font-medium text-sm">{entry.event}</p>
                      <p className="text-sm text-muted-foreground">
                        {entry.detail}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Linked items */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Linked Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {linkedItems.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="w-4 h-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium text-sm">{item.label}</p>
                        <p className="text-xs text-muted-foreground">
                          {item.type}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {item.status}
                      </Badge>
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chat Panel */}
        <div className="lg:col-span-1">
          <div className="sticky top-20">
            <ChatPanel
              sessionId={`job-${JOB.id}`}
              onEvent={(event) => {
                console.log("Agent event:", event);
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
