"use client";

import { useState, useMemo } from "react";
import { Plus, Search, FileText, DollarSign, Send, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

const ESTIMATES = [
  {
    id: "e1",
    number: "EST-1042",
    customer: "Oakwood Property Mgmt",
    job: "Multi-unit drain cleaning",
    total: 3450,
    status: "sent" as const,
    created: "2026-03-13",
    validUntil: "2026-03-27",
  },
  {
    id: "e2",
    number: "EST-1041",
    customer: "Johnson Residence",
    job: "Water heater replacement",
    total: 4200,
    status: "accepted" as const,
    created: "2026-03-12",
    validUntil: "2026-03-26",
  },
  {
    id: "e3",
    number: "EST-1040",
    customer: "Chen Family",
    job: "Bathroom remodel rough-in",
    total: 8750,
    status: "accepted" as const,
    created: "2026-03-10",
    validUntil: "2026-03-24",
  },
  {
    id: "e4",
    number: "EST-1039",
    customer: "Pacific Heights HOA",
    job: "Common area pipe replacement",
    total: 12300,
    status: "sent" as const,
    created: "2026-03-09",
    validUntil: "2026-03-23",
  },
  {
    id: "e5",
    number: "EST-1038",
    customer: "Williams Residence",
    job: "Fixture installation",
    total: 1850,
    status: "draft" as const,
    created: "2026-03-14",
    validUntil: "2026-03-28",
  },
  {
    id: "e6",
    number: "EST-1037",
    customer: "Downtown Diner",
    job: "Grease trap replacement",
    total: 2200,
    status: "declined" as const,
    created: "2026-03-07",
    validUntil: "2026-03-21",
  },
];

const statusConfig = {
  draft: { label: "Draft", color: "bg-gray-100 text-gray-700", icon: FileText },
  sent: { label: "Sent", color: "bg-blue-100 text-blue-700", icon: Send },
  accepted: { label: "Accepted", color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  declined: { label: "Declined", color: "bg-red-100 text-red-700", icon: XCircle },
};

export default function EstimatesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = useMemo(() => {
    return ESTIMATES.filter((e) => {
      if (statusFilter !== "all" && e.status !== statusFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          e.number.toLowerCase().includes(q) ||
          e.customer.toLowerCase().includes(q) ||
          e.job.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [search, statusFilter]);

  const totalValue = filtered.reduce((sum, e) => sum + e.total, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Estimates</h1>
          <p className="text-muted-foreground">Create and manage customer estimates</p>
        </div>
        <Button className="gap-1.5">
          <Plus className="w-4 h-4" />
          New Estimate
        </Button>
      </div>

      {/* Summary */}
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-1.5">
          <DollarSign className="w-4 h-4 text-muted-foreground" />
          <span className="text-muted-foreground">Total value:</span>
          <span className="font-semibold">{formatCurrency(totalValue)}</span>
        </div>
        <span className="text-muted-foreground">{filtered.length} estimates</span>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search estimates..."
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
          <option value="draft">Draft</option>
          <option value="sent">Sent</option>
          <option value="accepted">Accepted</option>
          <option value="declined">Declined</option>
        </select>
      </div>

      {/* List */}
      <div className="space-y-3">
        {filtered.map((est) => {
          const cfg = statusConfig[est.status];
          return (
            <Card key={est.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{est.number}</p>
                        <Badge className={cn("text-xs", cfg.color)}>
                          {cfg.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {est.customer} &mdash; {est.job}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold">{formatCurrency(est.total)}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(est.created)}
                    </p>
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
