"use client";

import { useState, useMemo } from "react";
import { Search, ClipboardCheck, Plus, Clock, CheckCircle2, AlertCircle, FileX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatDate } from "@/lib/utils";

const PERMITS = [
  { id: "1", type: "Plumbing Permit", job: "Water heater replacement", address: "1234 Oak St", status: "applied" as const, appliedDate: "2026-03-13", number: null },
  { id: "2", type: "Plumbing Permit", job: "Bathroom remodel rough-in", address: "890 Pine Dr", status: "approved" as const, appliedDate: "2026-03-08", number: "PRM-2026-4521" },
  { id: "3", type: "Building Permit", job: "Bathroom remodel rough-in", address: "890 Pine Dr", status: "applied" as const, appliedDate: "2026-03-09", number: null },
  { id: "4", type: "Sewer Permit", job: "Sewer line repair", address: "456 Elm Ave", status: "approved" as const, appliedDate: "2026-03-01", number: "SWR-2026-892" },
  { id: "5", type: "Plumbing Permit", job: "Common area pipe replacement", address: "100 Pacific Blvd", status: "required" as const, appliedDate: null, number: null },
  { id: "6", type: "Hot Work Permit", job: "Boiler installation", address: "300 Industrial Way", status: "rejected" as const, appliedDate: "2026-03-05", number: null },
];

const statusConfig = {
  required: { label: "Required", color: "bg-amber-100 text-amber-700", icon: AlertCircle },
  applied: { label: "Applied", color: "bg-blue-100 text-blue-700", icon: Clock },
  approved: { label: "Approved", color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-700", icon: FileX },
  not_required: { label: "Not Required", color: "bg-gray-100 text-gray-700", icon: ClipboardCheck },
};

export default function PermitsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = useMemo(() => {
    return PERMITS.filter((p) => {
      if (statusFilter !== "all" && p.status !== statusFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return p.type.toLowerCase().includes(q) || p.job.toLowerCase().includes(q) || p.address.toLowerCase().includes(q);
      }
      return true;
    });
  }, [search, statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Permits</h1>
          <p className="text-muted-foreground">Track permit applications and approvals</p>
        </div>
        <Button className="gap-1.5">
          <Plus className="w-4 h-4" />
          New Permit
        </Button>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search permits..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="required">Required</option>
          <option value="applied">Applied</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="space-y-3">
        {filtered.map((permit) => {
          const cfg = statusConfig[permit.status];
          const StatusIcon = cfg.icon;
          return (
            <Card key={permit.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <StatusIcon className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{permit.type}</p>
                        <Badge className={cn("text-xs", cfg.color)}>{cfg.label}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{permit.job} &mdash; {permit.address}</p>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    {permit.number && <p className="font-mono text-xs">{permit.number}</p>}
                    {permit.appliedDate && <p className="text-xs text-muted-foreground">Applied {formatDate(permit.appliedDate)}</p>}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
