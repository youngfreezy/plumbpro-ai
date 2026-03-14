"use client";

import { useState, useMemo } from "react";
import { Search, Users, Plus, Phone, Mail, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const CUSTOMERS = [
  { id: "1", name: "Johnson Residence", email: "johnson@email.com", phone: "(555) 123-4567", address: "1234 Oak Street, Springfield, IL 62701", jobs: 3, type: "residential" as const },
  { id: "2", name: "Oakwood Property Mgmt", email: "maint@oakwoodpm.com", phone: "(555) 234-5678", address: "567 Maple Ave, Springfield, IL 62702", jobs: 8, type: "commercial" as const },
  { id: "3", name: "Chen Family", email: "chen@email.com", phone: "(555) 345-6789", address: "890 Pine Dr, Springfield, IL 62701", jobs: 1, type: "residential" as const },
  { id: "4", name: "Riverside Office Park", email: "facilities@riverside.com", phone: "(555) 456-7890", address: "2200 River Rd, Building C", jobs: 5, type: "commercial" as const },
  { id: "5", name: "Martinez Home", email: "martinez@email.com", phone: "(555) 567-8901", address: "345 Elm St, Springfield, IL 62701", jobs: 2, type: "residential" as const },
  { id: "6", name: "Pacific Heights HOA", email: "board@pacifichoa.org", phone: "(555) 678-9012", address: "100 Pacific Blvd, Springfield, IL 62703", jobs: 4, type: "commercial" as const },
  { id: "7", name: "Williams Residence", email: "rwilliams@email.com", phone: "(555) 789-0123", address: "789 Birch Lane, Springfield, IL 62701", jobs: 1, type: "residential" as const },
  { id: "8", name: "Downtown Diner", email: "owner@downtowndiner.com", phone: "(555) 890-1234", address: "50 Main St, Springfield, IL 62701", jobs: 2, type: "commercial" as const },
];

export default function CustomersPage() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const filtered = useMemo(() => {
    return CUSTOMERS.filter((c) => {
      if (typeFilter !== "all" && c.type !== typeFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return c.name.toLowerCase().includes(q) || c.email.toLowerCase().includes(q) || c.phone.includes(q);
      }
      return true;
    });
  }, [search, typeFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Customers</h1>
          <p className="text-muted-foreground">{CUSTOMERS.length} customers in your database</p>
        </div>
        <Button className="gap-1.5">
          <Plus className="w-4 h-4" />
          Add Customer
        </Button>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search customers..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="all">All Types</option>
          <option value="residential">Residential</option>
          <option value="commercial">Commercial</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map((customer) => (
          <Card key={customer.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Users className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold">{customer.name}</p>
                    <Badge variant="secondary" className="text-xs mt-0.5 capitalize">{customer.type}</Badge>
                  </div>
                </div>
                <span className="text-sm text-muted-foreground">{customer.jobs} jobs</span>
              </div>
              <div className="space-y-1.5 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Mail className="w-3.5 h-3.5" />
                  <span>{customer.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5" />
                  <span>{customer.phone}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin className="w-3.5 h-3.5" />
                  <span className="truncate">{customer.address}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
