"""
ASIMNEXUS Economy Layer
=======================
User-facing economic systems: Wallet, Tokens, Escrow, Marketplace, Staking.
"""

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

from .wallet import (
    WalletEngine,
    WalletEntry,
    Balance,
    WalletTransaction,
    WalletStatus,
    TokenType,
    TransactionType as WalletTxType,
    TransactionStatus as WalletTxStatus,
    get_wallet_engine,
    reset_wallet_engine,
)

from .tokens import (
    TokenRegistry,
    TokenDefinition,
    TokenHolding,
    TokenMintEvent,
    TokenStandard,
    TokenStatus,
    initialize_default_tokens,
    DEFAULT_TOKENS,
    get_token_registry,
    reset_token_registry,
)

from .escrow import (
    EscrowEngine,
    EscrowTransaction,
    Dispute,
    EscrowRelease,
    EscrowStatus,
    DisputeReason,
    get_escrow_engine,
    reset_escrow_engine,
)

from .marketplace import (
    MarketplaceEngine,
    Listing,
    MarketplaceOrder,
    Review,
    ListingStatus,
    OrderStatus,
    ListingCategory,
    get_marketplace_engine,
    reset_marketplace_engine,
)

from .staking import (
    StakingEngine,
    StakePosition,
    Validator,
    RewardDistribution,
    StakeStatus,
    ValidatorStatus,
    get_staking_engine,
    reset_staking_engine,
)

__all__ = [
    # Nexus Credits (existing)
    "NexusCredits", "NexusCredit", "Transaction",
    "TransactionType", "TransactionStatus", "PackageType",
    "ZeroKnowledgeProof", "get_nexus_credits", "reset_nexus_credits",

    # Wallet
    "WalletEngine", "WalletEntry", "Balance", "WalletTransaction",
    "WalletStatus", "TokenType",
    "WalletTxType", "WalletTxStatus",
    "get_wallet_engine", "reset_wallet_engine",

    # Tokens
    "TokenRegistry", "TokenDefinition", "TokenHolding", "TokenMintEvent",
    "TokenStandard", "TokenStatus",
    "initialize_default_tokens", "DEFAULT_TOKENS",
    "get_token_registry", "reset_token_registry",

    # Escrow
    "EscrowEngine", "EscrowTransaction", "Dispute", "EscrowRelease",
    "EscrowStatus", "DisputeReason",
    "get_escrow_engine", "reset_escrow_engine",

    # Marketplace
    "MarketplaceEngine", "Listing", "MarketplaceOrder", "Review",
    "ListingStatus", "OrderStatus", "ListingCategory",
    "get_marketplace_engine", "reset_marketplace_engine",

    # Staking
    "StakingEngine", "StakePosition", "Validator", "RewardDistribution",
    "StakeStatus", "ValidatorStatus",
    "get_staking_engine", "reset_staking_engine",
]
