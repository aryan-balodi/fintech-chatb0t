class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def get_context(self, session_id):
        """Get entire session history (chat log)."""
        return self.sessions.get(session_id, {}).get("context", "")
    
    def get_stage(self, session_id):
        """Fetch the current stage of the user conversation."""
        return self.sessions.get(session_id, {}).get("stage", "STAGE_1")
    
    def update(self, session_id, user_input, assistant_response):
        """Append new turn to session chat history."""
        history = self.get_context(session_id)
        updated = (
            history
            + f"\nUser: {user_input}\nAssistant: {assistant_response.strip()}"
        )
        new_stage = self.detect_stage(assistant_response, user_input, history)
        prev_stage = self.get_stage(session_id)
        # Only allow forward progression
        stage_order = ["STAGE_1", "STAGE_2", "STAGE_3", "STAGE_4"]
        if stage_order.index(new_stage) < stage_order.index(prev_stage):
            new_stage = prev_stage
        self.sessions[session_id] = {
            "context": updated.strip(),
            "stage": new_stage,
        }

    def detect_stage(self, response, user_input, history):
        """Intelligent stage detection based on conversation content."""
        current_stage = self.get_stage_from_history(history)
        
        # Stage progression logic
        if current_stage == "STAGE_1":
            # Check if category selection is complete
            if any(category in response.lower() for category in ["kyc/aml", "employment verification", "onboarding"]):
                if "confirm" in response.lower() and any(word in user_input.lower() for word in ["yes", "correct", "right", "okay", "confirm"]):
                    return "STAGE_2"
        
        elif current_stage == "STAGE_2":
            # Check if service selection is complete
            if any(service in response.lower() for service in ["pan_advanced", "pan_to_gst", "pan_to_uan", "mobile_to_uan", "uan_basic", "gst_basic"]):
                if "confirm" in response.lower() and any(word in user_input.lower() for word in ["yes", "correct", "right", "okay", "confirm"]):
                    return "STAGE_3"
        
        elif current_stage == "STAGE_3":
            # Check if vendor selection is complete
            if any(vendor in response.lower() for vendor in ["azureraven", "emeraldwhale", "scarletpanther", "goldenotter", "crimsonfalcon", "sapphireswan", "onyxwolf", "cobalteagle", "silvertiger"]):
                if "confirm" in response.lower() and any(word in user_input.lower() for word in ["yes", "correct", "right", "okay", "confirm"]):
                    return "STAGE_4"
        
        elif current_stage == "STAGE_4":
            # STAGE_4 is the final stage - never go back
            return "STAGE_4"
        
        return current_stage
    
    def get_stage_from_history(self, history):
        """Extract current stage from conversation history."""
        if not history:
            return "STAGE_1"
        
        # Look for the most recent stage mention in the history
        stages = ["STAGE_4", "STAGE_3", "STAGE_2", "STAGE_1"]
        for stage in stages:
            if stage in history:
                return stage
        
        return "STAGE_1"
    
    def reset(self, session_id):
        """Clear session state, useful for restarts/testing."""
        self.sessions[session_id] = {"context": "", "stage": "STAGE_1"}
