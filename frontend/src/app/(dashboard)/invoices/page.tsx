"use client";

import { useState, useMemo } from "react";
import { Plus, Search, Receipt, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

const INVOICES = [
  { id: "1", number: "INV-2048", customer: "Martinez Home", job: "Emergency pipe burst repair", total: 1850, status: "paid" as const, date: "2026-03-13", dueDate: "2026-03-27" },
  { id: "2", number: "INV-2047", customer: "Pacific Heights HOA", job: "Garbage disposal installation", total: 425, status: "paid" as const, date: "2026-03-13", dueDate: "2026-03-27" },
  { id: "3", number: "INV-2046", customer: "Oakwood Apartments", job: "Unit 2A faucet repair", total: 275, status: "sent" as const, date: "2026-03-12", dueDate: "2026-03-26" },
  { id: "4", number: "INV-2045", customer: "Riverside Office Park", job: "Restroom maintenance", total: 1200, status: "overdue" as const, date: "2026-03-01", dueDate: "2026-03-08" },
  { id: "5", number: "INV-2044", customer: "Downtown Diner", job: "Kitchen plumbing repair", total: 680, status: "sent" as const, date: "2026-03-10", dueDate: "2026-03-24" },
];

const statusConfig = {
  draft: { label: "Draft", color: "bg-gray-100 text-gray-700" },
  sent: { label: "Sent", color: "bg-blue-100 text-blue-700" },
  paid: { label: "Paid", color: "bg-green-100 text-green-700" },
  overdue: { label: "Overdue", color: "bg-red-100 text-red-700" },
};

export default function InvoicesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = useMemo(() => {
    return INVOICES.filter((inv) => {
      if (statusFilter !== "all" && inv.status !== statusFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return inv.number.toLowerCase().includes(q) || inv.customer.toLowerCase().includes(q);
      }
      return true;
    });
  }, [search, statusFilter]);

  const totalOutstanding = INVOICES.filter((i) => i.status === "sent" || i.status === "overdue").reduce((s, i) => s + i.total, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Invoices</h1>
          <p className="text-muted-foreground">Track payments and outstanding invoices</p>
        </div>
        <Button className="gap-1.5">
          <Plus className="w-4 h-4" />
          New Invoice
        </Button>
      </div>

      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-1.5">
          <DollarSign className="w-4 h-4 text-amber-500" />
          <span className="text-muted-foreground">Outstanding:</span>
          <span className="font-semibold text-amber-600">{formatCurrency(totalOutstanding)}</span>
        </div>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search invoices..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="sent">Sent</option>
          <option value="paid">Paid</option>
          <option value="overdue">Overdue</option>
        </select>
      </div>

      <div className="space-y-3">
        {filtered.map((inv) => {
          const cfg = statusConfig[inv.status];
          return (
            <Card key={inv.id} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Receipt className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{inv.number}</p>
                        <Badge className={cn("text-xs", cfg.color)}>{cfg.label}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{inv.customer} &mdash; {inv.job}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-semibold">{formatCurrency(inv.total)}</p>
                    <p className="text-xs text-muted-foreground">Due {formatDate(inv.dueDate)}</p>
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
