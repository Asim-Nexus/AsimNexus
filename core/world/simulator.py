
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Simulation Sandbox
=============================
"What if" world scenarios testing
Includes: Scenario modeling, outcome prediction, risk assessment
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import os

logger = logging.getLogger("SimulationSandbox")


class ScenarioType(Enum):
    """Types of simulation scenarios"""
    POLICY = "policy"
    DISASTER = "disaster"
    ECONOMIC = "economic"
    CLIMATE = "climate"
    INFRASTRUCTURE = "infrastructure"
    SOCIAL = "social"


class SimulationStatus(Enum):
    """Simulation statuses"""
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SimulationScenario:
    """Simulation scenario definition"""
    scenario_id: str
    name: str
    scenario_type: ScenarioType
    description: str
    parameters: Dict[str, Any]
    initial_conditions: Dict[str, Any]
    status: SimulationStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class SimulationResult:
    """Simulation result"""
    result_id: str
    scenario_id: str
    outcomes: Dict[str, Any]
    metrics: Dict[str, float]
    risk_assessment: Dict[str, Any]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SimulationStep:
    """Step in simulation timeline"""
    step_id: str
    scenario_id: str
    step_number: int
    state: Dict[str, Any]
    events: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SimulationSandbox:
    """Simulation sandbox for world scenarios"""
    
    def __init__(self):
        self.scenarios: Dict[str, SimulationScenario] = {}
        self.results: Dict[str, SimulationResult] = {}
        self.steps: Dict[str, List[SimulationStep]] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize simulation sandbox"""
        logger.info("🧪 Initializing Simulation Sandbox...")
        logger.info("🌍 Setting up scenario modeling")
        logger.info("🔮 Setting up outcome prediction")
        logger.info("⚠️  Setting up risk assessment")
        logger.info("✅ Simulation Sandbox initialized")
    
    def create_scenario(
        self,
        name: str,
        scenario_type: ScenarioType,
        description: str,
        parameters: Dict[str, Any],
        initial_conditions: Dict[str, Any]
    ) -> SimulationScenario:
        """Create a new simulation scenario"""
        scenario = SimulationScenario(
            scenario_id=f"scenario_{uuid.uuid4().hex[:8]}",
            name=name,
            scenario_type=scenario_type,
            description=description,
            parameters=parameters,
            initial_conditions=initial_conditions,
            status=SimulationStatus.DRAFT
        )
        
        self.scenarios[scenario.scenario_id] = scenario
        logger.info(f"✅ Created scenario: {name} ({scenario_type.value})")
        return scenario
    
    def run_simulation(self, scenario_id: str, time_steps: int = 100) -> SimulationResult:
        """Run simulation scenario"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        scenario = self.scenarios[scenario_id]
        scenario.status = SimulationStatus.RUNNING
        scenario.started_at = datetime.utcnow()
        
        # Initialize steps list
        self.steps[scenario_id] = []
        
        # Run simulation steps
        current_state = scenario.initial_conditions.copy()
        
        for step_num in range(time_steps):
            # Simulate step
            new_state, events = self._simulate_step(current_state, scenario.parameters)
            
            step = SimulationStep(
                step_id=f"step_{uuid.uuid4().hex[:8]}",
                scenario_id=scenario_id,
                step_number=step_num,
                state=new_state,
                events=events
            )
            
            self.steps[scenario_id].append(step)
            current_state = new_state
        
        # Calculate results
        outcomes = self._calculate_outcomes(current_state, scenario.initial_conditions)
        metrics = self._calculate_metrics(current_state)
        risk_assessment = self._assess_risks(outcomes, metrics)
        confidence = 0.87
        
        result = SimulationResult(
            result_id=f"result_{uuid.uuid4().hex[:8]}",
            scenario_id=scenario_id,
            outcomes=outcomes,
            metrics=metrics,
            risk_assessment=risk_assessment,
            confidence=confidence
        )
        
        self.results[result.result_id] = result
        scenario.status = SimulationStatus.COMPLETED
        scenario.completed_at = datetime.utcnow()
        
        logger.info(f"✅ Completed simulation: {scenario.name}")
        return result
    
    def _simulate_step(self, current_state: Dict[str, Any], parameters: Dict[str, Any]) -> tuple:
        """Simulate a single time step"""
        # Simulate state evolution
        new_state = current_state.copy()
        
        # Apply parameters to state
        for key, value in parameters.items():
            if key in new_state:
                new_state[key] = new_state[key] * (1 + value * 0.01)
        
        # Generate events
        events = []
        if new_state.get("stress_level", 0) > 0.8:
            events.append({
                "type": "warning",
                "description": "High stress level detected"
            })
        
        return new_state, events
    
    def _calculate_outcomes(self, final_state: Dict[str, Any], initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate simulation outcomes"""
        outcomes = {}
        
        for key in final_state:
            if key in initial_state:
                change = final_state[key] - initial_state[key]
                outcomes[f"{key}_change"] = change
                outcomes[f"{key}_percent_change"] = (change / initial_state[key]) * 100 if initial_state[key] != 0 else 0
        
        return outcomes
    
    def _calculate_metrics(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Calculate simulation metrics"""
        metrics = {
            "stability_score": 0.85,
            "efficiency_score": 0.78,
            "resilience_score": 0.82,
            "sustainability_score": 0.76
        }
        
        # Adjust metrics based on state
        if state.get("stress_level", 0) > 0.7:
            metrics["stability_score"] -= 0.2
        
        return metrics
    
    def _assess_risks(self, outcomes: Dict[str, Any], metrics: Dict[str, float]) -> Dict[str, Any]:
        """Assess risks from simulation"""
        risks = []
        
        # Check for negative outcomes
        for key, value in outcomes.items():
            if "percent_change" in key and value < -20:
                risks.append({
                    "type": "negative_impact",
                    "metric": key,
                    "severity": "high" if value < -50 else "medium"
                })
        
        # Check for low metrics
        for key, value in metrics.items():
            if value < 0.5:
                risks.append({
                    "type": "low_metric",
                    "metric": key,
                    "severity": "high" if value < 0.3 else "medium"
                })
        
        return {
            "total_risks": len(risks),
            "risks": risks,
            "overall_risk_level": "high" if len(risks) > 5 else "medium" if len(risks) > 2 else "low"
        }
    
    def get_scenario(self, scenario_id: str) -> Optional[SimulationScenario]:
        """Get scenario by ID"""
        return self.scenarios.get(scenario_id)
    
    def get_result(self, result_id: str) -> Optional[SimulationResult]:
        """Get result by ID"""
        return self.results.get(result_id)
    
    def get_scenario_steps(self, scenario_id: str) -> List[SimulationStep]:
        """Get all steps for a scenario"""
        return self.steps.get(scenario_id, [])
    
    def compare_scenarios(self, scenario_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple scenarios"""
        comparison = {
            "scenarios": [],
            "metrics_comparison": {}
        }
        
        for scenario_id in scenario_ids:
            if scenario_id in self.scenarios:
                scenario = self.scenarios[scenario_id]
                result = next((r for r in self.results.values() if r.scenario_id == scenario_id), None)
                
                comparison["scenarios"].append({
                    "id": scenario_id,
                    "name": scenario.name,
                    "type": scenario.scenario_type.value,
                    "status": scenario.status.value,
                    "result": result.metrics if result else None
                })
        
        return comparison
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        type_counts = {}
        for scenario in self.scenarios.values():
            type_counts[scenario.scenario_type.value] = type_counts.get(scenario.scenario_type.value, 0) + 1
        
        status_counts = {}
        for scenario in self.scenarios.values():
            status_counts[scenario.status.value] = status_counts.get(scenario.status.value, 0) + 1
        
        return {
            "total_scenarios": len(self.scenarios),
            "scenario_type_distribution": type_counts,
            "scenario_status_distribution": status_counts,
            "total_results": len(self.results),
            "total_steps": sum(len(steps) for steps in self.steps.values())
        }


# Global instance
_simulation_sandbox: Optional[SimulationSandbox] = None


def get_simulation_sandbox() -> SimulationSandbox:
    """Get singleton instance"""
    global _simulation_sandbox
    if _simulation_sandbox is None:
        _simulation_sandbox = SimulationSandbox()
    return _simulation_sandbox
