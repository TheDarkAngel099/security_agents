from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
from ..core.graph import create_graph

router = APIRouter()

# Instantiate the graph once (or per request if stateful, but here we want stateless execution from API perspective)
# However, LangGraph is stateful. We need to handle state.
# For the demo, we'll instantiate a new graph runner or use a compiled one.
app_graph = create_graph()

# In-memory storage for demo purposes (since we need to pass state between steps)
# In production, use LangGraph's checkpointer or DB.
# We will use the SQL DB to store the state implicitly via 'Incident' and 'Log'.

@router.post("/scan", response_model=schemas.ScanResponse)
def scan_message(request: schemas.ScanRequest, db: Session = Depends(database.get_db)):
    """
    Initial scan: User drafts a message.
    Runs 'detection' and 'interaction' (if needed).
    Does NOT create an incident yet, or creates a temporary one?
    For the logic:
    1. Run detection.
    2. If violation -> Run interaction -> Return nudge.
    3. If no violation -> Return Clean.
    """
    
    initial_state = {
        "input_text": request.text,
        "sender": request.sender,
        "recipient": request.recipient,
        "user_action": None,
        "logs": []
    }
    
    # We want to run until we hit a "human" node or end.
    # The graph: detection -> (interaction | END)
    # If interaction -> routing (if override) -> ...
    
    # We can run the graph and inspect the output.
    # The graph is designed to run autonomously until END usually, but 'interaction' implies a stop?
    # Actually checking graph.py: 
    # detection -> should_interact -> interaction OR END.
    # interaction -> interaction_result (based on user_action) -> detection OR routing.
    
    # So if we run with user_action=None, it goes:
    # detection -> (if violation) -> interaction ->... 
    # interaction agent generates nudge.
    # But then what? usage of 'user_action' in 'interaction_agent'
    # 'user_action' defaults to "Override" in `interaction_agent` if not present?
    # line 123: user_action = state.get("user_action", "Override")
    
    # Wait, if we just want to SHOW the nudge, we should stop after interaction agent?
    # The current graph design assumes a continuous run.
    # We might need to modify the graph to be more step-by-step or use interrupt hooks.
    # OR for the /scan endpoint, we just run detection. 
    # If detection says violation, we run interaction agent specifically to get the nudge.
    
    # Let's import the agents directly for granular control in this API, 
    # OR modify the graph to have a breakpoint.
    
    # Option B: Run detection_agent directly.
    from ..core.agents import detection_agent, interaction_agent
    
    # 1. Detect
    detection_result = detection_agent(initial_state)
    
    response = schemas.ScanResponse(
        violation_detected=detection_result["violation_detected"],
        violation_type=detection_result.get("violation_type"),
        violation_details=detection_result.get("violation_details"),
        nudge_message=None,
        suggested_rewrite=None
    )
    
    if detection_result["violation_detected"]:
        # 2. Get Nudge
        # Interaction agent needs the detection details
        state_for_interaction = {**initial_state, **detection_result}
        interaction_result = interaction_agent(state_for_interaction)
        
        response.nudge_message = interaction_result["interaction_message"]
        # The interaction agent also returns 'suggested_rewrite' in the result dict inside the func but returns 'updates'
        # Let's check interaction_agent code.
        # It calls parse_json_response which gives 'nudge_message' and 'suggested_rewrite'.
        # It logs them.
        # It returns updates: "interaction_message", "logs", and if Edit, "input_text".
        # It does NOT return 'suggested_rewrite' in the returned dict explicitly?
        # Line 130: updates = {"interaction_message": ..., "logs": ...}
        # Line 137: update "input_text" if Edit.
        # Valid point. existing interaction_agent code suppresses 'suggested_rewrite' from the return if not editing?
        # We might need to modify interaction_agent to return 'suggested_rewrite' so we can show it to UI.
        
        pass # We will need to check/fix interaction_agent.
        
    return response

@router.post("/submit", response_model=schemas.SubmitActionResponse)
def submit_action(request: schemas.SubmitActionRequest, db: Session = Depends(database.get_db)):
    """
    User decides to Edit or Override.
    If Edit: Text is updated. Re-scan.
    If Override: Incident is created and routed to HR/Sec.
    """
    
    # If Override
    if request.action == "Override":
        # Run Routing -> Resolution
        # We can construct the state and run the graph from 'routing' node?
        # Or just run the agents.
        
        from ..core.agents import routing_agent, hr_resolution_agent, security_resolution_agent
        
        state = {
            "input_text": request.text,
            "violation_type": request.previous_violation_type,
            "violation_details": request.previous_violation_details,
            "user_action": "Override"
        }
        
        # 1. Route
        routing_result = routing_agent(state)
        dest = routing_result["resolution_agent"] # HR or Security
        
        # 2. Resolve
        state.update(routing_result)
        resolution_report = ""
        owner = dest
        
        if dest == "HR":
            hr_result = hr_resolution_agent(state)
            resolution_report = hr_result["resolution_report"]
        else: # Security
            sec_result = security_resolution_agent(state)
            resolution_report = sec_result["resolution_report"]
            
        # 3. Create Incident in DB
        incident = models.Incident(
            original_text=request.text,
            sender=request.sender,
            recipient=request.recipient,
            violation_type=request.previous_violation_type,
            violation_details=request.previous_violation_details,
            risk_level=routing_result.get("risk_level", "Medium"),
            status="Pending",
            owner_role=owner,
            resolution_notes=None # To be filled by human
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        # Log the automated report
        log = models.Log(
            incident_id=incident.id,
            agent=dest + " Agent",
            message=resolution_report
        )
        db.add(log)
        db.commit()
        
        return {"status": "Escalated", "incident_id": incident.id}
    
    elif request.action == "Edit":
        # Just return status ok, frontend will call /scan again with new text
        return {"status": "Edited", "incident_id": None}
        
    return {"status": "Unknown", "incident_id": None}
