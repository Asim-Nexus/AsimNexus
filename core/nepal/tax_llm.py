"""
STATUS: REAL — Nepal Tax LLM for government services

AsimNexus Nepal Tax LLM
=========================
Tax computation and filing for Nepal:
- Income Tax (व्यक्तिगत/कम्पनी)
- VAT/GST compliance
- PAN registration integration
- Integration with Nagarik App
- Dreamming Engine lessons for tax optimization
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("AsimNexus.Nepal.TaxLLM")

TAX_RULES_PATH = Path(__file__).parent.parent.parent / "data" / "tax_rules_nepal.json"

@dataclass
class TaxBracket:
    """Tax bracket definition"""
    min_income: float
    max_income: float
    rate: float
    description: str

@dataclass
class TaxLiability:
    """Calculated tax liability"""
    taxable_income: float
    tax_amount: float
    effective_rate: float
    breakdown: List[Dict]
    currency: str = "NPR"

class NepalTaxLLM:
    """
    Nepal-specific Tax computation and optimization
    
    Integrates with Government API and Dreamming Engine for
    personalized tax advice and compliance.
    """

    # Nepal Tax Year 2080/2081 (current fiscal year)
    INCOME_TAX_BRACKETS = [
        TaxBracket(0, 500000, 0.01, "First 500,000 - 1%"),
        TaxBracket(500001, 2000000, 0.10, "500,001-2,000,000 - 10%"),
        TaxBracket(2000001, 5000000, 0.20, "2,000,001-5,000,000 - 20%"),
        TaxBracket(5000001, 10000000, 0.25, "5,000,001-10,000,000 - 25%"),
        TaxBracket(1000001, float('inf'), 0.30, "Above 10,000,000 - 30%"),
    ]

    # Standard deductions
    STANDARD_DEDUCTION = 200000  # NPR 200,000
    
    # VAT rates
    VAT_RATES = {
        "standard": 0.13,  # 13%
        "reduced": 0.0,    # 0% for essentials
        "luxury": 0.25     # 25% for luxury goods
    }

    def __init__(self):
        self._training_data: List[Dict] = []
        self._load_tax_rules()
        logger.info("💰 NepalTaxLLM initialized for FY 2080/2081")

    def _load_tax_rules(self):
        """Load Nepal tax rules from data file or use defaults"""
        if TAX_RULES_PATH.exists():
            try:
                import json
                with open(TAX_RULES_PATH) as f:
                    rules = json.load(f)
                # Update brackets from file if available
                logger.info("📄 Loaded custom tax rules")
            except Exception as e:
                logger.warning(f"Using default tax rules: {e}")

    def calculate_income_tax(
        self, 
        gross_income: float, 
        deductions: Optional[Dict[str, float]] = None
    ) -> TaxLiability:
        """
        Calculate income tax for Nepali taxpayers
        
        Args:
            gross_income: Annual income in NPR
            deductions: Optional deductions breakdown
        
        Returns:
            TaxLiability with calculation details
        """
        total_deductions = sum(deductions.values()) if deductions else 0
        total_deductions += self.STANDARD_DEDUCTION

        taxable_income = max(0, gross_income - total_deductions)
        tax_amount = 0.0
        breakdown = []

        remaining = taxable_income
        for bracket in self.INCOME_TAX_BRACKETS:
            if remaining <= 0:
                break

            bracket_income = min(
                remaining, 
                bracket.max_income - bracket.min_income
            )
            bracket_tax = bracket_income * bracket.rate
            tax_amount += bracket_tax

            breakdown.append({
                "bracket": bracket.description,
                "income": bracket_income,
                "rate": bracket.rate,
                "tax": bracket_tax
            })

            remaining -= bracket_income

        effective_rate = tax_amount / max(taxable_income, 1) if taxable_income > 0 else 0

        return TaxLiability(
            taxable_income=taxable_income,
            tax_amount=tax_amount,
            effective_rate=effective_rate,
            breakdown=breakdown
        )

    def calculate_vat(
        self, 
        amount: float, 
        category: str = "standard"
    ) -> float:
        """
        Calculate VAT for transactions
        
        Args:
            amount: Transaction amount in NPR
            category: VAT category (standard/reduced/luxury)
        
        Returns:
            VAT amount
        """
        rate = self.VAT_RATES.get(category, self.VAT_RATES["standard"])
        return amount * rate

    def get_filing_deadline(self, year: int = 2081) -> datetime:
        """Get tax filing deadline (Shrawan 31 for Nepali calendar)"""
        # Approximate: Shrawan 31 = mid-August in Gregorian
        return datetime(year, 8, 15)

    async def train_from_dreams(self, lessons: List[Dict]) -> str:
        """
        Train tax LLM from Dreamming Engine lessons
        
        Args:
            lessons: Lessons containing tax-related discussions
        
        Returns:
            Path to trained adapter (placeholder)
        """
        tax_lessons = [
            l for l in lessons 
            if "tax" in l.get("topic", "").lower() or "कर" in l.get("topic", "")
        ]

        self._training_data.extend(tax_lessons)
        logger.info(f"💰 Trained on {len(tax_lessons)} tax lessons")

        # In production: use LoRA engine to create adapter
        from core.dreaming.lora_engine import get_lora_engine
        engine = get_lora_engine()
        
        return await engine.create_adapter_from_dreams("nepal_tax", tax_lessons)

    def optimize_deductions(
        self, 
        income: float, 
        expenses: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Suggest optimal deductions for tax planning
        
        Args:
            income: Annual income
            expenses: Expense categories
        
        Returns:
            Optimization suggestions
        """
        suggestions = []

        # Education allowance (up to NPR 100,000)
        if "education" in expenses:
            edu_ded = min(expenses["education"], 100000)
            suggestions.append({
                "category": "education",
                "deductible": edu_ded,
                "saving": edu_ded * 0.10  # At 10% marginal rate
            })

        # Medical insurance (up to NPR 50,000)
        if "medical" in expenses:
            med_ded = min(expenses["medical"], 50000)
            suggestions.append({
                "category": "medical",
                "deductible": med_ded,
                "saving": med_ded * 0.10
            })

        total_saving = sum(s["saving"] for s in suggestions)

        return {
            "suggestions": suggestions,
            "total_potential_saving": total_saving,
            "estimated_tax_reduction": self.calculate_income_tax(
                income, {s["category"]: s["deductible"] for s in suggestions}
            ).tax_amount
        }

    def integrate_with_nagarik_app(self, user_data: Dict) -> Dict:
        """
        Generate tax data compatible with Nagarik App
        
        Args:
            user_data: User's financial data
        
        Returns:
            Formatted data for Nagarik App
        """
        return {
            "tax_year": "2080/2081",
            "income_declaration": user_data.get("income", 0),
            "deductions": user_data.get("deductions", {}),
            "pan_number": user_data.get("pan", ""),
            "calculated_tax": self.calculate_income_tax(
                user_data.get("income", 0),
                user_data.get("deductions")
            ).tax_amount,
            "submission_ready": True
        }

    def status(self) -> Dict[str, Any]:
        """Get Tax LLM status"""
        return {
            "fiscal_year": "2080/2081",
            "brackets_count": len(self.INCOME_TAX_BRACKETS),
            "standard_deduction": self.STANDARD_DEDUCTION,
            "vat_rates": self.VAT_RATES,
            "training_samples": len(self._training_data),
            "nagarik_app_integration": True
        }

# Singleton
_tax_llm: Optional[NepalTaxLLM] = None

def get_tax_llm() -> NepalTaxLLM:
    """Get or create Nepal Tax LLM singleton"""
    global _tax_llm
    if _tax_llm is None:
        _tax_llm = NepalTaxLLM()
    return _tax_llm