
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Clone Direct Interaction - Human-Centric Interface
============================================================
Users talk to their Clone, not code or portals
Clone Auto-Navigates everything
Natural language interface for all ASIMNEXUS features
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger("CloneDirectInteraction")

class IntentCategory(Enum):
    """Categories of user intents"""
    TASK_EXECUTION = "task_execution"
    INFORMATION_QUERY = "information_query"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    TRANSACTION = "transaction"
    SYSTEM_CONTROL = "system_control"

class InteractionMode(Enum):
    """Interaction modes"""
    VOICE = "voice"
    TEXT = "text"
    GESTURE = "gesture"
    HYBRID = "hybrid"

@dataclass
class UserMessage:
    """Message from user to clone"""
    message_id: str
    user_id: str
    content: str
    mode: InteractionMode
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CloneResponse:
    """Response from clone to user"""
    response_id: str
    message_id: str
    content: str
    intent_category: IntentCategory
    actions_taken: List[str]
    confidence_score: float
    timestamp: datetime
    requires_confirmation: bool = False
    confirmation_options: List[str] = field(default_factory=list)

@dataclass
class NavigationStep:
    """Step in auto-navigation process"""
    step_id: str
    action: str
    target: str
    parameters: Dict[str, Any]
    status: str  # "pending", "completed", "failed"
    timestamp: datetime
    result: Optional[Dict[str, Any]] = None

class CloneDirectInteraction:
    """
    Clone Direct Interaction - Human-Centric Interface
    Users talk to their Clone, not code or portals
    Clone Auto-Navigates everything
    Natural language interface for all ASIMNEXUS features
    """
    
    def __init__(self):
        self.user_messages: Dict[str, UserMessage] = {}
        self.clone_responses: Dict[str, CloneResponse] = {}
        self.navigation_history: List[NavigationStep] = []
        self.clone_personality = {
            "name": "Nexus Clone",
            "tone": "helpful",
            "language": "nepali_english",
            "proactive": True
        }
        
        # Initialize interface
        self._initialize_interface()
        
    def _initialize_interface(self) -> None:
        """Initialize the Clone Direct Interaction interface"""
        logger.info("🤖 Initializing Clone Direct Interaction - Human-Centric Interface...")
        logger.info("💬 User talks to Clone, not code/portals")
        logger.info("🧭 Clone Auto-Navigates everything")
        logger.info("🌐 Natural language interface")
        logger.info("✅ Clone Direct Interaction initialized")
    
    async def process_user_message(
        self,
        user_id: str,
        content: str,
        mode: InteractionMode = InteractionMode.TEXT,
        context: Dict[str, Any] = None
    ) -> CloneResponse:
        """
        Process user message and generate clone response
        Clone auto-navigates to fulfill user request
        """
        try:
            logger.info(f"💬 Processing user message from: {user_id}")
            logger.info(f"   Content: {content}")
            logger.info(f"   Mode: {mode.value}")
            
            # Create user message
            message = UserMessage(
                message_id=f"msg_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                content=content,
                mode=mode,
                timestamp=datetime.utcnow(),
                context=context or {}
            )
            
            self.user_messages[message.message_id] = message
            
            # Understand intent
            intent = await self._understand_intent(message)
            
            # Auto-navigate to fulfill request
            navigation_steps = await self._auto_navigate(message, intent)
            
            # Generate response
            response = await self._generate_response(message, intent, navigation_steps)
            
            self.clone_responses[response.response_id] = response
            
            logger.info(f"✅ Clone response generated: {response.response_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")
            raise
    
    async def _understand_intent(self, message: UserMessage) -> Dict[str, Any]:
        """Understand user intent from message"""
        try:
            content_lower = message.content.lower()
            
            # Classify intent category
            if any(keyword in content_lower for keyword in ["send", "email", "message", "whatsapp", "call"]):
                intent_category = IntentCategory.COMMUNICATION
            elif any(keyword in content_lower for keyword in ["pay", "transfer", "buy", "purchase"]):
                intent_category = IntentCategory.TRANSACTION
            elif any(keyword in content_lower for keyword in ["automate", "schedule", "remind", "task"]):
                intent_category = IntentCategory.AUTOMATION
            elif any(keyword in content_lower for keyword in ["what", "how", "tell me", "show"]):
                intent_category = IntentCategory.INFORMATION_QUERY
            elif any(keyword in content_lower for keyword in ["do", "execute", "run", "perform"]):
                intent_category = IntentCategory.TASK_EXECUTION
            else:
                intent_category = IntentCategory.INFORMATION_QUERY
            
            # Extract key information
            entities = self._extract_entities(message.content)
            
            return {
                "intent_category": intent_category,
                "entities": entities,
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"❌ Intent understanding error: {e}")
            return {"intent_category": IntentCategory.INFORMATION_QUERY, "entities": {}, "confidence": 0.5}
    
    def _extract_entities(self, content: str) -> Dict[str, Any]:
        """Extract entities from user message"""
        entities = {}
        
        # Extract email addresses
        if "@" in content:
            entities["email"] = [word for word in content.split() if "@" in word]
        
        # Extract phone numbers
        import re
        phone_pattern = r'\+?\d{10,15}'
        phones = re.findall(phone_pattern, content)
        if phones:
            entities["phone"] = phones
        
        # Extract amounts (NPR)
        amount_pattern = r'npr\s*\d+'
        amounts = re.findall(amount_pattern, content, re.IGNORECASE)
        if amounts:
            entities["amount"] = amounts
        
        return entities
    
    async def _auto_navigate(
        self,
        message: UserMessage,
        intent: Dict[str, Any]
    ) -> List[NavigationStep]:
        """
        Auto-navigate through system to fulfill user request
        Clone handles all navigation automatically
        """
        try:
            logger.info(f"🧭 Auto-navigating for: {message.content}")
            
            navigation_steps = []
            intent_category = intent["intent_category"]
            entities = intent["entities"]
            
            # Navigate based on intent category
            if intent_category == IntentCategory.COMMUNICATION:
                steps = await self._navigate_communication(message, entities)
                navigation_steps.extend(steps)
            elif intent_category == IntentCategory.TRANSACTION:
                steps = await self._navigate_transaction(message, entities)
                navigation_steps.extend(steps)
            elif intent_category == IntentCategory.AUTOMATION:
                steps = await self._navigate_automation(message, entities)
                navigation_steps.extend(steps)
            elif intent_category == IntentCategory.TASK_EXECUTION:
                steps = await self._navigate_task_execution(message, entities)
                navigation_steps.extend(steps)
            else:
                # Information query
                steps = await self._navigate_information(message, entities)
                navigation_steps.extend(steps)
            
            # Store navigation history
            for step in navigation_steps:
                self.navigation_history.append(step)
            
            logger.info(f"✅ Auto-navigation complete: {len(navigation_steps)} steps")
            return navigation_steps
            
        except Exception as e:
            logger.error(f"❌ Auto-navigation error: {e}")
            return []
    
    async def _navigate_communication(
        self,
        message: UserMessage,
        entities: Dict[str, Any]
    ) -> List[NavigationStep]:
        """Navigate communication actions"""
        steps = []
        
        # Step 1: Identify communication channel
        step1 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="identify_channel",
            target="communication_system",
            parameters={},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"channel": "whatsapp" if "whatsapp" in message.content.lower() else "email"}
        )
        steps.append(step1)
        
        # Step 2: Get recipient information
        step2 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="get_recipient",
            target="contact_system",
            parameters=entities,
            status="completed",
            timestamp=datetime.utcnow(),
            result={"recipient": entities.get("email", entities.get("phone", ["unknown"])[0]) if entities else "unknown"}
        )
        steps.append(step2)
        
        # Step 3: Compose message
        step3 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="compose_message",
            target="messaging_agent",
            parameters={"content": message.content},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"message_composed": True}
        )
        steps.append(step3)
        
        # Step 4: Send message
        step4 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="send_message",
            target="messaging_agent",
            parameters={},
            status="pending",
            timestamp=datetime.utcnow()
        )
        steps.append(step4)
        
        return steps
    
    async def _navigate_transaction(
        self,
        message: UserMessage,
        entities: Dict[str, Any]
    ) -> List[NavigationStep]:
        """Navigate transaction actions"""
        steps = []
        
        # Step 1: Identify transaction type
        step1 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="identify_transaction",
            target="economy_system",
            parameters={},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"type": "payment"}
        )
        steps.append(step1)
        
        # Step 2: Get amount
        step2 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="get_amount",
            target="economy_system",
            parameters=entities,
            status="completed",
            timestamp=datetime.utcnow(),
            result={"amount": entities.get("amount", ["0"])[0] if entities else "0"}
        )
        steps.append(step2)
        
        # Step 3: Verify balance
        step3 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="verify_balance",
            target="economy_system",
            parameters={},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"sufficient": True}
        )
        steps.append(step3)
        
        # Step 4: Process transaction
        step4 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="process_transaction",
            target="economy_system",
            parameters={},
            status="pending",
            timestamp=datetime.utcnow()
        )
        steps.append(step4)
        
        return steps
    
    async def _navigate_automation(
        self,
        message: UserMessage,
        entities: Dict[str, Any]
    ) -> List[NavigationStep]:
        """Navigate automation actions"""
        steps = []
        
        # Step 1: Identify automation type
        step1 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="identify_automation",
            target="automation_system",
            parameters={},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"type": "task_automation"}
        )
        steps.append(step1)
        
        # Step 2: Create automation
        step2 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="create_automation",
            target="automation_system",
            parameters={"description": message.content},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"automation_created": True}
        )
        steps.append(step2)
        
        return steps
    
    async def _navigate_task_execution(
        self,
        message: UserMessage,
        entities: Dict[str, Any]
    ) -> List[NavigationStep]:
        """Navigate task execution actions"""
        steps = []
        
        # Step 1: Identify task
        step1 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="identify_task",
            target="task_system",
            parameters={},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"task": message.content}
        )
        steps.append(step1)
        
        # Step 2: Execute task
        step2 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="execute_task",
            target="task_system",
            parameters={},
            status="pending",
            timestamp=datetime.utcnow()
        )
        steps.append(step2)
        
        return steps
    
    async def _navigate_information(
        self,
        message: UserMessage,
        entities: Dict[str, Any]
    ) -> List[NavigationStep]:
        """Navigate information query actions"""
        steps = []
        
        # Step 1: Identify information type
        step1 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="identify_info",
            target="information_system",
            parameters={},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"type": "general_query"}
        )
        steps.append(step1)
        
        # Step 2: Retrieve information
        step2 = NavigationStep(
            step_id=f"step_{uuid.uuid4().hex[:12]}",
            action="retrieve_info",
            target="information_system",
            parameters={"query": message.content},
            status="completed",
            timestamp=datetime.utcnow(),
            result={"information_retrieved": True}
        )
        steps.append(step2)
        
        return steps
    
    async def _generate_response(
        self,
        message: UserMessage,
        intent: Dict[str, Any],
        navigation_steps: List[NavigationStep]
    ) -> CloneResponse:
        """Generate clone response to user"""
        try:
            intent_category = intent["intent_category"]
            
            # Generate response based on intent
            if intent_category == IntentCategory.COMMUNICATION:
                content = f"मैले तपाईंको सन्देश पठाउनेछु। Clone ले स्वचालित रूपमा WhatsApp/Email मा जानेछ।"
                requires_confirmation = True
                confirmation_options = ["Yes, send it", "No, cancel", "Edit message"]
            elif intent_category == IntentCategory.TRANSACTION:
                content = f"मैले तपाईंको ट्रान्जेक्सन प्रोसेस गर्नेछु। Clone ले Nexus Credits प्रयोग गरेर सुरक्षित रूपमा पैसा पठाउनेछ।"
                requires_confirmation = True
                confirmation_options = ["Confirm transaction", "Cancel"]
            elif intent_category == IntentCategory.AUTOMATION:
                content = f"मैले तपाईंको अटोमेशन सेट गर्नेछु। Clone ले यो काम स्वचालित रूपमा गर्नेछ।"
                requires_confirmation = True
                confirmation_options = ["Create automation", "Cancel"]
            elif intent_category == IntentCategory.TASK_EXECUTION:
                content = f"मैले तपाईंको काम गर्नेछु। Clone ले आवश्यक सबै कदम चलाउनेछ।"
                requires_confirmation = True
                confirmation_options = ["Execute task", "Cancel"]
            else:
                content = f"मैले तपाईंको प्रश्नको उत्तर दिनेछु। Clone ले आवश्यक जानकारी खोज्नेछ।"
                requires_confirmation = False
                confirmation_options = []
            
            response = CloneResponse(
                response_id=f"resp_{uuid.uuid4().hex[:12]}",
                message_id=message.message_id,
                content=content,
                intent_category=intent_category,
                actions_taken=[step.action for step in navigation_steps],
                confidence_score=intent.get("confidence", 0.85),
                timestamp=datetime.utcnow(),
                requires_confirmation=requires_confirmation,
                confirmation_options=confirmation_options
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            raise
    
    async def handle_confirmation(
        self,
        response_id: str,
        confirmation: str
    ) -> bool:
        """Handle user confirmation for clone action"""
        try:
            response = self.clone_responses.get(response_id)
            
            if not response:
                return False
            
            logger.info(f"✅ Confirmation received: {confirmation}")
            
            # Execute pending navigation steps
            for step in self.navigation_history:
                if step.status == "pending":
                    step.status = "completed"
                    step.result = {"executed": True}
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Confirmation handling error: {e}")
            return False
    
    def get_interaction_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get interaction history for user"""
        user_messages = [
            msg for msg in self.user_messages.values()
            if msg.user_id == user_id
        ]
        
        # Sort by timestamp (newest first)
        user_messages.sort(key=lambda m: m.timestamp, reverse=True)
        
        history = []
        for msg in user_messages[:limit]:
            response = self.clone_responses.get(
                next((r.message_id for r in self.clone_responses.values() if r.message_id == msg.message_id), None)
            )
            
            history.append({
                "message_id": msg.message_id,
                "content": msg.content,
                "mode": msg.mode.value,
                "timestamp": msg.timestamp.isoformat(),
                "response": response.content if response else None,
                "intent_category": response.intent_category.value if response else None
            })
        
        return history

# Global Clone Direct Interaction instance
_clone_direct_interaction = CloneDirectInteraction()

async def main():
    """Main entry point for testing"""
    # Process user message
    response = await _clone_direct_interaction.process_user_message(
        user_id="user_001",
        content="Send email to john@example.com about the project update",
        mode=InteractionMode.TEXT
    )
    
    print(f"Clone Response: {response.content}")
    print(f"Intent: {response.intent_category.value}")
    print(f"Actions: {response.actions_taken}")
    print(f"Requires Confirmation: {response.requires_confirmation}")
    
    # Get interaction history
    history = _clone_direct_interaction.get_interaction_history("user_001")
    print(f"Interaction History: {json.dumps(history, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
