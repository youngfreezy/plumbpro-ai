"use client";

import { cn } from "@/lib/utils";
import { formatRelativeTime } from "@/lib/utils";
import type { SSEEvent } from "@/lib/types";

const eventColors: Record<string, string> = {
  agent_message: "bg-primary",
  thinking: "bg-amber-500",
  tool_call: "bg-blue-500",
  tool_result: "bg-green-500",
  error: "bg-red-500",
  status_change: "bg-purple-500",
};

const eventLabels: Record<string, string> = {
  agent_message: "Message",
  thinking: "Thinking",
  tool_call: "Tool Call",
  tool_result: "Tool Result",
  error: "Error",
  status_change: "Status Change",
};

interface StatusFeedProps {
  events: SSEEvent[];
  className?: string;
}

export default function StatusFeed({ events, className }: StatusFeedProps) {
  if (events.length === 0) {
    return (
      <div className={cn("text-center text-muted-foreground text-sm py-8", className)}>
        No events yet. Interact with the AI assistant to see activity.
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {events.map((event, i) => {
        const color = eventColors[event.event] || "bg-gray-400";
        const label = eventLabels[event.event] || event.event;

        return (
          <div key={i} className="flex gap-3">
            {/* Timeline dot + line */}
            <div className="flex flex-col items-center">
              <div className={cn("w-2.5 h-2.5 rounded-full mt-1.5 shrink-0", color)} />
              {i < events.length - 1 && (
                <div className="w-px flex-1 bg-border mt-1" />
              )}
            </div>

            {/* Content */}
            <div className="pb-3 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span
                  className={cn(
                    "text-xs font-medium px-1.5 py-0.5 rounded",
                    event.event === "error"
                      ? "bg-red-100 text-red-700"
                      : event.event === "tool_call"
                      ? "bg-blue-100 text-blue-700"
                      : event.event === "tool_result"
                      ? "bg-green-100 text-green-700"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {label}
                </span>
                {event.agent && (
                  <span className="text-xs text-muted-foreground">
                    {event.agent}
                  </span>
                )}
                <span className="text-xs text-muted-foreground ml-auto">
                  {formatRelativeTime(event.timestamp)}
                </span>
              </div>
              {event.data && (
                <p className="text-sm text-muted-foreground truncate">
                  {typeof event.data === "string"
                    ? event.data
                    : (event.data as Record<string, string>).content ||
                      (event.data as Record<string, string>).tool_name ||
                      JSON.stringify(event.data).slice(0, 100)}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
