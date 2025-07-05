"""Agents base package."""
class Agent:
    """Base agent interface."""
    def __init__(self, state):
        self.state = state

    def run(self):
        raise NotImplementedError
