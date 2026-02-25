# State Manager Module

class StateManager:
    def __init__(self):
        self.state = "idle"  # Default state

    def get_state(self) -> str:
        return self.state

    def set_state(self, new_state: str):
        self.state = new_state