"""PlumbPro LangGraph state definition.

Defines the typed state schema used by the thin LangGraph router that
sits in front of the ReAct module agents.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional

from typing_extensions import TypedDict


def _merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Shallow-merge two dicts (used as the reducer for ``context``)."""
    return {**a, **b}


class PlumbProState(TypedDict):
    """State schema for the PlumbPro orchestrator graph.

    Attributes
    ----------
    session_id:
        Unique identifier for the SSE / websocket session so agents can
        emit real-time events to the correct frontend client.
    company_id:
        The plumbing company the request belongs to (multi-tenant).
    user_id:
        The authenticated user who initiated the request.
    module:
        Which module the request was routed to (e.g. ``"scheduling"``,
        ``"diagnostics"``, ``"estimates"``).  Set by ``classify_request``.
    request:
        The user's natural-language request text.
    context:
        Accumulated context dict — each node can merge additional data.
        Uses a shallow-merge reducer so concurrent updates are safe.
    job_id:
        If the request is about a specific job.
    customer_id:
        If the request is about a specific customer.
    result:
        The final output dict from the module agent.
    status:
        Pipeline status — ``"pending"`` | ``"running"`` | ``"hitl_pending"``
        | ``"complete"`` | ``"error"``.
    messages:
        Conversation history — appended via ``operator.add`` reducer.
    """

    session_id: str
    company_id: str
    user_id: str
    module: str
    request: str
    context: Annotated[Dict[str, Any], _merge_dicts]
    job_id: Optional[str]
    customer_id: Optional[str]
    result: Optional[Dict[str, Any]]
    status: str
    messages: Annotated[List[Any], operator.add]
