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
        stage = self.detect_stage(assistant_response)
        self.sessions[session_id] = {
            "context": updated.strip(),
            "stage": stage,
        }

    def detect_stage(self, response):
        """Crude detection from LLM response output suggesting next stage."""
        for stage in ["STAGE_1", "STAGE_2", "STAGE_3", "STAGE_4"]:
            if stage in response:
                return stage
        return "STAGE_1"
    
    def reset(self, session_id):
        """Clear session state, useful for restarts/testing."""
        self.sessions[session_id] = {"context": "", "stage": "STAGE_1"}
