"""
Demo script for the Multi-Agent Security System.
Runs four scenarios and saves detailed logs to the logs/ directory.

Usage:
    export GROQ_API_KEY="your-key-here"
    python demo.py
"""

import os
import sys
import datetime

# Ensure package imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph import create_graph

MAX_RECURSION_LIMIT = 50
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


def divider(char="─", width=70):
    return char * width


def run_scenario(name: str, initial_state: dict) -> None:
    """Run a single scenario through the agent graph and save logs."""
    print(f"\n{'═' * 70}")
    print(f"  SCENARIO: {name}")
    print(f"{'═' * 70}")

    app = create_graph()
    config = {"recursion_limit": MAX_RECURSION_LIMIT}

    try:
        final_state = app.invoke(initial_state, config=config)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    # ── Print logs to console ───────────────────────────────────────────
    logs = final_state.get("logs", [])
    print(f"\n{divider()}")
    print("  EXECUTION LOG")
    print(divider())
    for i, log in enumerate(logs, 1):
        print(f"  {i}. {log}")
    print(divider())

    # Print resolution report if one exists
    report = final_state.get("resolution_report")
    if report:
        print(f"\n{divider()}")
        print("  RESOLUTION REPORT")
        print(divider())
        for line in report.strip().split("\n"):
            print(f"  {line}")
        print(divider())

    final_action = final_state.get("final_action", "Message allowed – no violation.")
    print(f"\n  ✅ Final Action: {final_action}")

    # ── Save to log file ────────────────────────────────────────────────
    os.makedirs(LOG_DIR, exist_ok=True)
    log_name = name.replace(" ", "_").lower()
    log_file = os.path.join(LOG_DIR, f"{log_name}.txt")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "w") as f:
        f.write(f"{'=' * 60}\n")
        f.write(f"SCENARIO      : {name}\n")
        f.write(f"TIMESTAMP     : {timestamp}\n")
        f.write(f"INPUT         : {initial_state.get('input_text')}\n")
        f.write(f"USER ACTION   : {initial_state.get('user_action', 'N/A')}\n")
        f.write(f"{'=' * 60}\n\n")

        f.write("EXECUTION LOG:\n")
        f.write("-" * 60 + "\n")
        for i, log in enumerate(logs, 1):
            f.write(f"  {i}. {log}\n")
        f.write("-" * 60 + "\n\n")

        if final_state.get("interaction_message"):
            f.write(f"NUDGE MESSAGE : {final_state['interaction_message']}\n\n")

        if final_state.get("routing_rationale"):
            f.write(f"ROUTING REASON: {final_state['routing_rationale']}\n\n")

        if report:
            f.write("RESOLUTION REPORT:\n")
            f.write(report + "\n")

        f.write(f"FINAL ACTION  : {final_action}\n")

    print(f"  📄 Log saved: {log_file}")


def main():
    print("\n" + "█" * 70)
    print("  MULTI-AGENT SECURITY SYSTEM — DEMO")
    print("█" * 70)

    # Check for API key
    if not os.environ.get("GROQ_API_KEY"):
        print("\n  ⚠️  GROQ_API_KEY environment variable is not set!")
        print("  Set it with: export GROQ_API_KEY='your-key-here'")
        sys.exit(1)

    # ── Scenario 1: Safe Email ──────────────────────────────────────────
    run_scenario("Safe Email", {
        "input_text": "Hi team, the project meeting is rescheduled to 3 PM tomorrow. Please update your calendars.",
        "sender": "alice@company.com",
        "recipient": "team@company.com",
        "user_action": None,
        "logs": [],
    })

    # ── Scenario 2: Toxic Message → User Edits ─────────────────────────
    run_scenario("Toxicity - User Edits", {
        "input_text": "You are an absolute idiot and I hate working with you. You ruin everything.",
        "sender": "bob@company.com",
        "recipient": "carol@company.com",
        "user_action": "Edit",
        "logs": [],
    })

    # ── Scenario 3: Toxic Message → User Overrides → HR ────────────────
    run_scenario("Toxicity - Override to HR", {
        "input_text": "I swear I will make your life miserable if you don't do what I say.",
        "sender": "dave@company.com",
        "recipient": "eve@company.com",
        "user_action": "Override",
        "logs": [],
    })

    # ── Scenario 4: Data Leak → User Overrides → Security ──────────────
    run_scenario("Data Leak - Override to Security", {
        "input_text": "Hey, the production database password is SuperSecret123 and the API key is sk-abc123xyz.",
        "sender": "frank@company.com",
        "recipient": "external-vendor@gmail.com",
        "user_action": "Override",
        "logs": [],
    })


    run_scenario("Data Leak - Override to Security", {
        "input_text": "Hey, the production database password is SuperSecret123 and the API key is sk-abc123xyz.",
        "sender": "frank@company.com",
        "recipient": "external-vendor@gmail.com",
        "user_action": "Override",
        "logs": [],
    })

    print(f"\n{'█' * 70}")
    print(f"  ALL SCENARIOS COMPLETE — Logs saved in: {LOG_DIR}")
    print(f"{'█' * 70}\n")


if __name__ == "__main__":
    main()
