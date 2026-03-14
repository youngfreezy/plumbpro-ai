"use client";

import { useState, useMemo } from "react";
import { Search, Package, AlertTriangle, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatCurrency } from "@/lib/utils";

const INVENTORY = [
  { id: "1", name: '3/4" Copper Fittings', sku: "CPR-750", category: "Fittings", quantity: 4, minQuantity: 20, unitPrice: 3.50, supplier: "Ferguson Supply" },
  { id: "2", name: '1/2" PEX Tubing (100ft)', sku: "PEX-500", category: "Pipe", quantity: 8, minQuantity: 5, unitPrice: 45.00, supplier: "Ferguson Supply" },
  { id: "3", name: "Wax Ring Seals", sku: "WRS-100", category: "Seals", quantity: 3, minQuantity: 10, unitPrice: 4.25, supplier: "HD Supply" },
  { id: "4", name: '1/2" Ball Valves', sku: "BLV-500", category: "Valves", quantity: 12, minQuantity: 8, unitPrice: 8.75, supplier: "Ferguson Supply" },
  { id: "5", name: "P-Trap 1-1/2\" PVC", sku: "PTP-150", category: "Fittings", quantity: 6, minQuantity: 10, unitPrice: 5.50, supplier: "HD Supply" },
  { id: "6", name: "Teflon Tape (10-pack)", sku: "TFT-010", category: "Supplies", quantity: 2, minQuantity: 5, unitPrice: 12.00, supplier: "HD Supply" },
  { id: "7", name: "Water Heater Anode Rod", sku: "ANR-001", category: "Parts", quantity: 15, minQuantity: 5, unitPrice: 28.00, supplier: "Rinnai Direct" },
  { id: "8", name: "Drain Snake 25ft", sku: "DSN-025", category: "Tools", quantity: 3, minQuantity: 2, unitPrice: 65.00, supplier: "Ridgid" },
];

export default function InventoryPage() {
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [showLowOnly, setShowLowOnly] = useState(false);

  const categories = useMemo(() => Array.from(new Set(INVENTORY.map((i) => i.category))), []);

  const filtered = useMemo(() => {
    return INVENTORY.filter((item) => {
      if (categoryFilter !== "all" && item.category !== categoryFilter) return false;
      if (showLowOnly && item.quantity >= item.minQuantity) return false;
      if (search) {
        const q = search.toLowerCase();
        return item.name.toLowerCase().includes(q) || item.sku.toLowerCase().includes(q);
      }
      return true;
    });
  }, [search, categoryFilter, showLowOnly]);

  const lowStockCount = INVENTORY.filter((i) => i.quantity < i.minQuantity).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Inventory</h1>
          <p className="text-muted-foreground">Track stock levels and reorder supplies</p>
        </div>
        <Button className="gap-1.5">
          <Plus className="w-4 h-4" />
          Add Item
        </Button>
      </div>

      {lowStockCount > 0 && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span className="font-medium">{lowStockCount} items below minimum stock level</span>
          <Button variant="outline" size="sm" className="ml-auto text-amber-700 border-amber-300 hover:bg-amber-100" onClick={() => setShowLowOnly(!showLowOnly)}>
            {showLowOnly ? "Show All" : "Show Low Stock"}
          </Button>
        </div>
      )}

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search inventory..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="all">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              <th className="pb-3 font-medium text-muted-foreground">Item</th>
              <th className="pb-3 font-medium text-muted-foreground">SKU</th>
              <th className="pb-3 font-medium text-muted-foreground">Category</th>
              <th className="pb-3 font-medium text-muted-foreground text-right">Qty</th>
              <th className="pb-3 font-medium text-muted-foreground text-right">Min</th>
              <th className="pb-3 font-medium text-muted-foreground text-right">Unit Price</th>
              <th className="pb-3 font-medium text-muted-foreground">Supplier</th>
              <th className="pb-3 font-medium text-muted-foreground">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => {
              const isLow = item.quantity < item.minQuantity;
              return (
                <tr key={item.id} className="border-b hover:bg-muted/50 transition-colors cursor-pointer">
                  <td className="py-3 font-medium">{item.name}</td>
                  <td className="py-3 text-muted-foreground">{item.sku}</td>
                  <td className="py-3">
                    <Badge variant="secondary" className="text-xs">{item.category}</Badge>
                  </td>
                  <td className={cn("py-3 text-right font-medium", isLow && "text-red-600")}>{item.quantity}</td>
                  <td className="py-3 text-right text-muted-foreground">{item.minQuantity}</td>
                  <td className="py-3 text-right">{formatCurrency(item.unitPrice)}</td>
                  <td className="py-3 text-muted-foreground">{item.supplier}</td>
                  <td className="py-3">
                    {isLow ? (
                      <Badge className="text-xs bg-red-100 text-red-700">Low Stock</Badge>
                    ) : (
                      <Badge className="text-xs bg-green-100 text-green-700">In Stock</Badge>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
