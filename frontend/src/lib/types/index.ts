export type JobStatus =
  | "pending"
  | "scheduled"
  | "in_progress"
  | "completed"
  | "cancelled";

export type JobPriority = "low" | "medium" | "high" | "emergency";

export type EstimateStatus = "draft" | "sent" | "accepted" | "declined";

export type PermitStatus =
  | "not_required"
  | "required"
  | "applied"
  | "approved"
  | "rejected";

export interface Job {
  id: string;
  title: string;
  description: string;
  status: JobStatus;
  priority: JobPriority;
  customer_id: string;
  customer_name: string;
  address: string;
  assigned_tech_id: string | null;
  assigned_tech_name: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  estimated_duration_hours: number;
  actual_duration_hours: number | null;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  notes: string;
  created_at: string;
}

export interface Estimate {
  id: string;
  job_id: string;
  customer_id: string;
  status: EstimateStatus;
  line_items: EstimateLineItem[];
  subtotal: number;
  tax: number;
  total: number;
  notes: string;
  valid_until: string;
  created_at: string;
}

export interface EstimateLineItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Permit {
  id: string;
  job_id: string;
  permit_type: string;
  status: PermitStatus;
  application_date: string | null;
  approval_date: string | null;
  permit_number: string | null;
  notes: string;
}

export interface InventoryItem {
  id: string;
  name: string;
  sku: string;
  category: string;
  quantity: number;
  min_quantity: number;
  unit_price: number;
  supplier: string;
  last_restocked: string;
}

export interface ScheduleEntry {
  id: string;
  job_id: string;
  job_title: string;
  customer_name: string;
  address: string;
  tech_name: string;
  start_time: string;
  end_time: string;
  status: JobStatus;
}

export interface AgentSession {
  id: string;
  user_id: string;
  company_id: string;
  status: "active" | "completed" | "error";
  created_at: string;
}

export interface AgentMessage {
  id: string;
  session_id: string;
  role: "user" | "agent" | "system";
  content: string;
  tool_calls?: ToolCall[];
  timestamp: string;
}

export interface ToolCall {
  id: string;
  name: string;
  status: "running" | "completed" | "error";
  args?: Record<string, unknown>;
  result?: string;
}

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
  agent?: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  company_id: string;
  role: "owner" | "admin" | "technician";
}

export interface ActivityItem {
  id: string;
  type: "job_created" | "job_completed" | "estimate_sent" | "permit_approved" | "customer_added" | "inventory_low";
  message: string;
  timestamp: string;
}
