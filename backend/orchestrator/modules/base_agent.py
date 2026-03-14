"""Base ReAct agent runner for PlumbPro AI modules.

Instead of hardcoded LangGraph node chains, each module runs a ReAct loop
where Claude picks tools dynamically based on the situation.  This is the
core execution engine that every module agent delegates to.

The loop:
  1. Send the accumulated message history (system + conversation) to the LLM.
  2. If the response contains no tool_calls -> the agent is finished.
  3. For each tool_call: emit an SSE event, execute the tool, capture the
     result (or error), append a ToolMessage, and loop back to step 1.
  4. Stop after max_iterations to prevent runaway loops.
"""

from __future__ import annotations

import json
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

from backend.shared.event_bus import emit_agent_event
from backend.shared.llm import get_default_model, invoke_with_retry

logger = logging.getLogger(__name__)


def _find_tool(tools: List[BaseTool], name: str) -> Optional[BaseTool]:
    """Look up a tool by name from the tool list."""
    for t in tools:
        if t.name == name:
            return t
    return None


def _serialize_tool_result(result: Any) -> str:
    """Convert a tool's return value to a string suitable for a ToolMessage."""
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, default=str)
    except (TypeError, ValueError):
        return str(result)


async def run_react_agent(
    system_prompt: str,
    tools: List[BaseTool],
    user_message: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    max_iterations: int = 15,
    llm: Optional[ChatAnthropic] = None,
) -> Dict[str, Any]:
    """Execute a ReAct tool-calling loop.

    Parameters
    ----------
    system_prompt:
        The system-level instructions that define the agent's role and
        behaviour.  Should include all domain-specific guidance.
    tools:
        A list of LangChain tool objects (decorated with ``@tool``) that the
        agent may call.
    user_message:
        The user's natural-language request.
    context:
        Optional dict of contextual data (company_id, job details, etc.)
        that will be injected into the system prompt as a JSON block.
    session_id:
        SSE session identifier.  When provided, progress events are emitted
        to the frontend via the shared event bus.
    max_iterations:
        Safety cap on the number of LLM round-trips.
    llm:
        Override the default ChatAnthropic model (useful for tests or
        premium-tier escalation).

    Returns
    -------
    dict
        {
            "status": "complete" | "max_iterations",
            "result": <final text from the agent>,
            "tool_calls_made": [<list of tool names invoked>],
        }
    """
    # -----------------------------------------------------------------
    # Build the LLM with tools bound
    # -----------------------------------------------------------------
    if llm is None:
        llm = get_default_model()

    llm_with_tools = llm.bind_tools(tools) if tools else llm

    # -----------------------------------------------------------------
    # Assemble the initial message list
    # -----------------------------------------------------------------
    full_system = system_prompt
    if context:
        full_system += (
            "\n\n--- CONTEXT ---\n"
            + json.dumps(context, indent=2, default=str)
        )

    messages: List[BaseMessage] = [
        SystemMessage(content=full_system),
        HumanMessage(content=user_message),
    ]

    tool_calls_made: List[str] = []

    # -----------------------------------------------------------------
    # ReAct loop
    # -----------------------------------------------------------------
    for iteration in range(1, max_iterations + 1):
        logger.info(
            "[ReAct %s] iteration %d/%d",
            session_id or "no-session",
            iteration,
            max_iterations,
        )

        # -- Step 1: call the LLM --
        try:
            response: AIMessage = await invoke_with_retry(  # type: ignore[assignment]
                llm_with_tools, messages
            )
        except Exception as exc:
            logger.error("LLM call failed permanently: %s", exc)
            return {
                "status": "error",
                "result": f"LLM call failed: {exc}",
                "tool_calls_made": tool_calls_made,
            }

        messages.append(response)

        # -- Step 2: check for tool calls --
        if not response.tool_calls:
            # Agent is done — extract the final text answer.
            final_text = response.content or ""
            if isinstance(final_text, list):
                # Claude sometimes returns a list of content blocks
                final_text = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in final_text
                )

            logger.info(
                "[ReAct %s] agent complete after %d iterations, %d tool calls",
                session_id or "no-session",
                iteration,
                len(tool_calls_made),
            )

            # Emit thinking / completion events
            if session_id and final_text:
                await emit_agent_event(session_id, "agent_thinking", {
                    "iteration": iteration,
                    "text": final_text,
                })
                await emit_agent_event(session_id, "agent_complete", {
                    "result": final_text,
                    "tool_calls_made": tool_calls_made,
                    "iterations": iteration,
                })

            return {
                "status": "complete",
                "result": final_text,
                "tool_calls_made": tool_calls_made,
            }

        # If the response has both text AND tool calls, emit the thinking
        if response.content and session_id:
            thinking_text = response.content
            if isinstance(thinking_text, list):
                thinking_text = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in thinking_text
                )
            if thinking_text.strip():
                await emit_agent_event(session_id, "agent_thinking", {
                    "iteration": iteration,
                    "text": thinking_text,
                })

        # -- Step 3: execute each tool call --
        for tc in response.tool_calls:
            tool_name: str = tc["name"]
            tool_args: dict = tc["args"]
            tool_call_id: str = tc["id"]

            logger.info(
                "[ReAct %s] calling tool %s with args %s",
                session_id or "no-session",
                tool_name,
                json.dumps(tool_args, default=str)[:500],
            )
            tool_calls_made.append(tool_name)

            # Emit tool_call event
            if session_id:
                await emit_agent_event(session_id, "tool_call", {
                    "iteration": iteration,
                    "tool": tool_name,
                    "args": tool_args,
                })

            # Find and execute the tool
            tool_fn = _find_tool(tools, tool_name)
            if tool_fn is None:
                error_msg = f"Tool '{tool_name}' not found in available tools."
                logger.warning(error_msg)
                messages.append(
                    ToolMessage(content=error_msg, tool_call_id=tool_call_id)
                )
                if session_id:
                    await emit_agent_event(session_id, "tool_result", {
                        "iteration": iteration,
                        "tool": tool_name,
                        "error": error_msg,
                    })
                continue

            try:
                result = await tool_fn.ainvoke(tool_args)
                result_str = _serialize_tool_result(result)
            except Exception as exc:
                # Tool threw an error — feed it back to the LLM so it can
                # decide how to recover (retry, try another approach, etc.)
                error_msg = (
                    f"Tool '{tool_name}' raised an error: {exc}\n"
                    f"{traceback.format_exc()}"
                )
                logger.error(error_msg)
                result_str = f"ERROR: {exc}"

                if session_id:
                    await emit_agent_event(session_id, "tool_result", {
                        "iteration": iteration,
                        "tool": tool_name,
                        "error": str(exc),
                    })

                messages.append(
                    ToolMessage(content=result_str, tool_call_id=tool_call_id)
                )
                continue

            logger.info(
                "[ReAct %s] tool %s returned: %s",
                session_id or "no-session",
                tool_name,
                result_str[:500],
            )

            if session_id:
                await emit_agent_event(session_id, "tool_result", {
                    "iteration": iteration,
                    "tool": tool_name,
                    "result": result_str[:2000],  # cap for SSE payload size
                })

            messages.append(
                ToolMessage(content=result_str, tool_call_id=tool_call_id)
            )

    # -- Exhausted max_iterations --
    logger.warning(
        "[ReAct %s] hit max iterations (%d)", session_id or "no-session", max_iterations
    )

    # Try to extract any useful text from the last AI message
    last_ai_msgs = [m for m in reversed(messages) if isinstance(m, AIMessage)]
    fallback_text = ""
    if last_ai_msgs:
        content = last_ai_msgs[0].content
        if isinstance(content, list):
            fallback_text = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )
        elif isinstance(content, str):
            fallback_text = content

    if session_id:
        await emit_agent_event(session_id, "agent_complete", {
            "result": fallback_text or "Agent reached maximum iterations without a final answer.",
            "tool_calls_made": tool_calls_made,
            "iterations": max_iterations,
            "max_iterations_reached": True,
        })

    return {
        "status": "max_iterations",
        "result": fallback_text or "Agent reached maximum iterations without a final answer.",
        "tool_calls_made": tool_calls_made,
    }
