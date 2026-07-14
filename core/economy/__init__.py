
"""
STATUS: REAL — Phase 3B: All economy modules upgraded to full persistence + API
"""

"""
ASIMNEXUS Economy Module
=========================
Central wiring point for all economy subsystems:
- NexusCredits (user payment system)
- ContractExecutor (contract lifecycle with FSM)
- MarketplaceEngine (digital goods marketplace)
- SovereignTokenEngine (SVT micro-token economy)
- HybridEconomy (human-agent hybrid economy)
- ReputationSystem (reputation with staking)
- JobMarketplace (SQLite-backed job board)
- DecentralizedTaskBus (distributed task execution)
- TokenBridge (cross-chain bridge)
- LedgerEngine (double-entry accounting ledger)
"""

from .job_marketplace import marketplace, JobMarketplace, JobStatus, PaymentStatus, JobCategory
from .contract_executor import (
    ContractExecutor,
    ContractStatus,
    ContractDuration,
    ContractType,
    AuditEntry,
    get_contract_executor,
    reset_contract_executor,
)
from .reputation_system import (
    ReputationSystem,
    ReputationLevel,
    ReputationScore,
    StakeRecord,
    ReputationEvent,
    get_reputation_system,
    reset_reputation_system,
)
from .hybrid_economy import (
    HybridEconomy,
    EconomyMode,
    EconomyAccount,
    Task,
    TaskStatus,
    get_hybrid_economy,
    reset_hybrid_economy,
)
from .sovereign_token import (
    SovereignTokenEngine,
    SVTTransaction,
    SVTWallet,
    TxType,
    get_svt_engine,
    reset_svt_engine,
)
from .marketplace_engine import (
    MarketplaceEngine,
    MarketplaceListing,
    MarketplaceOrder,
    ShoppingCart,
    ShoppingCartItem,
    Review,
    ListingStatus,
    ListingCategory,
    OrderStatus,
    PaymentMethod,
    get_marketplace,
    reset_marketplace,
)
from .task_bus import (
    DecentralizedTaskBus,
    BusTask,
    AgentNode,
    TaskPriority,
    TaskState,
    get_task_bus,
    reset_task_bus,
)
from .token_bridge import (
    TokenBridge,
    BridgeTransaction,
    BridgeStatus,
    Blockchain,
    LiquidityPool,
    get_token_bridge,
    reset_token_bridge,
)

# Saga Orchestrator for distributed transactions
from .saga_orchestrator import (
    SagaOrchestrator,
    SagaTransaction,
    SagaStep,
    SagaStatus,
    SagaStepStatus,
    get_saga_orchestrator,
    reset_saga_orchestrator,
)

# Also wire the user-facing NexusCredits (now local)
from .nexus_credits import (
    NexusCredits,
    NexusCredit,
    Transaction,
    TransactionType,
    TransactionStatus,
    PackageType,
    ZeroKnowledgeProof,
    get_nexus_credits,
    reset_nexus_credits,
)

# Ledger Engine — Double-Entry Accounting (Stripe/Visa pattern)
from .ledger_engine import (
    LedgerEngine,
    JournalEntry,
    AccountBalance,
    AccountType,
    EntrySide,
    CHART_OF_ACCOUNTS,
    NEPAL_TAX_RATES,
    get_ledger_engine,
    reset_ledger_engine,
)


# Re-export from root-level module: plugin_marketplace.py
from core.plugin_marketplace import (
    Marketplace,
    PluginSDK,
    get_marketplace,
    get_plugin_sdk,
    reset_plugin_system,
)


__all__ = [
    # Saga Orchestrator
    "SagaOrchestrator",
    "SagaTransaction",
    "SagaStep",
    "SagaStatus",
    "SagaStepStatus",
    "get_saga_orchestrator",
    "reset_saga_orchestrator",
    # Contract Executor
    "ContractExecutor",
    "ContractStatus",
    "ContractDuration",
    "ContractType",
    "AuditEntry",
    "get_contract_executor",
    "reset_contract_executor",
    # Nexus Credits
    "NexusCredits",
    "NexusCredit",
    "Transaction",
    "TransactionType",
    "TransactionStatus",
    "PackageType",
    "ZeroKnowledgeProof",
    "get_nexus_credits",
    "reset_nexus_credits",
    # Hybrid Economy
    "HybridEconomy",
    "EconomyMode",
    "EconomyAccount",
    "Task",
    "TaskStatus",
    "get_hybrid_economy",
    "reset_hybrid_economy",
    # Reputation
    "ReputationSystem",
    "ReputationLevel",
    "ReputationScore",
    "StakeRecord",
    "ReputationEvent",
    "get_reputation_system",
    "reset_reputation_system",
    # Sovereign Token
    "SovereignTokenEngine",
    "SVTTransaction",
    "SVTWallet",
    "TxType",
    "get_svt_engine",
    "reset_svt_engine",
    # Marketplace Engine
    "MarketplaceEngine",
    "MarketplaceListing",
    "MarketplaceOrder",
    "ShoppingCart",
    "ShoppingCartItem",
    "Review",
    "ListingStatus",
    "ListingCategory",
    "OrderStatus",
    "PaymentMethod",
    "get_marketplace",
    "reset_marketplace",
    # Task Bus
    "DecentralizedTaskBus",
    "BusTask",
    "AgentNode",
    "TaskPriority",
    "TaskState",
    "get_task_bus",
    "reset_task_bus",
    # Token Bridge
    "TokenBridge",
    "BridgeTransaction",
    "BridgeStatus",
    "Blockchain",
    "LiquidityPool",
    "get_token_bridge",
    "reset_token_bridge",
    # Job Marketplace
    "marketplace",
    "JobMarketplace",
    "JobStatus",
    "PaymentStatus",
    "JobCategory",
    # Ledger Engine
    "LedgerEngine",
    "JournalEntry",
    "AccountBalance",
    "AccountType",
    "EntrySide",
    "CHART_OF_ACCOUNTS",
    "NEPAL_TAX_RATES",
    "get_ledger_engine",
    "reset_ledger_engine",
]
