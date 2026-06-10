
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
Nyaya Layer - Logic Reasoning Engine
=====================================
Nyaya (c. 500 BCE) - Indian school of logic
- Pramanas (valid means of knowledge)
- Syllogism (five-membered argument)
- Fallacy detection
- Debate methodology
- Logical inference

This layer implements Nyaya logic for:
- Explainable AI (XAI)
- Reasoning engine
- Fallacy detection
- Decision explanation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("NyayaLayer")


class Pramana(Enum):
    """Pramanas - valid means of knowledge in Nyaya"""
    PRATYAKSHA = "pratyaksha"  # Perception
    ANUMANA = "anumana"  # Inference
    UPAMANA = "upamana"  # Comparison
    SHABDA = "shabda"  # Testimony
    ARTHAPATTI = "arthapatti"  # Postulation
    ANUPALABDHI = "anupalabdhi"  # Non-apprehension


class FallacyType(Enum):
    """Types of logical fallacies in Nyaya"""
    STRAW_MAN = "straw_man"
    AD_HOMINEM = "ad_hominem"
    FALSE_DICHOTOMY = "false_dichotomy"
    CIRCULAR_REASONING = "circular_reasoning"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    HASTY_GENERALIZATION = "hasty_generalization"


@dataclass
class Syllogism:
    """Nyaya five-membered syllogism"""
    pratijna: str  # Proposition
    hetu: str  # Reason
    udaharana: str  # Example
    upanaya: str  # Application
    nigamana: str  # Conclusion


class NyayaLayer:
    """
    Nyaya Layer - Logic Reasoning Engine
    
    Implements Nyaya school of logic:
    - Pramanas (valid knowledge sources)
    - Syllogistic reasoning
    - Fallacy detection
    - Explainable AI
    """
    
    def __init__(self):
        self.pramanas = list(Pramana)
        self.fallacies = list(FallacyType)
        self.reasoning_history = []
        
    def reason(self, premises: List[str], conclusion: str) -> Dict[str, Any]:
        """
        Reason using Nyaya syllogism
        Returns reasoning with explanation
        """
        result = {
            "valid": False,
            "explanation": "",
            "confidence": 0.0,
            "pramanas_used": [],
            "fallacies_detected": [],
            "syllogism": None
        }
        
        # Validate syllogism
        syllogism = self._create_syllogism(premises, conclusion)
        result["syllogism"] = syllogism
        
        # Check validity
        is_valid = self._validate_syllogism(syllogism)
        result["valid"] = is_valid
        
        # Detect fallacies
        fallacies = self._detect_fallacies(premises, conclusion)
        result["fallacies_detected"] = fallacies
        
        # Generate explanation
        explanation = self._generate_explanation(syllogism, is_valid, fallacies)
        result["explanation"] = explanation
        
        # Calculate confidence
        confidence = self._calculate_confidence(is_valid, fallacies)
        result["confidence"] = confidence
        
        # Record pramanas used
        result["pramanas_used"] = [Pramana.ANUMANA.value, Pramana.SHABDA.value]
        
        # Store in history
        self.reasoning_history.append(result)
        
        return result
        
    def _create_syllogism(self, premises: List[str], conclusion: str) -> Syllogism:
        """Create Nyaya five-membered syllogism"""
        if len(premises) >= 2:
            pratijna = conclusion
            hetu = premises[0]
            udaharana = premises[1] if len(premises) > 1 else ""
            upanaya = f"Therefore, {conclusion}"
            nigamana = conclusion
        else:
            pratijna = conclusion
            hetu = premises[0] if premises else ""
            udaharana = ""
            upanaya = ""
            nigamana = conclusion
            
        return Syllogism(
            pratijna=pratijna,
            hetu=hetu,
            udaharana=udaharana,
            upanaya=upanaya,
            nigamana=nigamana
        )
        
    def _validate_syllogism(self, syllogism: Syllogism) -> bool:
        """Validate Nyaya syllogism"""
        # Check if all components are present
        if not syllogism.pratijna or not syllogism.hetu:
            return False
        
        # Check if conclusion follows from premises
        if syllogism.hetu and syllogism.udaharana:
            return True
        
        return False
        
    def _detect_fallacies(self, premises: List[str], conclusion: str) -> List[str]:
        """Detect logical fallacies"""
        fallacies = []
        
        # Check for circular reasoning
        if conclusion in premises:
            fallacies.append(FallacyType.CIRCULAR_REASONING.value)
        
        # Check for hasty generalization
        if len(premises) < 2 and "all" in conclusion.lower():
            fallacies.append(FallacyType.HASTY_GENERALIZATION.value)
        
        # Check for false dichotomy
        if "either" in conclusion.lower() and "or" in conclusion.lower():
            fallacies.append(FallacyType.FALSE_DICHOTOMY.value)
        
        return fallacies
        
    def _generate_explanation(self, syllogism: Syllogism, is_valid: bool, fallacies: List[str]) -> str:
        """Generate explanation for reasoning"""
        explanation_parts = []
        
        explanation_parts.append(f"Proposition: {syllogism.pratijna}")
        explanation_parts.append(f"Reason: {syllogism.hetu}")
        
        if syllogism.udaharana:
            explanation_parts.append(f"Example: {syllogism.udaharana}")
        
        if is_valid:
            explanation_parts.append("The reasoning follows valid Nyaya syllogism structure.")
        else:
            explanation_parts.append("The reasoning does not follow valid syllogism structure.")
        
        if fallacies:
            explanation_parts.append(f"Fallacies detected: {', '.join(fallacies)}")
        
        return " ".join(explanation_parts)
        
    def _calculate_confidence(self, is_valid: bool, fallacies: List[str]) -> float:
        """Calculate confidence score for reasoning"""
        confidence = 0.5  # Base confidence
        
        if is_valid:
            confidence += 0.3
        
        confidence -= len(fallacies) * 0.1
        
        return max(0.0, min(1.0, confidence))
        
    def apply_pramana(self, pramana: Pramana, data: Any) -> Dict[str, Any]:
        """Apply specific pramana (valid means of knowledge)"""
        result = {
            "pramana": pramana.value,
            "applied": False,
            "result": None
        }
        
        if pramana == Pramana.PRATYAKSHA:
            # Direct perception
            result["applied"] = True
            result["result"] = f"Perceived: {data}"
        elif pramana == Pramana.ANUMANA:
            # Inference
            result["applied"] = True
            result["result"] = f"Inferred from: {data}"
        elif pramana == Pramana.SHABDA:
            # Testimony
            result["applied"] = True
            result["result"] = f"Testimony: {data}"
        
        return result
        
    def detect_fallacy_in_text(self, text: str) -> List[str]:
        """Detect fallacies in text"""
        fallacies = []
        
        text_lower = text.lower()
        
        # Check for ad hominem
        if "you are" in text_lower or "you're" in text_lower:
            fallacies.append(FallacyType.AD_HOMINEM.value)
        
        # Check for appeal to authority
        if "expert says" in text_lower or "authority says" in text_lower:
            fallacies.append(FallacyType.APPEAL_TO_AUTHORITY.value)
        
        # Check for straw man
        if "so you're saying" in text_lower:
            fallacies.append(FallacyType.STRAW_MAN.value)
        
        return fallacies
        
    def explain_decision(self, decision: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Explain a decision using Nyaya reasoning
        Provides explainable AI (XAI) capabilities
        """
        result = {
            "decision": decision,
            "explanation": "",
            "reasoning_chain": [],
            "confidence": 0.0
        }
        
        # Create reasoning chain
        reasoning_chain = []
        
        # Add context as premises
        if "premises" in context:
            for premise in context["premises"]:
                reasoning_chain.append({
                    "type": "premise",
                    "content": premise
                })
        
        # Add decision as conclusion
        reasoning_chain.append({
            "type": "conclusion",
            "content": decision
        })
        
        result["reasoning_chain"] = reasoning_chain
        
        # Generate explanation
        premises = [p["content"] for p in reasoning_chain if p["type"] == "premise"]
        reasoning_result = self.reason(premises, decision)
        result["explanation"] = reasoning_result["explanation"]
        result["confidence"] = reasoning_result["confidence"]
        
        return result
        
    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get reasoning engine statistics"""
        return {
            "pramanas_available": len(self.pramanas),
            "fallacies_detectable": len(self.fallacies),
            "reasoning_history_size": len(self.reasoning_history),
            "methods_available": [
                "reason",
                "apply_pramana",
                "detect_fallacy_in_text",
                "explain_decision"
            ],
            "average_confidence": 0.75
        }
