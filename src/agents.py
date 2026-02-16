import json
import os
import re
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from .state import AgentState

# ── Load .env ───────────────────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Shared LLM ──────────────────────────────────────────────────────────────
model = ChatGroq(model="llama-3.1-8b-instant", temperature=0.5)


# ── Robust JSON parser ─────────────────────────────────────────────────────
def parse_json_response(text: str, fallback: dict) -> dict:
    """Parse JSON from LLM output, resilient to markdown and extra text."""
    try:
        # 1. Try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Aggressive extraction: find first '{' and last '}'
    # This handles cases where the model adds "Here is the JSON:" preamble
    try:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except json.JSONDecodeError:
        pass
        
    return fallback


# ── 1. Detection Agent ──────────────────────────────────────────────────────
DETECTION_SYSTEM_PROMPT = """You are a corporate communication safety filter.
Analyze the message for:
1. **Toxicity** (hate speech, insults, threats)
2. **PII** (passwords, SSNs, keys, personal data)
3. **Adversarial** (phishing, malware, hacking)

Return JSON ONLY. No markdown. No reasoning outside JSON.
Format:
{"violation_detected": boolean, "violation_type": "Toxicity"|"PII"|"Adversarial"|null, "explanation": "string"}
"""


def detection_agent(state: AgentState) -> Dict[str, Any]:
    text = state.get("input_text", "")
    response = model.invoke([
        SystemMessage(content=DETECTION_SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this message:\n\n\"{text}\"")
    ])

    fallback = {"violation_detected": False, "violation_type": None, "explanation": "Parse error – treating as safe."}
    result = parse_json_response(response.content, fallback)

    log = (
        f"[Detection Agent] Scanned: '{text}' | "
        f"Violation: {result['violation_detected']} | "
        f"Type: {result.get('violation_type')} | "
        f"Reason: {result.get('explanation')}"
    )

    return {
        "violation_detected": result["violation_detected"],
        "violation_type": result.get("violation_type"),
        "violation_details": result.get("explanation"),
        "logs": [log],
    }


# ── 2. Interaction Agent (The Nudge) ────────────────────────────────────────
INTERACTION_SYSTEM_PROMPT = """You are a respectful workplace assistant.
A user has written a message that was flagged as a violation.

Violation type : {violation_type}
Details        : {violation_details}
Original text  : "{input_text}"

Your job:
1. Craft a short, polite message explaining WHY the message was flagged.
2. Suggest a safer alternative wording.

Respond ONLY with valid JSON:
{{
  "nudge_message": "Your polite explanation to the user",
  "suggested_rewrite": "A safer version of the original message"
}}"""


def interaction_agent(state: AgentState) -> Dict[str, Any]:
    prompt = INTERACTION_SYSTEM_PROMPT.format(
        violation_type=state.get("violation_type"),
        violation_details=state.get("violation_details"),
        input_text=state.get("input_text"),
    )
    response = model.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Please generate the nudge message and suggested rewrite.")
    ])

    fallback = {
        "nudge_message": "Your message was flagged. Please review it.",
        "suggested_rewrite": state.get("input_text", ""),
    }
    result = parse_json_response(response.content, fallback)

    user_action = state.get("user_action", "Override")
    log = (
        f"[Interaction Agent] Nudge: {result['nudge_message']} | "
        f"Suggested rewrite: {result.get('suggested_rewrite')} | "
        f"User chose: {user_action}"
    )

    updates: Dict[str, Any] = {
        "interaction_message": result["nudge_message"],
        "logs": [log],
    }

    if user_action == "Edit":
        # Use the LLM-suggested safe rewrite as the edited text
        updates["input_text"] = result.get("suggested_rewrite", state.get("input_text"))
        updates["edited_text"] = updates["input_text"]

    return updates


# ── 3. Routing Agent (The Switchboard) ──────────────────────────────────────
ROUTING_SYSTEM_PROMPT = """You are a corporate incident routing specialist.
A message has been overridden by the user despite being flagged.

Violation type    : {violation_type}
Violation details : {violation_details}
Original message  : "{input_text}"

Route the incident:
- "HR" for behavioral / ethics issues (toxicity, harassment, code-of-conduct)
- "Security" for technical issues (data leaks, PII exposure, malware, adversarial attacks)

Respond ONLY with valid JSON:
{{
  "resolution_agent": "HR" | "Security",
  "risk_level": "High",
  "rationale": "Why you chose this route"
}}"""


def routing_agent(state: AgentState) -> Dict[str, Any]:
    prompt = ROUTING_SYSTEM_PROMPT.format(
        violation_type=state.get("violation_type"),
        violation_details=state.get("violation_details"),
        input_text=state.get("input_text"),
    )
    response = model.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Route this incident.")
    ])

    fallback = {"resolution_agent": "Security", "risk_level": "High", "rationale": "Parse error – defaulting to Security."}
    result = parse_json_response(response.content, fallback)

    log = (
        f"[Routing Agent] Routed to: {result['resolution_agent']} | "
        f"Risk: {result['risk_level']} | "
        f"Rationale: {result.get('rationale')}"
    )

    return {
        "resolution_agent": result["resolution_agent"],
        "risk_level": result["risk_level"],
        "routing_rationale": result.get("rationale"),
        "logs": [log],
    }


# ── 4a. HR Resolution Agent ────────────────────────────────────────────────
HR_SYSTEM_PROMPT = """You are an HR compliance officer AI.
An employee sent a message that violates corporate code of conduct.

Violation type : {violation_type}
Details        : {violation_details}
Message        : "{input_text}"

Produce a formal incident report. Include:
1. Violation summary
2. Severity assessment (Low / Medium / High / Critical)
3. Recommended action (e.g., warning, mandatory training, suspension, escalation to management)
4. Notification list (e.g., direct manager, HR director)

Respond ONLY with valid JSON:
{{
  "severity": "Low" | "Medium" | "High" | "Critical",
  "recommended_action": "Your recommendation",
  "notification_list": ["person1", "person2"],
  "report_summary": "Full incident summary paragraph"
}}"""


def hr_resolution_agent(state: AgentState) -> Dict[str, Any]:
    prompt = HR_SYSTEM_PROMPT.format(
        violation_type=state.get("violation_type"),
        violation_details=state.get("violation_details"),
        input_text=state.get("input_text"),
    )
    response = model.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Generate the HR incident report.")
    ])

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {
            "severity": "High",
            "recommended_action": "Escalate to HR director for manual review.",
            "notification_list": ["HR Director"],
            "report_summary": "Automated report generation failed. Manual review required.",
        }

    report = (
        f"=== HR INCIDENT REPORT ===\n"
        f"Severity          : {result['severity']}\n"
        f"Recommended Action: {result['recommended_action']}\n"
        f"Notify            : {', '.join(result.get('notification_list', []))}\n"
        f"Summary           : {result['report_summary']}\n"
    )
    log = f"[HR Agent] Severity: {result['severity']} | Action: {result['recommended_action']}"

    return {
        "final_action": result["recommended_action"],
        "resolution_report": report,
        "logs": [log],
    }


# ── 4b. Security Resolution Agent ──────────────────────────────────────────
SECURITY_SYSTEM_PROMPT = """You are a cybersecurity incident response AI.
An employee attempted to send a message containing sensitive or malicious content.

Violation type : {violation_type}
Details        : {violation_details}
Message        : "{input_text}"

Produce a security incident report. Include:
1. Threat assessment
2. Data classification of exposed information (if any)
3. Severity (Low / Medium / High / Critical)
4. Recommended actions (e.g., block email, revoke access, notify CISO)
5. Notification list

Respond ONLY with valid JSON:
{{
  "severity": "Low" | "Medium" | "High" | "Critical",
  "threat_assessment": "Description of the threat",
  "data_classification": "Public" | "Internal" | "Confidential" | "Restricted",
  "recommended_action": "Your recommendation",
  "notification_list": ["person1", "person2"],
  "report_summary": "Full incident summary paragraph"
}}"""


def security_resolution_agent(state: AgentState) -> Dict[str, Any]:
    prompt = SECURITY_SYSTEM_PROMPT.format(
        violation_type=state.get("violation_type"),
        violation_details=state.get("violation_details"),
        input_text=state.get("input_text"),
    )
    response = model.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Generate the security incident report.")
    ])

    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        result = {
            "severity": "Critical",
            "threat_assessment": "Unable to parse — treating as critical.",
            "data_classification": "Restricted",
            "recommended_action": "Block all external communications. Notify CISO immediately.",
            "notification_list": ["CISO", "IT Security Lead"],
            "report_summary": "Automated report generation failed. Immediate manual review required.",
        }

    report = (
        f"=== SECURITY INCIDENT REPORT ===\n"
        f"Severity           : {result['severity']}\n"
        f"Threat             : {result.get('threat_assessment')}\n"
        f"Data Classification: {result.get('data_classification')}\n"
        f"Recommended Action : {result['recommended_action']}\n"
        f"Notify             : {', '.join(result.get('notification_list', []))}\n"
        f"Summary            : {result['report_summary']}\n"
    )
    log = f"[Security Agent] Severity: {result['severity']} | Action: {result['recommended_action']}"

    return {
        "final_action": result["recommended_action"],
        "resolution_report": report,
        "logs": [log],
    }
