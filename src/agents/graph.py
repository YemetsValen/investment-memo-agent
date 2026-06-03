"""LangGraph pipeline: Researcher → Analyst → Risk → Writer.

This is the orchestration layer that chains the four agents
into a sequential graph with conditional routing.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from src.agents.analyst import analyst_node
from src.agents.researcher import researcher_node
from src.agents.risk import risk_node
from src.agents.state import AgentState
from src.agents.writer import writer_node

logger = logging.getLogger(__name__)


def _should_continue(state: AgentState) -> str:
    """Route to writer on error (to produce error report), else continue."""
    if state.get("error"):
        return "writer"
    return "continue"


def build_graph() -> StateGraph:
    """Construct and compile the multi-agent analysis graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("risk", risk_node)
    graph.add_node("writer", writer_node)

    # Define edges
    graph.set_entry_point("researcher")

    graph.add_conditional_edges(
        "researcher",
        _should_continue,
        {"continue": "analyst", "writer": "writer"},
    )

    graph.add_conditional_edges(
        "analyst",
        _should_continue,
        {"continue": "risk", "writer": "writer"},
    )

    graph.add_edge("risk", "writer")
    graph.add_edge("writer", END)

    return graph


def compile_graph():
    """Return a compiled, runnable graph."""
    return build_graph().compile()
