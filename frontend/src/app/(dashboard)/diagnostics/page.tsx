"use client";

import { useState } from "react";
import { Search, Send, Bot, Upload, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const COMMON_ISSUES = [
  { label: "Leaking faucet", query: "Customer reports a dripping kitchen faucet, single-handle Moen" },
  { label: "No hot water", query: "No hot water from gas water heater, pilot light is out" },
  { label: "Slow drain", query: "Bathroom sink draining very slowly, tried plunger" },
  { label: "Running toilet", query: "Toilet runs intermittently, flapper looks worn" },
  { label: "Low water pressure", query: "Low water pressure throughout the house, no recent changes" },
  { label: "Sewer smell", query: "Sewer gas smell from basement floor drain" },
];

export default function DiagnosticsPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDiagnose = async (text?: string) => {
    const diagQuery = text || query;
    if (!diagQuery.trim()) return;

    setLoading(true);
    setResult(null);

    // Simulated AI response for demo
    setTimeout(() => {
      setResult(
        `**Diagnosis: ${diagQuery.includes("faucet") ? "Worn Cartridge / O-Ring" : diagQuery.includes("hot water") ? "Faulty Thermocouple" : "Potential Blockage"}**\n\n` +
        `Based on the symptoms described, here is the recommended approach:\n\n` +
        `1. **Initial Assessment**: Verify the symptoms on-site. Check for visible damage or wear.\n\n` +
        `2. **Diagnostic Steps**:\n` +
        `   - Inspect the affected components\n` +
        `   - Test water pressure and flow rates\n` +
        `   - Check for code compliance issues\n\n` +
        `3. **Recommended Repair**:\n` +
        `   - Replace worn components\n` +
        `   - Estimated time: 1-2 hours\n` +
        `   - Estimated parts cost: $25-75\n\n` +
        `4. **Additional Notes**: Consider recommending preventive maintenance to the customer.`
      );
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Diagnostics</h1>
        <p className="text-muted-foreground">
          Describe plumbing symptoms to get AI-powered diagnosis and repair recommendations
        </p>
      </div>

      {/* Input area */}
      <Card>
        <CardContent className="p-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleDiagnose();
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium mb-1.5">
                Describe the plumbing issue
              </label>
              <textarea
                className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-y"
                placeholder="e.g., Customer reports a slow-draining bathtub. They mention hearing gurgling sounds from the drain when the washing machine runs..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={!query.trim() || loading} className="gap-1.5">
                <Search className="w-4 h-4" />
                {loading ? "Diagnosing..." : "Diagnose"}
              </Button>
              <Button type="button" variant="outline" className="gap-1.5">
                <Upload className="w-4 h-4" />
                Upload Photo
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Common issues */}
      <div>
        <h2 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-1.5">
          <Lightbulb className="w-4 h-4" />
          Common Issues - Quick Diagnose
        </h2>
        <div className="flex flex-wrap gap-2">
          {COMMON_ISSUES.map((issue) => (
            <Button
              key={issue.label}
              variant="outline"
              size="sm"
              onClick={() => {
                setQuery(issue.query);
                handleDiagnose(issue.query);
              }}
            >
              {issue.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Result */}
      {(result || loading) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              Diagnostic Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
                <div className="h-4 w-full bg-muted animate-pulse rounded" />
                <div className="h-4 w-5/6 bg-muted animate-pulse rounded" />
                <div className="h-4 w-2/3 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <div className="prose prose-sm max-w-none">
                {result?.split("\n").map((line, i) => (
                  <p key={i} className={line.startsWith("**") ? "font-semibold" : ""}>
                    {line.replace(/\*\*/g, "")}
                  </p>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
