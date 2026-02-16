import operator
from typing import Annotated, List, Optional, TypedDict


class AgentState(TypedDict):
    input_text: str
    sender: str
    recipient: str
    # Detection
    violation_detected: bool
    violation_type: Optional[str]       # "Toxicity", "PII", "Adversarial", None
    violation_details: Optional[str]    # LLM explanation of why it's a violation
    # Interaction
    user_action: Optional[str]          # "Edit", "Override", None
    edited_text: Optional[str]          # User's edited text (if action=Edit)
    interaction_message: Optional[str]  # LLM-generated nudge message to user
    # Routing
    risk_level: Optional[str]           # "High"
    resolution_agent: Optional[str]     # "HR", "Security", None
    routing_rationale: Optional[str]    # LLM explanation of route choice
    # Resolution
    final_action: Optional[str]         # LLM recommended action
    resolution_report: Optional[str]    # Full LLM report
    # Logging
    logs: Annotated[List[str], operator.add]
