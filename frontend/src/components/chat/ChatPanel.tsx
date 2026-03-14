"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Loader2, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { connectSSE, sendMessage } from "@/lib/api";
import type { SSEEvent, AgentMessage, ToolCall } from "@/lib/types";

interface ChatPanelProps {
  sessionId: string;
  onEvent?: (event: SSEEvent) => void;
}

export default function ChatPanel({ sessionId, onEvent }: ChatPanelProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: "system-1",
      session_id: sessionId,
      role: "system",
      content:
        "AI Assistant ready. Ask me about this job, request diagnostics, generate estimates, or get help with anything plumbing-related.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [connected, setConnected] = useState(false);
  const [activeTools, setActiveTools] = useState<ToolCall[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, activeTools, scrollToBottom]);

  // Connect SSE
  useEffect(() => {
    const cleanup = connectSSE(
      sessionId,
      (event) => {
        onEvent?.(event);

        if (event.event === "agent_message") {
          const data = event.data as Record<string, string>;
          setMessages((prev) => [
            ...prev,
            {
              id: `agent-${Date.now()}`,
              session_id: sessionId,
              role: "agent",
              content: data.content || "",
              timestamp: event.timestamp,
            },
          ]);
          setIsThinking(false);
          setActiveTools([]);
        } else if (event.event === "thinking") {
          setIsThinking(true);
        } else if (event.event === "tool_call") {
          const data = event.data as Record<string, string>;
          setActiveTools((prev) => [
            ...prev.filter((t) => t.name !== data.tool_name),
            {
              id: `tool-${Date.now()}`,
              name: data.tool_name || "unknown",
              status: "running",
            },
          ]);
        } else if (event.event === "tool_result") {
          const data = event.data as Record<string, string>;
          setActiveTools((prev) =>
            prev.map((t) =>
              t.name === data.tool_name
                ? { ...t, status: "completed" as const, result: data.result }
                : t
            )
          );
        }
      },
      setConnected
    );

    return cleanup;
  }, [sessionId, onEvent]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;

    const userMsg: AgentMessage = {
      id: `user-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);

    try {
      await sendMessage(sessionId, text);
    } catch {
      setIsThinking(false);
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          session_id: sessionId,
          role: "system",
          content: "Failed to send message. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    }

    inputRef.current?.focus();
  };

  return (
    <Card className="flex flex-col h-[600px]">
      <CardHeader className="pb-3 border-b shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Bot className="w-4 h-4 text-primary" />
            AI Assistant
          </CardTitle>
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              connected ? "bg-green-500" : "bg-gray-300"
            )}
            title={connected ? "Connected" : "Disconnected"}
          />
        </div>
      </CardHeader>

      {/* Messages */}
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-2.5",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {msg.role !== "user" && (
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center shrink-0",
                  msg.role === "agent"
                    ? "gradient-primary"
                    : "bg-muted"
                )}
              >
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[80%] rounded-lg px-3 py-2 text-sm",
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : msg.role === "system"
                  ? "bg-muted text-muted-foreground italic"
                  : "bg-muted"
              )}
            >
              {msg.content}
            </div>
            {msg.role === "user" && (
              <div className="w-7 h-7 rounded-full bg-secondary flex items-center justify-center shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {/* Active tool calls */}
        {activeTools.map((tool) => (
          <div key={tool.id} className="flex gap-2.5">
            <div className="w-7 h-7 rounded-full bg-muted flex items-center justify-center shrink-0">
              <Wrench className="w-4 h-4 text-primary" />
            </div>
            <div className="bg-muted rounded-lg px-3 py-2 text-sm flex items-center gap-2">
              {tool.status === "running" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
              ) : (
                <span className="w-3.5 h-3.5 text-green-500">&#10003;</span>
              )}
              <span className="text-muted-foreground">
                {tool.status === "running"
                  ? `Running: ${tool.name}...`
                  : `Completed: ${tool.name}`}
              </span>
            </div>
          </div>
        ))}

        {/* Thinking indicator */}
        {isThinking && activeTools.length === 0 && (
          <div className="flex gap-2.5">
            <div className="w-7 h-7 rounded-full gradient-primary flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-muted rounded-lg px-3 py-2">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </CardContent>

      {/* Input */}
      <div className="p-3 border-t shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the AI assistant..."
            disabled={isThinking}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isThinking}
          >
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </Card>
  );
}
