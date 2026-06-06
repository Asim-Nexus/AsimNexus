
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Cultural Sovereignty System
======================================
Country-specific cultural values enforcement
Respects local laws, customs, and ethical frameworks
Each country defines its own rules, enforced by the system
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ASIM_CULTURAL_SOVEREIGNTY")

class RulePriority(Enum):
    """Priority levels for cultural rules"""
    MANDATORY = "mandatory"  # Must follow, blocks action
    RECOMMENDED = "recommended"  # Warning, but allowed
    ADVISORY = "advisory"  # Information only

class RuleCategory(Enum):
    """Categories of cultural rules"""
    FINANCIAL = "financial"  # Banking, transactions, interest
    PRIVACY = "privacy"  # Data protection, surveillance
    CONTENT = "content"  # Speech, media, expression
    BUSINESS = "business"  # Commerce, trade, contracts
    SOCIAL = "social"  # Family, marriage, inheritance
    TECHNICAL = "technical"  # Encryption, protocols

@dataclass
class CulturalRule:
    """A cultural rule defined by a country"""
    rule_id: str
    country_code: str
    name: str
    description: str
    category: RuleCategory
    priority: RulePriority
    
    # Rule logic
    condition: Dict[str, Any]  # When this rule applies
    action: str  # What to do: 'block', 'warn', 'log', 'require_approval'
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    active: bool

class CountryCulturalProfile:
    """Cultural profile for a country"""
    
    def __init__(self, country_code: str, country_name: str):
        self.country_code = country_code
        self.country_name = country_name
        self.rules: List[CulturalRule] = []
        self.active = True
        
        # Country-specific settings
        self.preferences = {
            'default_data_residency': country_code.lower(),
            'allow_foreign_encryption': True,
            'require_local_backups': False,
            'business_hours': {'start': 9, 'end': 17, 'timezone': 'UTC'}
        }
        
        logger.info(f"🌍 Cultural profile created: {country_name} ({country_code})")
    
    def add_rule(self, rule: CulturalRule) -> bool:
        """Add a cultural rule"""
        if rule.country_code != self.country_code:
            return False
        
        self.rules.append(rule)
        logger.info(f"📜 Rule added: {rule.name} ({self.country_code})")
        return True
    
    def check_action(self, action: str, params: Dict) -> Dict:
        """Check if action complies with cultural rules"""
        violations = []
        warnings = []
        required_approvals = []
        
        for rule in self.rules:
            if not rule.active:
                continue
            
            # Check if rule applies to this action
            if self._rule_applies(rule, action, params):
                result = {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'category': rule.category.value,
                    'priority': rule.priority.value,
                    'action': rule.action
                }
                
                if rule.priority == RulePriority.MANDATORY:
                    violations.append(result)
                elif rule.priority == RulePriority.RECOMMENDED:
                    warnings.append(result)
                
                if rule.action == 'require_approval':
                    required_approvals.append(result)
        
        # Determine overall compliance
        if violations:
            compliant = False
            status = 'blocked'
        elif required_approvals:
            compliant = True
            status = 'requires_approval'
        elif warnings:
            compliant = True
            status = 'warning'
        else:
            compliant = True
            status = 'compliant'
        
        return {
            'country_code': self.country_code,
            'compliant': compliant,
            'status': status,
            'violations': violations,
            'warnings': warnings,
            'required_approvals': required_approvals
        }
    
    def _rule_applies(self, rule: CulturalRule, action: str, params: Dict) -> bool:
        """Check if rule applies to this action"""
        condition = rule.condition
        
        # Check action type
        if 'action_type' in condition:
            if condition['action_type'] != action:
                return False
        
        # Check action contains
        if 'action_contains' in condition:
            if condition['action_contains'] not in action:
                return False
        
        # Check value threshold
        if 'min_value' in condition:
            if params.get('value', 0) < condition['min_value']:
                return False
        
        if 'max_value' in condition:
            if params.get('value', 0) > condition['max_value']:
                return False
        
        # Check entity type
        if 'entity_type' in condition:
            if params.get('entity_type') != condition['entity_type']:
                return False
        
        # Check custom condition
        if 'custom_check' in condition:
            # Custom checks would be implemented here
            pass
        
        return True

class CulturalSovereigntyEngine:
    """
    Cultural Sovereignty Enforcement Engine
    
    Manages country-specific rules and enforces them
    across all actions in the system
    """
    
    def __init__(self):
        self.countries: Dict[str, CountryCulturalProfile] = {}
        self._init_default_profiles()
        
        logger.info("🌍 Cultural Sovereignty Engine initialized")
    
    def _init_default_profiles(self):
        """Initialize default country profiles with sample rules"""
        
        # Nepal Profile
        nepal = CountryCulturalProfile('NP', 'Nepal')
        nepal.add_rule(CulturalRule(
            rule_id='np_no_interest_microfinance',
            country_code='NP',
            name='No Interest on Small Loans',
            description='Interest-free microfinance loans up to NPR 50,000',
            category=RuleCategory.FINANCIAL,
            priority=RulePriority.MANDATORY,
            condition={'action_type': 'microfinance_loan', 'max_value': 50000},
            action='block_if_interest',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        nepal.add_rule(CulturalRule(
            rule_id='np_digital_property_rights',
            country_code='NP',
            name='Digital Property Rights',
            description='Respect for digital property as per Nepal Digital Dharma',
            category=RuleCategory.BUSINESS,
            priority=RulePriority.MANDATORY,
            condition={'action_contains': 'property_transfer'},
            action='require_approval',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        nepal.preferences['business_hours']['timezone'] = 'Asia/Kathmandu'
        self.countries['NP'] = nepal
        
        # India Profile
        india = CountryCulturalProfile('IN', 'India')
        india.add_rule(CulturalRule(
            rule_id='in_data_localization',
            country_code='IN',
            name='Data Localization',
            description='Sensitive data must remain within Indian borders',
            category=RuleCategory.PRIVACY,
            priority=RulePriority.MANDATORY,
            condition={'action_contains': 'data_transfer'},
            action='require_local_storage',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        india.add_rule(CulturalRule(
            rule_id='in_dpi_compliance',
            country_code='IN',
            name='Digital Public Infrastructure',
            description='Respect for India Stack (UPI, Aadhaar, etc.)',
            category=RuleCategory.TECHNICAL,
            priority=RulePriority.RECOMMENDED,
            condition={'action_contains': 'digital_identity'},
            action='warn_if_not_compliant',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        india.preferences['business_hours']['timezone'] = 'Asia/Kolkata'
        self.countries['IN'] = india
        
        # USA Profile
        usa = CountryCulturalProfile('US', 'United States')
        usa.add_rule(CulturalRule(
            rule_id='us_encryption_export',
            country_code='US',
            name='Encryption Export Control',
            description='Strong encryption may require export approval',
            category=RuleCategory.TECHNICAL,
            priority=RulePriority.RECOMMENDED,
            condition={'action_contains': 'export_encryption'},
            action='require_approval',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        usa.add_rule(CulturalRule(
            rule_id='us_state_privacy_laws',
            country_code='US',
            name='State Privacy Laws',
            description='Comply with CCPA, BIPA, and other state laws',
            category=RuleCategory.PRIVACY,
            priority=RulePriority.MANDATORY,
            condition={'action_contains': 'data_collection'},
            action='log_and_warn',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        self.countries['US'] = usa
        
        # EU Profile
        eu = CountryCulturalProfile('EU', 'European Union')
        eu.add_rule(CulturalRule(
            rule_id='eu_gdpr_compliance',
            country_code='EU',
            name='GDPR Compliance',
            description='General Data Protection Regulation compliance',
            category=RuleCategory.PRIVACY,
            priority=RulePriority.MANDATORY,
            condition={'action_contains': 'personal_data'},
            action='require_consent',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        eu.add_rule(CulturalRule(
            rule_id='eu_digital_markets',
            country_code='EU',
            name='Digital Markets Act',
            description='Fair competition in digital markets',
            category=RuleCategory.BUSINESS,
            priority=RulePriority.MANDATORY,
            condition={'action_contains': 'platform_access'},
            action='ensure_fair_access',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            active=True
        ))
        self.countries['EU'] = eu
        
        logger.info(f"  ✅ Initialized {len(self.countries)} country profiles")
    
    def check_action(self, country_code: str, action: str, params: Dict) -> Dict:
        """Check action against country's cultural rules"""
        if country_code not in self.countries:
            # No specific rules for this country
            return {
                'country_code': country_code,
                'compliant': True,
                'status': 'no_rules_defined',
                'violations': [],
                'warnings': [],
                'required_approvals': []
            }
        
        country = self.countries[country_code]
        result = country.check_action(action, params)
        
        logger.debug(f"🌍 Cultural check: {country_code} - {result['status']}")
        return result
    
    def add_country_rule(self, country_code: str, rule: CulturalRule) -> bool:
        """Add a rule to a country's profile"""
        if country_code not in self.countries:
            # Create new profile
            self.countries[country_code] = CountryCulturalProfile(
                country_code,
                f"Country_{country_code}"
            )
        
        return self.countries[country_code].add_rule(rule)
    
    def get_country_profile(self, country_code: str) -> Optional[Dict]:
        """Get country's cultural profile"""
        if country_code not in self.countries:
            return None
        
        profile = self.countries[country_code]
        return {
            'country_code': profile.country_code,
            'country_name': profile.country_name,
            'active': profile.active,
            'rule_count': len(profile.rules),
            'rules': [
                {
                    'rule_id': r.rule_id,
                    'name': r.name,
                    'category': r.category.value,
                    'priority': r.priority.value,
                    'active': r.active
                }
                for r in profile.rules
            ],
            'preferences': profile.preferences
        }
    
    def list_countries(self) -> List[Dict]:
        """List all countries with cultural rules"""
        return [
            {
                'country_code': c.country_code,
                'country_name': c.country_name,
                'active': c.active,
                'rule_count': len(c.rules)
            }
            for c in self.countries.values()
        ]
    
    def get_global_compliance_report(self) -> Dict:
        """Get global compliance statistics"""
        total_countries = len(self.countries)
        total_rules = sum(len(c.rules) for c in self.countries.values())
        active_countries = sum(1 for c in self.countries.values() if c.active)
        
        rules_by_category = {}
        for country in self.countries.values():
            for rule in country.rules:
                cat = rule.category.value
                rules_by_category[cat] = rules_by_category.get(cat, 0) + 1
        
        return {
            'total_countries': total_countries,
            'active_countries': active_countries,
            'total_rules': total_rules,
            'rules_by_category': rules_by_category,
            'timestamp': datetime.now().isoformat()
        }

_sovereignty_engine = None

def get_cultural_sovereignty_engine() -> CulturalSovereigntyEngine:
    """Get cultural sovereignty engine singleton"""
    global _sovereignty_engine
    if _sovereignty_engine is None:
        _sovereignty_engine = CulturalSovereigntyEngine()
    return _sovereignty_engine

if __name__ == "__main__":
    import sys
    
    engine = get_cultural_sovereignty_engine()
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Test action checking
        country = sys.argv[2] if len(sys.argv) > 2 else 'NP'
        action = sys.argv[3] if len(sys.argv) > 3 else 'microfinance_loan'
        
        result = engine.check_action(country, action, {'value': 30000})
        print(json.dumps(result, indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "profile":
        country = sys.argv[2] if len(sys.argv) > 2 else 'NP'
        profile = engine.get_country_profile(country)
        if profile:
            print(json.dumps(profile, indent=2))
        else:
            print(f"No profile found for {country}")
            
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        countries = engine.list_countries()
        print(json.dumps(countries, indent=2))
        
    elif len(sys.argv) > 1 and sys.argv[1] == "report":
        report = engine.get_global_compliance_report()
        print(json.dumps(report, indent=2))
        
    else:
        print("Usage: python cultural_sovereignty.py [check|profile|list|report]")
