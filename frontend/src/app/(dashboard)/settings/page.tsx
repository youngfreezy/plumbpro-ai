"use client";

import { useState } from "react";
import {
  Building2,
  Phone,
  Mail,
  MapPin,
  Clock,
  Users,
  Percent,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const TEAM_MEMBERS = [
  { id: "t1", name: "Mike Torres", role: "Lead Plumber", email: "mike@plumbpro.com", phone: "(555) 111-2222" },
  { id: "t2", name: "Sarah Kim", role: "Journeyman Plumber", email: "sarah@plumbpro.com", phone: "(555) 222-3333" },
  { id: "t3", name: "Dave Reynolds", role: "Apprentice", email: "dave@plumbpro.com", phone: "(555) 333-4444" },
  { id: "t4", name: "Lisa Chen", role: "Office Manager", email: "lisa@plumbpro.com", phone: "(555) 444-5555" },
];

const roleBadgeColors: Record<string, string> = {
  "Lead Plumber": "bg-blue-100 text-blue-700",
  "Journeyman Plumber": "bg-green-100 text-green-700",
  Apprentice: "bg-amber-100 text-amber-700",
  "Office Manager": "bg-purple-100 text-purple-700",
};

export default function SettingsPage() {
  const [companyName, setCompanyName] = useState("PlumbPro Services LLC");
  const [companyPhone, setCompanyPhone] = useState("(555) 100-2000");
  const [companyEmail, setCompanyEmail] = useState("office@plumbpro.com");
  const [companyAddress, setCompanyAddress] = useState("500 Commerce Dr, Suite 200, Springfield, IL 62701");
  const [zipCodes, setZipCodes] = useState("62701, 62702, 62703, 62704, 62707");
  const [workStart, setWorkStart] = useState("07:00");
  const [workEnd, setWorkEnd] = useState("18:00");
  const [defaultMarkup, setDefaultMarkup] = useState("35");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Manage your company configuration</p>
        </div>
        <Button className="gap-1.5">
          <Save className="w-4 h-4" />
          Save Changes
        </Button>
      </div>

      {/* Company Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            Company Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Company Name</label>
              <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Phone Number</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input className="pl-9" value={companyPhone} onChange={(e) => setCompanyPhone(e.target.value)} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input className="pl-9" value={companyEmail} onChange={(e) => setCompanyEmail(e.target.value)} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Address</label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input className="pl-9" value={companyAddress} onChange={(e) => setCompanyAddress(e.target.value)} />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Area */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Service Area
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div>
            <label className="text-sm font-medium mb-1.5 block">Zip Codes (comma-separated)</label>
            <Input value={zipCodes} onChange={(e) => setZipCodes(e.target.value)} placeholder="Enter zip codes..." />
            <p className="text-xs text-muted-foreground mt-1.5">
              {zipCodes.split(",").filter((z) => z.trim()).length} zip codes in service area
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Working Hours */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Working Hours
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-md">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Start Time</label>
              <Input type="time" value={workStart} onChange={(e) => setWorkStart(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">End Time</label>
              <Input type="time" value={workEnd} onChange={(e) => setWorkEnd(e.target.value)} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Team Management */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="w-4 h-4" />
            Team Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {TEAM_MEMBERS.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                    <Users className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm">{member.name}</p>
                      <Badge className={`text-xs ${roleBadgeColors[member.role] || "bg-gray-100 text-gray-700"}`}>
                        {member.role}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {member.email} &middot; {member.phone}
                    </p>
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  Edit
                </Button>
              </div>
            ))}
          </div>
          <Button variant="outline" className="mt-4 gap-1.5">
            <Users className="w-4 h-4" />
            Add Team Member
          </Button>
        </CardContent>
      </Card>

      {/* Markup Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Percent className="w-4 h-4" />
            Markup Settings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-w-xs">
            <label className="text-sm font-medium mb-1.5 block">Default Markup Percentage</label>
            <div className="relative">
              <Input
                type="number"
                min="0"
                max="100"
                value={defaultMarkup}
                onChange={(e) => setDefaultMarkup(e.target.value)}
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">%</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1.5">Applied to material costs on new estimates</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
