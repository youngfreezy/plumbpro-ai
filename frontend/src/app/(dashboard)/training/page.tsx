"use client";

import { useState, useMemo } from "react";
import {
  Search,
  GraduationCap,
  Award,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Play,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatDate } from "@/lib/utils";

const CERTIFICATIONS = [
  {
    id: "1",
    tech: "Mike Torres",
    cert: "Journeyman Plumber License",
    issuer: "State Board",
    earned: "2024-06-15",
    expires: "2026-06-15",
    status: "active" as const,
  },
  {
    id: "2",
    tech: "Mike Torres",
    cert: "Backflow Prevention Certification",
    issuer: "ASSE",
    earned: "2025-01-10",
    expires: "2027-01-10",
    status: "active" as const,
  },
  {
    id: "3",
    tech: "Sarah Kim",
    cert: "Journeyman Plumber License",
    issuer: "State Board",
    earned: "2025-03-01",
    expires: "2027-03-01",
    status: "active" as const,
  },
  {
    id: "4",
    tech: "Sarah Kim",
    cert: "Medical Gas Installer",
    issuer: "ASSE",
    earned: "2024-09-20",
    expires: "2026-03-20",
    status: "expiring_soon" as const,
  },
  {
    id: "5",
    tech: "Dave Reynolds",
    cert: "Apprentice Plumber License",
    issuer: "State Board",
    earned: "2025-08-01",
    expires: "2027-08-01",
    status: "active" as const,
  },
  {
    id: "6",
    tech: "Dave Reynolds",
    cert: "OSHA 10-Hour Construction",
    issuer: "OSHA",
    earned: "2024-11-15",
    expires: "2026-11-15",
    status: "active" as const,
  },
  {
    id: "7",
    tech: "Mike Torres",
    cert: "OSHA 30-Hour Construction",
    issuer: "OSHA",
    earned: "2023-05-01",
    expires: "2025-05-01",
    status: "expired" as const,
  },
];

const QUIZZES = [
  { id: "q1", title: "Backflow Prevention Basics", questions: 20, duration: "15 min", category: "Safety" },
  { id: "q2", title: "Code Compliance Update 2026", questions: 30, duration: "25 min", category: "Code" },
  { id: "q3", title: "Tankless Water Heater Installation", questions: 15, duration: "10 min", category: "Technical" },
  { id: "q4", title: "Workplace Safety Refresher", questions: 25, duration: "20 min", category: "Safety" },
  { id: "q5", title: "Customer Communication Skills", questions: 10, duration: "8 min", category: "Soft Skills" },
];

const QUIZ_SCORES = [
  { tech: "Mike Torres", quiz: "Backflow Prevention Basics", score: 95, date: "2026-03-10" },
  { tech: "Mike Torres", quiz: "Code Compliance Update 2026", score: 88, date: "2026-03-08" },
  { tech: "Sarah Kim", quiz: "Backflow Prevention Basics", score: 100, date: "2026-03-11" },
  { tech: "Sarah Kim", quiz: "Workplace Safety Refresher", score: 92, date: "2026-03-05" },
  { tech: "Dave Reynolds", quiz: "Backflow Prevention Basics", score: 78, date: "2026-03-12" },
];

const statusConfig = {
  active: { label: "Active", color: "bg-green-100 text-green-700", icon: CheckCircle2 },
  expiring_soon: { label: "Expiring Soon", color: "bg-amber-100 text-amber-700", icon: AlertTriangle },
  expired: { label: "Expired", color: "bg-red-100 text-red-700", icon: Clock },
};

export default function TrainingPage() {
  const [search, setSearch] = useState("");
  const [techFilter, setTechFilter] = useState("all");

  const techs = useMemo(() => Array.from(new Set(CERTIFICATIONS.map((c) => c.tech))), []);

  const filteredCerts = useMemo(() => {
    return CERTIFICATIONS.filter((c) => {
      if (techFilter !== "all" && c.tech !== techFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return c.cert.toLowerCase().includes(q) || c.tech.toLowerCase().includes(q);
      }
      return true;
    });
  }, [search, techFilter]);

  const expiringCount = CERTIFICATIONS.filter(
    (c) => c.status === "expiring_soon" || c.status === "expired"
  ).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Training</h1>
          <p className="text-muted-foreground">
            Certifications, quizzes, and team development
          </p>
        </div>
        <Button className="gap-1.5">
          <GraduationCap className="w-4 h-4" />
          Assign Training
        </Button>
      </div>

      {expiringCount > 0 && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span className="font-medium">
            {expiringCount} certification{expiringCount !== 1 ? "s" : ""} expired or expiring soon
          </span>
        </div>
      )}

      {/* Certifications */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Team Certifications</h2>
        <div className="flex gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search certifications..."
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            value={techFilter}
            onChange={(e) => setTechFilter(e.target.value)}
          >
            <option value="all">All Technicians</option>
            {techs.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          {filteredCerts.map((cert) => {
            const cfg = statusConfig[cert.status];
            const StatusIcon = cfg.icon;
            return (
              <Card key={cert.id} className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Award className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-semibold">{cert.cert}</p>
                          <Badge className={cn("text-xs", cfg.color)}>{cfg.label}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {cert.tech} &mdash; {cert.issuer}
                        </p>
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      <p className="text-xs text-muted-foreground">
                        Expires {formatDate(cert.expires)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Available Quizzes */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Available Quizzes</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {QUIZZES.map((quiz) => (
            <Card key={quiz.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold">{quiz.title}</p>
                    <Badge variant="secondary" className="text-xs mt-1">
                      {quiz.category}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                  <span>{quiz.questions} questions</span>
                  <span>{quiz.duration}</span>
                </div>
                <Button size="sm" className="w-full gap-1.5">
                  <Play className="w-3.5 h-3.5" />
                  Start Quiz
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Scores */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Recent Quiz Scores</h2>
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="p-3 font-medium text-muted-foreground">Technician</th>
                    <th className="p-3 font-medium text-muted-foreground">Quiz</th>
                    <th className="p-3 font-medium text-muted-foreground text-right">Score</th>
                    <th className="p-3 font-medium text-muted-foreground text-right">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {QUIZ_SCORES.map((score, i) => (
                    <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="p-3 font-medium">{score.tech}</td>
                      <td className="p-3 text-muted-foreground">{score.quiz}</td>
                      <td className="p-3 text-right">
                        <Badge
                          className={cn(
                            "text-xs",
                            score.score >= 90
                              ? "bg-green-100 text-green-700"
                              : score.score >= 80
                              ? "bg-amber-100 text-amber-700"
                              : "bg-red-100 text-red-700"
                          )}
                        >
                          {score.score}%
                        </Badge>
                      </td>
                      <td className="p-3 text-right text-muted-foreground">
                        {formatDate(score.date)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
