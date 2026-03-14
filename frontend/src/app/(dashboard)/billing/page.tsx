"use client";

import { CreditCard, CheckCircle2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, formatCurrency } from "@/lib/utils";

const PLANS = [
  {
    name: "Starter",
    price: 49,
    period: "month",
    features: ["Up to 3 technicians", "50 jobs/month", "Basic AI diagnostics", "Email support"],
    current: false,
  },
  {
    name: "Professional",
    price: 99,
    period: "month",
    features: ["Up to 10 technicians", "Unlimited jobs", "Full AI suite", "Permit management", "Priority support"],
    current: true,
  },
  {
    name: "Enterprise",
    price: 249,
    period: "month",
    features: ["Unlimited technicians", "Unlimited jobs", "Full AI suite", "API access", "Dedicated account manager", "Custom integrations"],
    current: false,
  },
];

const INVOICES = [
  { date: "Mar 1, 2026", amount: 99, status: "paid" },
  { date: "Feb 1, 2026", amount: 99, status: "paid" },
  { date: "Jan 1, 2026", amount: 99, status: "paid" },
  { date: "Dec 1, 2025", amount: 99, status: "paid" },
];

export default function BillingPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold">Billing</h1>
        <p className="text-muted-foreground">Manage your subscription and billing information</p>
      </div>

      {/* Current Plan */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Current Plan</CardTitle>
              <CardDescription>You are on the Professional plan</CardDescription>
            </div>
            <Badge className="bg-primary/10 text-primary border-0 text-sm">Active</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-1 mb-4">
            <span className="text-4xl font-bold">{formatCurrency(99)}</span>
            <span className="text-muted-foreground">/month</span>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            Next billing date: April 1, 2026
          </p>
          <div className="flex gap-3">
            <Button variant="outline">Change Plan</Button>
            <Button variant="outline" className="text-destructive hover:text-destructive">
              Cancel Subscription
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Plans comparison */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Available Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PLANS.map((plan) => (
            <Card
              key={plan.name}
              className={cn(
                "relative",
                plan.current && "border-primary ring-1 ring-primary"
              )}
            >
              {plan.current && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="gradient-primary text-white border-0">Current Plan</Badge>
                </div>
              )}
              <CardContent className="p-5 pt-6">
                <h3 className="font-bold text-lg mb-1">{plan.name}</h3>
                <div className="flex items-baseline gap-1 mb-4">
                  <span className="text-3xl font-bold">{formatCurrency(plan.price)}</span>
                  <span className="text-muted-foreground text-sm">/{plan.period}</span>
                </div>
                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="text-sm flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Button
                  variant={plan.current ? "outline" : "default"}
                  className="w-full"
                  disabled={plan.current}
                >
                  {plan.current ? "Current Plan" : "Upgrade"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Payment method */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Payment Method
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-7 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center text-white text-xs font-bold">
                VISA
              </div>
              <div>
                <p className="text-sm font-medium">Visa ending in 4242</p>
                <p className="text-xs text-muted-foreground">Expires 12/2027</p>
              </div>
            </div>
            <Button variant="ghost" size="sm">Update</Button>
          </div>
        </CardContent>
      </Card>

      {/* Billing history */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Billing History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {INVOICES.map((inv, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                <div>
                  <p className="text-sm font-medium">{inv.date}</p>
                  <p className="text-xs text-muted-foreground">Professional Plan</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">{formatCurrency(inv.amount)}</span>
                  <Badge className="text-xs bg-green-100 text-green-700">Paid</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
