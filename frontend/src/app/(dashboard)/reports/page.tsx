"use client";

import { useState, useMemo } from "react";
import {
  Search,
  FileText,
  Download,
  ClipboardCheck,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatDate } from "@/lib/utils";

const REPORTS = [
  {
    id: "r1",
    title: "Water Heater Replacement - Completion Report",
    customer: "Johnson Residence",
    address: "1234 Oak Street",
    type: "completion" as const,
    date: "2026-03-13",
    tech: "Mike Torres",
    jobId: "j1",
  },
  {
    id: "r2",
    title: "Emergency Pipe Burst - Completion Report",
    customer: "Martinez Home",
    address: "345 Elm St",
    type: "completion" as const,
    date: "2026-03-13",
    tech: "Mike Torres",
    jobId: "j5",
  },
  {
    id: "r3",
    title: "Sewer Line Camera Inspection",
    customer: "Riverside Office Park",
    address: "2200 River Rd, Building C",
    type: "inspection" as const,
    date: "2026-03-12",
    tech: "Dave Reynolds",
    jobId: "j4",
  },
  {
    id: "r4",
    title: "Garbage Disposal Installation - Completion Report",
    customer: "Pacific Heights HOA",
    address: "100 Pacific Blvd, Unit 12",
    type: "completion" as const,
    date: "2026-03-11",
    tech: "Sarah Kim",
    jobId: "j6",
  },
  {
    id: "r5",
    title: "Bathroom Remodel - Pre-Inspection Report",
    customer: "Chen Family",
    address: "890 Pine Dr",
    type: "inspection" as const,
    date: "2026-03-10",
    tech: "Mike Torres",
    jobId: "j3",
  },
  {
    id: "r6",
    title: "Annual Backflow Test Report",
    customer: "Oakwood Property Mgmt",
    address: "567 Maple Ave",
    type: "inspection" as const,
    date: "2026-03-08",
    tech: "Sarah Kim",
    jobId: null,
  },
  {
    id: "r7",
    title: "Multi-Unit Drain Cleaning - Completion Report",
    customer: "Oakwood Property Mgmt",
    address: "567 Maple Ave",
    type: "completion" as const,
    date: "2026-03-07",
    tech: "Dave Reynolds",
    jobId: null,
  },
];

const typeConfig = {
  completion: { label: "Completion", color: "bg-green-100 text-green-700" },
  inspection: { label: "Inspection", color: "bg-blue-100 text-blue-700" },
};

export default function ReportsPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const filtered = useMemo(() => {
    return REPORTS.filter((r) => {
      if (typeFilter !== "all" && r.type !== typeFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          r.title.toLowerCase().includes(q) ||
          r.customer.toLowerCase().includes(q) ||
          r.address.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [search, typeFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-muted-foreground">
            Job completion and inspection reports
          </p>
        </div>
        <Button className="gap-1.5">
          <FileText className="w-4 h-4" />
          Generate Report
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by address, customer, or title..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="all">All Types</option>
          <option value="completion">Completion</option>
          <option value="inspection">Inspection</option>
        </select>
      </div>

      <p className="text-sm text-muted-foreground">
        {filtered.length} report{filtered.length !== 1 ? "s" : ""}
      </p>

      {/* List */}
      <div className="space-y-3">
        {filtered.map((report) => {
          const cfg = typeConfig[report.type];
          return (
            <Card key={report.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      {report.type === "inspection" ? (
                        <ClipboardCheck className="w-5 h-5 text-primary" />
                      ) : (
                        <FileText className="w-5 h-5 text-primary" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{report.title}</p>
                        <Badge className={cn("text-xs", cfg.color)}>
                          {cfg.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {report.customer} &mdash; {report.address}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right text-sm">
                      <p className="text-xs text-muted-foreground">{report.tech}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(report.date)}</p>
                    </div>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg font-medium">No reports found</p>
          <p className="text-sm mt-1">Try adjusting your search or filters.</p>
        </div>
      )}
    </div>
  );
}
