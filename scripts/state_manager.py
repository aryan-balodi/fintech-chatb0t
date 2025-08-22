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
            # Check if category selection is confirmed by the user
            # Only move to STAGE_2 if the user explicitly confirms after seeing category options
            confirmation_words = ["yes", "correct", "right", "okay", "confirm", "proceed", "that's right", "exactly"]
            
            # Check if the bot has presented categories in its previous response
            bot_presented_categories = any(cat.lower() in response.lower() for cat in [
                "asset verification", "alternate data suite", "employment verification", 
                "onboarding", "kyc/aml", "banking", "utility bill", "credit risk"
            ])
            
            # Check if user is confirming a category choice
            user_confirming = any(word in user_input.lower() for word in confirmation_words)
            
            # Only advance if bot presented categories AND user explicitly confirmed
            if bot_presented_categories and user_confirming:
                return "STAGE_2"
            
            # Alternative: if there's a JSON output with category (final confirmation)
            if "JSON_OUTPUT" in response and "category" in response:
                return "STAGE_2"
        
        elif current_stage == "STAGE_2":
            # Check if service selection is confirmed by the user
            confirmation_words = ["yes", "correct", "right", "okay", "confirm", "proceed", "that's right", "exactly"]
            
            # Check if the bot has presented services in its previous response
            bot_presented_services = any(service.lower() in response.lower() for service in [
                "rc verification", "mobile to rc", "pan", "verification", "service"
            ])
            
            # Check if user is confirming a service choice or selecting by number
            user_confirming = any(word in user_input.lower() for word in confirmation_words)
            user_selecting_number = any(char.isdigit() for char in user_input)
            
            # Only advance if bot presented services AND user explicitly confirmed or selected
            if bot_presented_services and (user_confirming or user_selecting_number):
                return "STAGE_3"
            
            # Alternative: if there's a JSON output with service (final confirmation)
            if "JSON_OUTPUT" in response and "service" in response:
                return "STAGE_3"
        
        elif current_stage == "STAGE_3":
            # Check if vendor selection is confirmed by the user
            confirmation_words = ["yes", "correct", "right", "okay", "confirm", "proceed", "that's right", "exactly"]
            
            # Check if the bot has presented vendors in its previous response
            bot_presented_vendors = any(vendor.lower() in response.lower() for vendor in [
                "azureraven", "emeraldwhale", "scarletpanther", "goldenotter", "crimsonfalcon", 
                "sapphireswan", "onyxwolf", "cobalteagle", "silvertiger"
            ])
            
            # Check if user is confirming a vendor choice or selecting by number
            user_confirming = any(word in user_input.lower() for word in confirmation_words)
            user_selecting_number = any(char.isdigit() for char in user_input)
            
            # Only advance if bot presented vendors AND user explicitly confirmed or selected
            if bot_presented_vendors and (user_confirming or user_selecting_number):
                return "STAGE_4"
            
            # Alternative: if there's a JSON output with vendor (final confirmation)
            if "JSON_OUTPUT" in response and "vendor" in response:
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
