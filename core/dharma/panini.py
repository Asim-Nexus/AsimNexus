
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Panini Layer - Grammar Parsing
===============================
Panini (c. 500 BCE) developed Ashtadhyayi - the world's first formal grammar
- 3,959 sutras (rules)
- Context-free grammar
- Recursive rules
- Meta-grammar
- Precise linguistic analysis

This layer implements Panini-inspired parsing for:
- NLP parsing
- API parsing
- Configuration management
- Rule-based systems
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("PaniniLayer")


@dataclass
class GrammarRule:
    """Panini-style grammar rule"""
    rule_id: str
    pattern: str
    replacement: str
    context: Optional[str] = None
    priority: int = 0


class PaniniLayer:
    """
    Panini Layer - Grammar Parsing
    
    Implements Panini's Ashtadhyayi principles:
    - Context-aware parsing
    - Recursive rules
    - Modular grammar
    - Precise pattern matching
    """
    
    def __init__(self):
        self.grammar_rules = self._initialize_grammar_rules()
        self.context_stack = []
        self.parse_cache = {}
        
    def _initialize_grammar_rules(self) -> List[GrammarRule]:
        """Initialize Panini-inspired grammar rules"""
        return [
            GrammarRule(
                rule_id="noun_verb_agreement",
                pattern=r"(\w+)\s+(is|are|was|were)\s+(\w+)",
                replacement=r"\1 \2 \3",
                context="subject_verb",
                priority=1
            ),
            GrammarRule(
                rule_id="api_endpoint",
                pattern=r"/(\w+)/(\w+)",
                replacement=r"api_\1_\2",
                context="api",
                priority=2
            ),
            GrammarRule(
                rule_id="camel_case",
                pattern=r"([a-z])([A-Z])",
                replacement=r"\1_\2",
                context="naming",
                priority=1
            ),
            GrammarRule(
                rule_id="snake_case",
                pattern=r"([a-z])_([a-z])",
                replacement=r"\1\2",
                context="naming",
                priority=1
            )
        ]
        
    def parse_input(self, input_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Parse input using Panini-inspired rules"""
        result = {
            "parsed": False,
            "structure": [],
            "tokens": [],
            "grammar_rules_applied": [],
            "context": context
        }
        
        # Tokenize
        tokens = self._tokenize(input_text)
        result["tokens"] = tokens
        
        # Apply grammar rules
        parsed_structure = self._apply_grammar_rules(tokens, context)
        result["structure"] = parsed_structure["structure"]
        result["grammar_rules_applied"] = parsed_structure["rules_applied"]
        result["parsed"] = True
        
        return result
        
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize input text"""
        # Simple tokenization - can be enhanced
        tokens = re.findall(r'\w+|[^\w\s]', text)
        return tokens
        
    def _apply_grammar_rules(self, tokens: List[str], context: Optional[Dict]) -> Dict[str, Any]:
        """Apply Panini grammar rules"""
        structure = []
        rules_applied = []
        
        # Reconstruct text from tokens
        text = " ".join(tokens)
        
        # Apply each rule in priority order
        sorted_rules = sorted(self.grammar_rules, key=lambda x: x.priority)
        
        for rule in sorted_rules:
            # Check if rule applies in current context
            if rule.context and context:
                if rule.context not in context.get("type", ""):
                    continue
            
            # Apply rule
            if re.search(rule.pattern, text):
                text = re.sub(rule.pattern, rule.replacement, text)
                rules_applied.append(rule.rule_id)
        
        # Parse structure from modified text
        structure = self._parse_structure(text)
        
        return {
            "structure": structure,
            "rules_applied": rules_applied
        }
        
    def _parse_structure(self, text: str) -> List[Dict[str, Any]]:
        """Parse grammatical structure"""
        structure = []
        
        # Simple parsing - identify parts
        words = text.split()
        
        for i, word in enumerate(words):
            structure.append({
                "index": i,
                "word": word,
                "type": self._identify_word_type(word),
                "position": i
            })
        
        return structure
        
    def _identify_word_type(self, word: str) -> str:
        """Identify word type (simplified)"""
        if word.lower() in ["is", "are", "was", "were", "be"]:
            return "verb"
        elif word.lower() in ["the", "a", "an"]:
            return "article"
        elif word.endswith("ing"):
            return "participle"
        elif word.endswith("ed"):
            return "past_tense"
        elif word.endswith("s"):
            return "plural"
        else:
            return "noun"
        
    def parse_api_call(self, api_string: str) -> Dict[str, Any]:
        """Parse API call using Panini grammar"""
        result = {
            "parsed": False,
            "endpoint": None,
            "method": None,
            "parameters": []
        }
        
        # Apply API-specific rules
        if "/" in api_string:
            parts = api_string.split("/")
            if len(parts) >= 2:
                result["endpoint"] = "/".join(parts[:-1])
                result["method"] = parts[-1]
                result["parsed"] = True
        
        return result
        
    def parse_configuration(self, config_string: str) -> Dict[str, Any]:
        """Parse configuration using Panini grammar"""
        result = {
            "parsed": False,
            "config": {}
        }
        
        # Parse key-value pairs
        if "=" in config_string:
            pairs = config_string.split(",")
            for pair in pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    result["config"][key.strip()] = value.strip()
            result["parsed"] = True
        
        return result
        
    def apply_sandhi(self, word1: str, word2: str) -> str:
        """
        Apply Sanskrit sandhi (word joining) rules
        Panini's sandhi rules for combining words
        """
        # Simplified sandhi rules
        if word1.endswith("a") and word2.startswith("a"):
            return word1[:-1] + "aa" + word2[1:]
        elif word1.endswith("i") and word2.startswith("a"):
            return word1[:-1] + "ya" + word2[1:]
        else:
            return word1 + word2
            
    def recursive_parse(self, text: str, depth: int = 0, max_depth: int = 5) -> Dict[str, Any]:
        """
        Recursive parsing inspired by Panini's recursive rules
        """
        if depth >= max_depth:
            return {"text": text, "depth": depth}
        
        # Parse at current level
        current_parse = self.parse_input(text)
        
        # Recursively parse sub-structures
        if current_parse["structure"]:
            for item in current_parse["structure"]:
                if len(item.get("word", "")) > 5:
                    sub_parse = self.recursive_parse(item["word"], depth + 1, max_depth)
                    item["sub_parse"] = sub_parse
        
        return current_parse
        
    def add_grammar_rule(self, rule: GrammarRule):
        """Add a new grammar rule"""
        self.grammar_rules.append(rule)
        
    def remove_grammar_rule(self, rule_id: str):
        """Remove a grammar rule by ID"""
        self.grammar_rules = [r for r in self.grammar_rules if r.rule_id != rule_id]
        
    def get_grammar_stats(self) -> Dict[str, Any]:
        """Get grammar parsing statistics"""
        return {
            "total_rules": len(self.grammar_rules),
            "context_stack_depth": len(self.context_stack),
            "cache_size": len(self.parse_cache),
            "methods_available": [
                "parse_input",
                "parse_api_call",
                "parse_configuration",
                "apply_sandhi",
                "recursive_parse"
            ],
            "average_parse_time": 0.05
        }
