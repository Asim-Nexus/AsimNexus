
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Execution Timeout & Circuit Breaker
============================================
Prevents infinite execution and provides graceful fallback
Implements circuit breaker pattern for fault tolerance
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json

logger = logging.getLogger("ASIM_EXECUTION_TIMEOUT")

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, stop requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class ExecutionResult:
    """Execution result with timeout info"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    timeout_occurred: bool = False
    execution_time_ms: float = 0
    circuit_state: CircuitState = CircuitState.CLOSED

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds to wait before trying again
    expected_exception: type = Exception
    success_threshold: int = 2          # Successes before closing

class CircuitBreaker:
    """
    Circuit Breaker implementation
    Prevents cascading failures
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
    def call_allowed(self) -> bool:
        """Check if call is allowed based on circuit state"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                if time_since_failure >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
            return False
        
        # HALF_OPEN state - allow some calls to test recovery
        return True
    
    def record_success(self):
        """Record successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("🔌 Circuit breaker CLOSED - Service recovered")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("🔌 Circuit breaker OPEN - Service still failing")
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"🔌 Circuit breaker OPEN - {self.failure_count} failures detected")
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }

class ExecutionTimeout:
    """
    Execution timeout manager with circuit breaker
    Provides graceful fallback and fault tolerance
    """
    
    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._active_executions: Dict[str, Dict] = {}
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize execution timeout system"""
        try:
            self._initialized = True
            logger.info("✅ Execution Timeout system initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Execution Timeout initialization failed: {e}")
            return False
    
    async def execute_with_timeout(
        self,
        func: Callable,
        timeout: Optional[int] = None,
        circuit_name: Optional[str] = None,
        fallback_func: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute function with timeout and circuit breaker protection
        
        Args:
            func: Function to execute
            timeout: Timeout in seconds (uses default if None)
            circuit_name: Circuit breaker name (uses func name if None)
            fallback_func: Fallback function if execution fails
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        if not self._initialized:
            await self.initialize()
        
        execution_id = str(uuid.uuid4())
        timeout = timeout or self.default_timeout
        circuit_name = circuit_name or func.__name__
        
        # Get or create circuit breaker
        circuit_breaker = self._get_circuit_breaker(circuit_name)
        
        # Check if call is allowed
        if not circuit_breaker.call_allowed():
            logger.warning(f"🚫 Circuit breaker OPEN for {circuit_name}")
            
            if fallback_func:
                try:
                    fallback_result = await fallback_func(*args, **kwargs)
                    return ExecutionResult(
                        success=True,
                        result=fallback_result,
                        timeout_occurred=False,
                        circuit_state=CircuitState.OPEN,
                        execution_time_ms=0
                    )
                except Exception as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Circuit breaker OPEN and fallback failed: {str(e)}",
                        timeout_occurred=False,
                        circuit_state=CircuitState.OPEN,
                        execution_time_ms=0
                    )
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Circuit breaker OPEN for {circuit_name}",
                    timeout_occurred=False,
                    circuit_state=CircuitState.OPEN,
                    execution_time_ms=0
                )
        
        # Record execution start
        start_time = time.time()
        self._active_executions[execution_id] = {
            "func": func.__name__,
            "start_time": start_time,
            "circuit_name": circuit_name
        }
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Record success
            circuit_breaker.record_success()
            
            logger.debug(f"✅ Execution completed: {func.__name__} in {execution_time_ms:.2f}ms")
            
            return ExecutionResult(
                success=True,
                result=result,
                timeout_occurred=False,
                circuit_state=circuit_breaker.state,
                execution_time_ms=execution_time_ms
            )
            
        except asyncio.TimeoutError:
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Record failure
            circuit_breaker.record_failure()
            
            logger.warning(f"⏰ Execution timeout: {func.__name__} after {execution_time_ms:.2f}ms")
            
            # Try fallback
            if fallback_func:
                try:
                    fallback_result = await fallback_func(*args, **kwargs)
                    return ExecutionResult(
                        success=True,
                        result=fallback_result,
                        timeout_occurred=True,
                        circuit_state=circuit_breaker.state,
                        execution_time_ms=execution_time_ms
                    )
                except Exception as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Timeout and fallback failed: {str(e)}",
                        timeout_occurred=True,
                        circuit_state=circuit_breaker.state,
                        execution_time_ms=execution_time_ms
                    )
            else:
                return ExecutionResult(
                    success=False,
                    error=f"Execution timeout after {timeout} seconds",
                    timeout_occurred=True,
                    circuit_state=circuit_breaker.state,
                    execution_time_ms=execution_time_ms
                )
                
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Record failure
            circuit_breaker.record_failure()
            
            # Adaptive Resource Feedback: Notify state manager
            try:
                from core.state_manager import get_state_manager, AgentState
                state_manager = get_state_manager()
                # Update system state to reflect failure
                await state_manager.cleanup_expired_sessions()
                logger.info(f"🔄 Adaptive feedback: Updated state manager after failure in {func.__name__}")
            except Exception as feedback_error:
                logger.warning(f"Failed to send adaptive feedback: {feedback_error}")
            
            logger.error(f"❌ Execution failed: {func.__name__} - {str(e)}")
            
            # Try fallback
            if fallback_func:
                try:
                    fallback_result = await fallback_func(*args, **kwargs)
                    return ExecutionResult(
                        success=True,
                        result=fallback_result,
                        timeout_occurred=False,
                        circuit_state=circuit_breaker.state,
                        execution_time_ms=execution_time_ms
                    )
                except Exception as fallback_error:
                    return ExecutionResult(
                        success=False,
                        error=f"Original error: {str(e)}, Fallback error: {str(fallback_error)}",
                        timeout_occurred=False,
                        circuit_state=circuit_breaker.state,
                        execution_time_ms=execution_time_ms
                    )
            else:
                return ExecutionResult(
                    success=False,
                    error=str(e),
                    timeout_occurred=False,
                    circuit_state=circuit_breaker.state,
                    execution_time_ms=execution_time_ms
                )
                
        finally:
            # Clean up execution record
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
    
    def _get_circuit_breaker(self, circuit_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for circuit name"""
        if circuit_name not in self._circuit_breakers:
            config = CircuitBreakerConfig()
            self._circuit_breakers[circuit_name] = CircuitBreaker(config)
        
        return self._circuit_breakers[circuit_name]
    
    def get_circuit_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all circuit breaker states"""
        return {name: cb.get_state() for name, cb in self._circuit_breakers.items()}
    
    def get_active_executions(self) -> Dict[str, Dict]:
        """Get currently active executions"""
        current_time = time.time()
        active_executions = {}
        
        for exec_id, execution in self._active_executions.items():
            runtime = current_time - execution["start_time"]
            active_executions[exec_id] = {
                **execution,
                "runtime_seconds": runtime
            }
        
        return active_executions
    
    def reset_circuit_breaker(self, circuit_name: str) -> bool:
        """Reset a circuit breaker to closed state"""
        if circuit_name in self._circuit_breakers:
            circuit_breaker = self._circuit_breakers[circuit_name]
            circuit_breaker.state = CircuitState.CLOSED
            circuit_breaker.failure_count = 0
            circuit_breaker.success_count = 0
            circuit_breaker.last_failure_time = None
            logger.info(f"🔄 Circuit breaker reset: {circuit_name}")
            return True
        return False
    
    def configure_circuit_breaker(self, circuit_name: str, config: CircuitBreakerConfig):
        """Configure circuit breaker for specific circuit"""
        self._circuit_breakers[circuit_name] = CircuitBreaker(config)
        logger.info(f"⚙️ Circuit breaker configured: {circuit_name}")

# Global instance
_execution_timeout = None

def get_execution_timeout(default_timeout: int = 30) -> ExecutionTimeout:
    """Get global execution timeout instance"""
    global _execution_timeout
    if _execution_timeout is None:
        _execution_timeout = ExecutionTimeout(default_timeout)
    return _execution_timeout

# Decorator for automatic timeout and circuit breaker protection
def with_timeout(timeout: int = 30, circuit_name: str = None, fallback_func: Callable = None):
    """Decorator to automatically add timeout and circuit breaker protection"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            timeout_manager = get_execution_timeout()
            
            result = await timeout_manager.execute_with_timeout(
                func=func,
                timeout=timeout,
                circuit_name=circuit_name,
                fallback_func=fallback_func,
                *args,
                **kwargs
            )
            
            if result.success:
                return result.result
            else:
                raise Exception(f"Execution failed: {result.error}")
        
        return wrapper
    return decorator

# Graceful fallback functions
async def default_fallback_response(*args, **kwargs) -> str:
    """Default fallback response"""
    return "I'm sorry, the operation is currently unavailable. Please try again later."

async def file_operation_fallback(*args, **kwargs) -> str:
    """Fallback for file operations"""
    return "File operations are temporarily unavailable. Please check file permissions and try again."

async def api_call_fallback(*args, **kwargs) -> str:
    """Fallback for API calls"""
    return "External services are temporarily unavailable. Please try again later."

async def llm_fallback(*args, **kwargs) -> str:
    """Fallback for LLM calls"""
    return "AI processing is temporarily unavailable. Please try again later."
