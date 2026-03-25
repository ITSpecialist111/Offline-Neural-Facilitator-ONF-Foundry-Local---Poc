from datetime import datetime

class AgendaService:
    def __init__(self, foundry_engine):
        self.foundry = foundry_engine
        self.current_topic = "Introduction"
        self.agenda_items = []
        self.last_check_time = datetime.now()

    def detect_topic(self, recent_transcript):
        """
        Uses the LLM to detect the current topic from the transcript.
        """
        prompt = f"""
        Analyze the following meeting transcript segment and determine the current topic.
        If the topic has changed from '{self.current_topic}', indicate the new topic.
        
        Transcript: 
        {recent_transcript}
        
        Output ONLY the topic name. If uncertain, output 'Unknown'.
        """
        
        new_topic = self.foundry.fast_reflex(prompt, system_prompt="You are a topic detector.")
        if new_topic and new_topic != "Unknown":
            self.current_topic = new_topic.strip()
            
        return self.current_topic

    def get_agenda_status(self):
        return {
            "current_topic": self.current_topic,
            "items": self.agenda_items
        }
