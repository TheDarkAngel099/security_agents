from langgraph.graph import StateGraph, END
from .state import AgentState
from .agents import (
    detection_agent,
    interaction_agent,
    routing_agent,
    hr_resolution_agent,
    security_resolution_agent,
)


def should_interact(state: AgentState):
    """After detection: route to interaction agent if violation, else end."""
    if state.get("violation_detected"):
        return "interaction"
    return END


def interaction_result(state: AgentState):
    """After interaction: if user edits, re-scan; if override, escalate."""
    action = state.get("user_action")
    if action == "Edit":
        return "detection"   # re-scan the edited message
    return "routing"         # override → escalate


def route_resolution(state: AgentState):
    """After routing: send to the correct resolution agent."""
    agent = state.get("resolution_agent")
    if agent == "HR":
        return "hr_resolution"
    elif agent == "Security":
        return "security_resolution"
    return END


def create_graph():
    workflow = StateGraph(AgentState)

    # ── Nodes ───────────────────────────────────────────────────────────────
    workflow.add_node("detection", detection_agent)
    workflow.add_node("interaction", interaction_agent)
    workflow.add_node("routing", routing_agent)
    workflow.add_node("hr_resolution", hr_resolution_agent)
    workflow.add_node("security_resolution", security_resolution_agent)

    # ── Entry point ─────────────────────────────────────────────────────────
    workflow.set_entry_point("detection")

    # ── Conditional edges ───────────────────────────────────────────────────
    workflow.add_conditional_edges(
        "detection",
        should_interact,
        {"interaction": "interaction", END: END},
    )

    workflow.add_conditional_edges(
        "interaction",
        interaction_result,
        {"detection": "detection", "routing": "routing"},
    )

    workflow.add_conditional_edges(
        "routing",
        route_resolution,
        {
            "hr_resolution": "hr_resolution",
            "security_resolution": "security_resolution",
            END: END,
        },
    )

    # ── Terminal edges ──────────────────────────────────────────────────────
    workflow.add_edge("hr_resolution", END)
    workflow.add_edge("security_resolution", END)

    return workflow.compile()
