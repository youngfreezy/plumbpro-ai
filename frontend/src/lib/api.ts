import { getSession } from "next-auth/react";
import type {
  Job,
  Customer,
  AgentSession,
  Estimate,
  ScheduleEntry,
  SSEEvent,
} from "@/lib/types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- CSRF ---

let _csrfToken: string | null = null;

export async function getCsrfToken(): Promise<string> {
  if (_csrfToken) return _csrfToken;
  try {
    const res = await fetch(`${API_BASE}/api/csrf-token`, {
      credentials: "include",
    });
    const data = await res.json();
    _csrfToken = data.csrf_token;
    return _csrfToken!;
  } catch {
    return "";
  }
}

export async function csrfHeaders(): Promise<Record<string, string>> {
  const token = await getCsrfToken();
  return token ? { "X-CSRF-Token": token } : {};
}

// --- Auth ---

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const session = await getSession();
  const accessToken = (session as Record<string, unknown> | null)?.accessToken as
    | string
    | undefined;
  if (accessToken) {
    return { Authorization: `Bearer ${accessToken}` };
  }
  return {};
}

export async function getSSEToken(): Promise<string> {
  const session = await getSession();
  return ((session as Record<string, unknown> | null)?.accessToken as string) || "";
}

// --- Fetch wrapper ---

export async function apiFetch(
  url: string,
  options: RequestInit = {}
): Promise<unknown> {
  const authHeaders = await getAuthHeaders();
  const csrf = await csrfHeaders();

  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...csrf,
      ...(options.headers as Record<string, string> | undefined),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as Record<string, string>).detail || `Request failed: ${res.status}`
    );
  }

  return res.json();
}

// --- SSE ---

export function connectSSE(
  sessionId: string,
  onEvent: (event: SSEEvent) => void,
  onConnectionChange?: (connected: boolean) => void
): () => void {
  let aborted = false;
  let retryCount = 0;
  const maxRetries = 5;

  async function connect() {
    if (aborted) return;

    const token = await getSSEToken();
    const url = `${API_BASE}/api/agent/sessions/${sessionId}/stream?token=${encodeURIComponent(token)}`;

    try {
      const eventSource = new EventSource(url);
      onConnectionChange?.(true);
      retryCount = 0;

      eventSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          const sseEvent: SSEEvent = {
            event: data.event || "message",
            data: data,
            timestamp: data.timestamp || new Date().toISOString(),
            agent: data.agent,
          };
          onEvent(sseEvent);
        } catch {
          // skip malformed messages
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        onConnectionChange?.(false);
        if (!aborted && retryCount < maxRetries) {
          retryCount++;
          const delay = Math.min(1000 * 2 ** retryCount, 30000);
          setTimeout(connect, delay);
        }
      };

      // Store for cleanup
      const cleanup = () => {
        aborted = true;
        eventSource.close();
        onConnectionChange?.(false);
      };
      cleanupRef = cleanup;
    } catch {
      onConnectionChange?.(false);
      if (!aborted && retryCount < maxRetries) {
        retryCount++;
        setTimeout(connect, 2000);
      }
    }
  }

  let cleanupRef: (() => void) | null = null;
  connect();

  return () => {
    aborted = true;
    cleanupRef?.();
  };
}

// --- Typed API functions ---

export async function startAgentSession(context?: Record<string, unknown>): Promise<AgentSession> {
  return apiFetch("/api/agent/sessions", {
    method: "POST",
    body: JSON.stringify(context || {}),
  }) as Promise<AgentSession>;
}

export async function sendMessage(
  sessionId: string,
  message: string
): Promise<void> {
  await apiFetch(`/api/agent/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content: message }),
  });
}

export async function getJobs(params?: {
  status?: string;
  priority?: string;
}): Promise<Job[]> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.priority) searchParams.set("priority", params.priority);
  const qs = searchParams.toString();
  return apiFetch(`/api/jobs${qs ? `?${qs}` : ""}`) as Promise<Job[]>;
}

export async function getJob(id: string): Promise<Job> {
  return apiFetch(`/api/jobs/${id}`) as Promise<Job>;
}

export async function createJob(
  data: Partial<Job>
): Promise<Job> {
  return apiFetch("/api/jobs", {
    method: "POST",
    body: JSON.stringify(data),
  }) as Promise<Job>;
}

export async function updateJobStatus(
  id: string,
  status: string
): Promise<Job> {
  return apiFetch(`/api/jobs/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  }) as Promise<Job>;
}

export async function getCustomers(): Promise<Customer[]> {
  return apiFetch("/api/customers") as Promise<Customer[]>;
}

export async function createCustomer(
  data: Partial<Customer>
): Promise<Customer> {
  return apiFetch("/api/customers", {
    method: "POST",
    body: JSON.stringify(data),
  }) as Promise<Customer>;
}

export async function getSchedule(date?: string): Promise<ScheduleEntry[]> {
  const qs = date ? `?date=${date}` : "";
  return apiFetch(`/api/schedule${qs}`) as Promise<ScheduleEntry[]>;
}

export async function getEstimates(jobId?: string): Promise<Estimate[]> {
  const qs = jobId ? `?job_id=${jobId}` : "";
  return apiFetch(`/api/estimates${qs}`) as Promise<Estimate[]>;
}

export async function createEstimate(
  data: Partial<Estimate>
): Promise<Estimate> {
  return apiFetch("/api/estimates", {
    method: "POST",
    body: JSON.stringify(data),
  }) as Promise<Estimate>;
}
