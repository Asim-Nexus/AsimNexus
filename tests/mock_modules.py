
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Mock modules for testing when actual modules are not available
"""

class MockBrain:
    async def think(self, prompt):
        return f"Response to: {prompt[:20]}"

class ForkResult:
    def __init__(self, strategy, response, tokens, time, confidence):
        self.strategy = strategy
        self.response = response
        self.tokens = tokens
        self.time = time
        self.confidence = confidence

class ForkStrategy:
    TECHNICAL = "technical"
    ECONOMIC = "economic"

class AgentForkManager:
    def __init__(self, brain):
        self.brain = brain
    
    async def fork_execute(self, base_prompt, strategies, num_forks):
        return [
            ForkResult(ForkStrategy.TECHNICAL, "Technical view", 100, 50, 0.8),
            ForkResult(ForkStrategy.ECONOMIC, "Economic view", 100, 50, 0.9)
        ]
    
    async def get_consensus(self, results):
        return {
            "consensus": "Consensus view",
            "confidence": 0.85,
            "diverse_views": len(results)
        }

class CompactionLevel:
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

class ContextCompactor:
    class Result:
        def __init__(self, compaction_level, original_count, compacted_count, tokens_saved):
            self.compaction_level = compaction_level
            self.original_count = original_count
            self.compacted_count = compacted_count
            self.tokens_saved = tokens_saved
    
    async def compact(self, history, token_budget):
        if len(history) * 100 < token_budget:
            return self.Result(CompactionLevel.NONE, len(history), len(history), 0)
        return self.Result(CompactionLevel.MEDIUM, len(history), len(history)//2, len(history)*50)

class CodeChange:
    def __init__(self, path, operation, new_content=None):
        self.path = path
        self.operation = operation
        self.new_content = new_content

class ExecutionPlan:
    def __init__(self, description, changes, test_commands, estimated_risk):
        self.description = description
        self.changes = changes
        self.test_commands = test_commands
        self.estimated_risk = estimated_risk

class GitWorktreeSandbox:
    def __init__(self, repo_path):
        self.repo_path = repo_path
    
    async def create_sandbox(self, plan):
        return f"worktree_{id(plan)}"

class LifeMode:
    GUARDIAN = "guardian"
    EMPIRE = "empire"

class ModeManager:
    def __init__(self):
        self.current_mode = LifeMode.GUARDIAN
    
    async def switch_mode(self, mode, reason):
        self.current_mode = mode
        return {"success": True, "mode": mode, "reason": reason}
    
    def check_dharma_compliance(self, query):
        if "colleague" in query or "work" in query.lower():
            return True, "Work query compliant"
        return False, "Personal query blocked - use GUARDIAN mode"

class Priority:
    CRITICAL = "critical"
    NORMAL = "normal"
    LOW = "low"

class Message:
    def __init__(self, msg_id, sender, recipient, priority, payload):
        self.msg_id = msg_id
        self.sender = sender
        self.recipient = recipient
        self.priority = priority
        self.payload = payload

class AgentMailbox:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.messages = []
    
    async def enqueue(self, message):
        self.messages.append(message)
    
    async def receive(self, timeout=1.0):
        if not self.messages:
            return None
        # Return highest priority first
        self.messages.sort(key=lambda m: m.priority)
        return self.messages.pop(0)

class ASIMBrain:
    async def _spiritual_brain_fallback(self, prompt):
        return f"🕉️ Spiritual response to: {prompt}"
