"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  MapPin,
  Clock,
  User,
  LayoutGrid,
  List,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Job, JobStatus, JobPriority } from "@/lib/types";

// Placeholder data
const PLACEHOLDER_JOBS: Job[] = [
  {
    id: "j1",
    title: "Water heater replacement",
    description: "Replace 50-gallon gas water heater with new tankless unit",
    status: "in_progress",
    priority: "high",
    customer_id: "c1",
    customer_name: "Johnson Residence",
    address: "1234 Oak Street, Springfield",
    assigned_tech_id: "t1",
    assigned_tech_name: "Mike Torres",
    scheduled_start: "2026-03-14T08:00:00",
    scheduled_end: "2026-03-14T12:00:00",
    estimated_duration_hours: 4,
    actual_duration_hours: null,
    created_at: "2026-03-12T10:00:00",
    updated_at: "2026-03-14T08:15:00",
  },
  {
    id: "j2",
    title: "Kitchen drain cleaning",
    description: "Slow draining kitchen sink, possible grease buildup",
    status: "scheduled",
    priority: "medium",
    customer_id: "c2",
    customer_name: "Oakwood Apartments #4B",
    address: "567 Maple Ave, Unit 4B",
    assigned_tech_id: "t2",
    assigned_tech_name: "Sarah Kim",
    scheduled_start: "2026-03-14T10:30:00",
    scheduled_end: "2026-03-14T12:00:00",
    estimated_duration_hours: 1.5,
    actual_duration_hours: null,
    created_at: "2026-03-13T14:00:00",
    updated_at: "2026-03-13T14:00:00",
  },
  {
    id: "j3",
    title: "Bathroom remodel rough-in",
    description: "New bathroom plumbing rough-in: toilet, vanity, shower",
    status: "scheduled",
    priority: "medium",
    customer_id: "c3",
    customer_name: "Chen Family",
    address: "890 Pine Dr, Springfield",
    assigned_tech_id: "t1",
    assigned_tech_name: "Mike Torres",
    scheduled_start: "2026-03-14T13:00:00",
    scheduled_end: "2026-03-14T17:00:00",
    estimated_duration_hours: 4,
    actual_duration_hours: null,
    created_at: "2026-03-10T09:00:00",
    updated_at: "2026-03-10T09:00:00",
  },
  {
    id: "j4",
    title: "Sewer line inspection",
    description: "Camera inspection of main sewer line, possible root intrusion",
    status: "scheduled",
    priority: "high",
    customer_id: "c4",
    customer_name: "Riverside Office Park",
    address: "2200 River Rd, Building C",
    assigned_tech_id: "t3",
    assigned_tech_name: "Dave Reynolds",
    scheduled_start: "2026-03-14T15:30:00",
    scheduled_end: "2026-03-14T17:00:00",
    estimated_duration_hours: 1.5,
    actual_duration_hours: null,
    created_at: "2026-03-11T11:00:00",
    updated_at: "2026-03-11T11:00:00",
  },
  {
    id: "j5",
    title: "Emergency pipe burst repair",
    description: "Burst pipe in basement, flooding actively",
    status: "completed",
    priority: "emergency",
    customer_id: "c5",
    customer_name: "Martinez Home",
    address: "345 Elm St, Springfield",
    assigned_tech_id: "t1",
    assigned_tech_name: "Mike Torres",
    scheduled_start: "2026-03-13T07:00:00",
    scheduled_end: "2026-03-13T10:00:00",
    estimated_duration_hours: 3,
    actual_duration_hours: 2.5,
    created_at: "2026-03-13T06:30:00",
    updated_at: "2026-03-13T09:30:00",
  },
  {
    id: "j6",
    title: "Garbage disposal installation",
    description: "Install new InSinkErator garbage disposal",
    status: "completed",
    priority: "low",
    customer_id: "c6",
    customer_name: "Pacific Heights HOA",
    address: "100 Pacific Blvd, Unit 12",
    assigned_tech_id: "t2",
    assigned_tech_name: "Sarah Kim",
    scheduled_start: "2026-03-13T14:00:00",
    scheduled_end: "2026-03-13T15:30:00",
    estimated_duration_hours: 1.5,
    actual_duration_hours: 1,
    created_at: "2026-03-12T10:00:00",
    updated_at: "2026-03-13T15:00:00",
  },
  {
    id: "j7",
    title: "Fixture installation - master bath",
    description: "Install new faucet, showerhead, and toilet",
    status: "pending",
    priority: "low",
    customer_id: "c7",
    customer_name: "Williams Residence",
    address: "789 Birch Lane",
    assigned_tech_id: null,
    assigned_tech_name: null,
    scheduled_start: null,
    scheduled_end: null,
    estimated_duration_hours: 3,
    actual_duration_hours: null,
    created_at: "2026-03-14T09:00:00",
    updated_at: "2026-03-14T09:00:00",
  },
];

const statusColors: Record<JobStatus, string> = {
  pending: "bg-gray-100 text-gray-700 border-gray-200",
  scheduled: "bg-blue-50 text-blue-700 border-blue-200",
  in_progress: "bg-amber-50 text-amber-700 border-amber-200",
  completed: "bg-green-50 text-green-700 border-green-200",
  cancelled: "bg-red-50 text-red-700 border-red-200",
};

const priorityColors: Record<JobPriority, string> = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-amber-100 text-amber-700",
  emergency: "bg-red-100 text-red-700",
};

const statusLabels: Record<JobStatus, string> = {
  pending: "Pending",
  scheduled: "Scheduled",
  in_progress: "In Progress",
  completed: "Completed",
  cancelled: "Cancelled",
};

export default function JobsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");

  const filteredJobs = useMemo(() => {
    return PLACEHOLDER_JOBS.filter((job) => {
      if (statusFilter !== "all" && job.status !== statusFilter) return false;
      if (priorityFilter !== "all" && job.priority !== priorityFilter)
        return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          job.title.toLowerCase().includes(q) ||
          job.customer_name.toLowerCase().includes(q) ||
          job.address.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [search, statusFilter, priorityFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Jobs</h1>
          <p className="text-muted-foreground">
            Manage all your plumbing jobs
          </p>
        </div>
        <Button className="gap-1.5">
          <Plus className="w-4 h-4" />
          New Job
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search jobs, customers, addresses..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="scheduled">Scheduled</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
        >
          <option value="all">All Priorities</option>
          <option value="emergency">Emergency</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <div className="flex border rounded-md">
          <button
            className={cn(
              "px-3 py-2 transition-colors",
              viewMode === "list" ? "bg-muted" : "hover:bg-muted/50"
            )}
            onClick={() => setViewMode("list")}
          >
            <List className="w-4 h-4" />
          </button>
          <button
            className={cn(
              "px-3 py-2 transition-colors",
              viewMode === "grid" ? "bg-muted" : "hover:bg-muted/50"
            )}
            onClick={() => setViewMode("grid")}
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Results count */}
      <p className="text-sm text-muted-foreground">
        {filteredJobs.length} job{filteredJobs.length !== 1 ? "s" : ""}
      </p>

      {/* Job list / grid */}
      <div
        className={cn(
          viewMode === "grid"
            ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
            : "space-y-3"
        )}
      >
        {filteredJobs.map((job) => (
          <Link key={job.id} href={`/dashboard/jobs/${job.id}`}>
            <Card className="hover:shadow-md hover:border-primary/30 transition-all cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold truncate">{job.title}</h3>
                  <div className="flex gap-1.5 shrink-0">
                    <span
                      className={cn(
                        "text-xs px-2 py-0.5 rounded-full font-medium",
                        priorityColors[job.priority]
                      )}
                    >
                      {job.priority}
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5" />
                    <span className="truncate">{job.customer_name}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" />
                    <span className="truncate">{job.address}</span>
                  </div>
                  {job.scheduled_start && (
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>
                        {new Date(job.scheduled_start).toLocaleString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between mt-3 pt-3 border-t">
                  <Badge
                    variant="outline"
                    className={cn("text-xs", statusColors[job.status])}
                  >
                    {statusLabels[job.status]}
                  </Badge>
                  {job.assigned_tech_name && (
                    <span className="text-xs text-muted-foreground">
                      {job.assigned_tech_name}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {filteredJobs.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg font-medium">No jobs found</p>
          <p className="text-sm mt-1">
            Try adjusting your filters or create a new job.
          </p>
        </div>
      )}
    </div>
  );
}
