"use client";

import { useState } from "react";
import {
  CalendarDays,
  Clock,
  MapPin,
  User,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const SCHEDULE_DATA = [
  {
    id: "1",
    time: "8:00 AM - 12:00 PM",
    title: "Water heater replacement",
    customer: "Johnson Residence",
    address: "1234 Oak Street",
    tech: "Mike T.",
    status: "in_progress" as const,
  },
  {
    id: "2",
    time: "10:30 AM - 12:00 PM",
    title: "Kitchen drain cleaning",
    customer: "Oakwood Apartments #4B",
    address: "567 Maple Ave, Unit 4B",
    tech: "Sarah K.",
    status: "scheduled" as const,
  },
  {
    id: "3",
    time: "1:00 PM - 5:00 PM",
    title: "Bathroom remodel rough-in",
    customer: "Chen Family",
    address: "890 Pine Dr",
    tech: "Mike T.",
    status: "scheduled" as const,
  },
  {
    id: "4",
    time: "3:30 PM - 5:00 PM",
    title: "Sewer line inspection",
    customer: "Riverside Office Park",
    address: "2200 River Rd, Building C",
    tech: "Dave R.",
    status: "scheduled" as const,
  },
];

const statusStyles = {
  in_progress: "bg-amber-50 text-amber-700 border-amber-200",
  scheduled: "bg-blue-50 text-blue-700 border-blue-200",
  completed: "bg-green-50 text-green-700 border-green-200",
};

export default function SchedulePage() {
  const [currentDate] = useState(new Date());

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Schedule</h1>
          <p className="text-muted-foreground">
            Manage your crew&apos;s daily schedule
          </p>
        </div>
        <Button className="gap-1.5">
          <CalendarDays className="w-4 h-4" />
          Add to Schedule
        </Button>
      </div>

      {/* Date navigation */}
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon">
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <div className="text-center">
          <p className="text-lg font-semibold">
            {currentDate.toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </p>
          <p className="text-sm text-muted-foreground">
            {SCHEDULE_DATA.length} jobs scheduled
          </p>
        </div>
        <Button variant="outline" size="icon">
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>

      {/* Technician columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {["Mike T.", "Sarah K.", "Dave R."].map((tech) => {
          const techJobs = SCHEDULE_DATA.filter((j) => j.tech === tech);
          return (
            <Card key={tech}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="w-4 h-4 text-primary" />
                  </div>
                  {tech}
                  <Badge variant="secondary" className="ml-auto">
                    {techJobs.length} jobs
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {techJobs.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No jobs scheduled
                  </p>
                ) : (
                  techJobs.map((job) => (
                    <div
                      key={job.id}
                      className="p-3 rounded-lg border hover:shadow-sm transition-shadow cursor-pointer"
                    >
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <p className="font-medium text-sm">{job.title}</p>
                        <Badge
                          variant="outline"
                          className={cn("text-[10px] shrink-0", statusStyles[job.status])}
                        >
                          {job.status === "in_progress" ? "In Progress" : "Scheduled"}
                        </Badge>
                      </div>
                      <div className="space-y-1 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {job.time}
                        </div>
                        <div className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {job.customer}
                        </div>
                        <div className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {job.address}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
