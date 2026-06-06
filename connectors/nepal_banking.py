
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Nepal Banking Connector - Nepal Banking System Integration
Integrates with Nepal's banking system and payment gateways
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class BankType(Enum):
    """Types of banks in Nepal"""
    COMMERCIAL = "commercial"
    DEVELOPMENT = "development"
    COOPERATIVE = "cooperative"
    MICROFINANCE = "microfinance"
    DIGITAL = "digital"


class PaymentGateway(Enum):
    """Payment gateways in Nepal"""
    ESEWA = "esewa"
    KHALTI = "khalti"
    FONEPAY = "fonepay"
    IME_PAY = "ime_pay"
    PRABHU_PAY = "prabhu_pay"
    NTC_PAY = "ntc_pay"


class TransactionStatus(Enum):
    """Transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class BankAccount:
    """Represents a bank account"""
    account_id: str
    bank_name: str
    account_number: str
    account_type: str
    balance: float
    currency: str
    created_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = data['created_at'].isoformat()
        return data


@dataclass
class Transaction:
    """Represents a transaction"""
    transaction_id: str
    account_id: str
    gateway: PaymentGateway
    amount: float
    currency: str
    status: TransactionStatus
    recipient: str
    description: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['gateway'] = data['gateway'].value
        data['status'] = data['status'].value
        data['created_at'] = data['created_at'].isoformat()
        if data['completed_at']:
            data['completed_at'] = data['completed_at'].isoformat()
        return data


class NepalBanking:
    """
    Nepal Banking Connector
    Integrates with Nepal's banking system and payment gateways
    """
    
    def __init__(self):
        self.bank_accounts: List[BankAccount] = []
        self.transactions: List[Transaction] = []
        
        # Nepal banks
        self.nepal_banks = {
            "NIC Asia Bank": {"type": BankType.COMMERCIAL, "code": "NICA"},
            "Nabil Bank": {"type": BankType.COMMERCIAL, "code": "NABIL"},
            "Standard Chartered Nepal": {"type": BankType.COMMERCIAL, "code": "SCB"},
            "Nepal Investment Bank": {"type": BankType.COMMERCIAL, "code": "NIBL"},
            "Agricultural Development Bank": {"type": BankType.DEVELOPMENT, "code": "ADBL"},
            "Rastriya Banijya Bank": {"type": BankType.COMMERCIAL, "code": "RBBL"},
            "Nepal Bangladesh Bank": {"type": BankType.COMMERCIAL, "code": "NBB"},
            "Kumari Bank": {"type": BankType.COMMERCIAL, "code": "KBL"},
            "NMB Bank": {"type": BankType.COMMERCIAL, "code": "NMB"},
            "Laxmi Capital": {"type": BankType.DEVELOPMENT, "code": "LCM"}
        }
        
        # Payment gateway configurations
        self.gateway_configs = {
            PaymentGateway.ESEWA: {
                "api_endpoint": "https://esewa.com.np/api",
                "merchant_id": "ASIM_NEXUS",
                "fees": 0.025  # 2.5%
            },
            PaymentGateway.KHALTI: {
                "api_endpoint": "https://khalti.com/api",
                "merchant_id": "ASIM_NEXUS",
                "fees": 0.02  # 2%
            },
            PaymentGateway.FONEPAY: {
                "api_endpoint": "https://fonepay.com.np/api",
                "merchant_id": "ASIM_NEXUS",
                "fees": 0.015  # 1.5%
            },
            PaymentGateway.IME_PAY: {
                "api_endpoint": "https://imepay.com.np/api",
                "merchant_id": "ASIM_NEXUS",
                "fees": 0.02  # 2%
            }
        }
        
        logger.info("Nepal Banking Connector initialized")
    
    async def add_bank_account(
        self,
        bank_name: str,
        account_number: str,
        account_type: str,
        initial_balance: float = 0.0
    ) -> BankAccount:
        """
        Add a bank account
        
        Args:
            bank_name: Name of the bank
            account_number: Account number
            account_type: Type of account (savings, current)
            initial_balance: Initial balance in NPR
            
        Returns:
            BankAccount object
        """
        account_id = f"acc_{bank_name}_{datetime.now().timestamp()}"
        
        logger.info(f"Adding bank account: {bank_name}")
        
        account = BankAccount(
            account_id=account_id,
            bank_name=bank_name,
            account_number=account_number,
            account_type=account_type,
            balance=initial_balance,
            currency="NPR",
            created_at=datetime.now()
        )
        
        self.bank_accounts.append(account)
        
        logger.info(f"Bank account added: {account_id}")
        
        return account
    
    async def process_payment(
        self,
        gateway: PaymentGateway,
        amount: float,
        recipient: str,
        account_id: str,
        description: str = ""
    ) -> Transaction:
        """
        Process payment through Nepal payment gateway
        
        Args:
            gateway: Payment gateway to use
            amount: Amount in NPR
            recipient: Recipient identifier
            account_id: Source account ID
            description: Transaction description
            
        Returns:
            Transaction object
        """
        transaction_id = f"txn_{gateway.value}_{datetime.now().timestamp()}"
        
        logger.info(f"Processing payment via {gateway.value}: {amount} NPR")
        
        # Get gateway config
        config = self.gateway_configs.get(gateway)
        if not config:
            logger.error(f"Unsupported gateway: {gateway.value}")
            return None
        
        transaction = Transaction(
            transaction_id=transaction_id,
            account_id=account_id,
            gateway=gateway,
            amount=amount,
            currency="NPR",
            status=TransactionStatus.PROCESSING,
            recipient=recipient,
            description=description,
            created_at=datetime.now(),
            completed_at=None
        )
        
        try:
            # Simulate payment processing
            await asyncio.sleep(1)
            
            # Calculate fees
            fee_rate = config.get('fees', 0.02)
            fee = amount * fee_rate
            total_amount = amount + fee
            
            # Update account balance
            account = await self._get_account_by_id(account_id)
            if account and account.balance >= total_amount:
                account.balance -= total_amount
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.now()
                
                logger.info(f"Payment successful: {transaction_id}")
            else:
                transaction.status = TransactionStatus.FAILED
                logger.error(f"Insufficient balance for {account_id}")
                
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            transaction.status = TransactionStatus.FAILED
        
        self.transactions.append(transaction)
        
        return transaction
    
    async def check_balance(self, account_id: str) -> Optional[float]:
        """
        Check account balance
        
        Args:
            account_id: Account ID
            
        Returns:
            Account balance or None if not found
        """
        account = await self._get_account_by_id(account_id)
        if account:
            return account.balance
        return None
    
    async def transfer_between_accounts(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: float,
        description: str = ""
    ) -> bool:
        """
        Transfer funds between accounts
        
        Args:
            from_account_id: Source account ID
            to_account_id: Destination account ID
            amount: Amount to transfer
            description: Transfer description
            
        Returns:
            True if successful
        """
        logger.info(f"Transferring {amount} NPR from {from_account_id} to {to_account_id}")
        
        from_account = await self._get_account_by_id(from_account_id)
        to_account = await self._get_account_by_id(to_account_id)
        
        if not from_account or not to_account:
            logger.error("One or both accounts not found")
            return False
        
        if from_account.balance < amount:
            logger.error("Insufficient balance")
            return False
        
        try:
            from_account.balance -= amount
            to_account.balance += amount
            
            # Record transaction for from_account
            self.transactions.append(Transaction(
                transaction_id=f"transfer_{datetime.now().timestamp()}",
                account_id=from_account_id,
                gateway=PaymentGateway.ESEWA,  # Internal transfer
                amount=amount,
                currency="NPR",
                status=TransactionStatus.COMPLETED,
                recipient=to_account_id,
                description=f"Transfer to {to_account_id}: {description}",
                created_at=datetime.now(),
                completed_at=datetime.now()
            ))
            
            logger.info("Transfer successful")
            return True
            
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return False
    
    async def get_transaction_status(self, transaction_id: str) -> Optional[TransactionStatus]:
        """
        Get transaction status
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction status or None if not found
        """
        for transaction in self.transactions:
            if transaction.transaction_id == transaction_id:
                return transaction.status
        return None
    
    async def get_account_transactions(self, account_id: str, limit: int = 20) -> List[Transaction]:
        """
        Get transactions for an account
        
        Args:
            account_id: Account ID
            limit: Maximum transactions to return
            
        Returns:
            List of transactions
        """
        account_transactions = [
            t for t in self.transactions
            if t.account_id == account_id
        ]
        
        # Sort by created time (newest first)
        account_transactions.sort(key=lambda t: t.created_at, reverse=True)
        
        return account_transactions[:limit]
    
    async def _get_account_by_id(self, account_id: str) -> Optional[BankAccount]:
        """Get account by ID"""
        for account in self.bank_accounts:
            if account.account_id == account_id:
                return account
        return None
    
    async def get_banking_summary(self) -> Dict:
        """Get summary of banking operations"""
        total_balance = sum(acc.balance for acc in self.bank_accounts)
        
        gateway_stats = {}
        for transaction in self.transactions:
            gateway = transaction.gateway.value
            gateway_stats[gateway] = gateway_stats.get(gateway, 0) + 1
        
        status_counts = {}
        for transaction in self.transactions:
            status = transaction.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_accounts': len(self.bank_accounts),
            'total_balance': total_balance,
            'total_transactions': len(self.transactions),
            'gateway_usage': gateway_stats,
            'transaction_status': status_counts,
            'supported_banks': list(self.nepal_banks.keys()),
            'supported_gateways': list(self.gateway_configs.keys())
        }
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str = "NPR") -> Optional[float]:
        """
        Get exchange rate (simplified)
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Exchange rate or None
        """
        # Simplified exchange rates (in production, fetch from NRB)
        rates = {
            "USD": 133.15,
            "EUR": 144.50,
            "GBP": 169.20,
            "INR": 1.60,
            "CNY": 18.45,
            "JPY": 0.89,
            "AED": 36.25,
            "SAR": 35.50
        }
        
        if from_currency == "NPR":
            return 1.0 / rates.get(to_currency, 1.0)
        elif from_currency in rates:
            return rates[from_currency]
        else:
            return None
    
    async def export_banking_data(self) -> Dict:
        """Export banking data for backup"""
        return {
            'bank_accounts': [a.to_dict() for a in self.bank_accounts],
            'transactions': [t.to_dict() for t in self.transactions],
            'nepal_banks': self.nepal_banks,
            'gateway_configs': self.gateway_configs
        }
    
    async def import_banking_data(self, data: Dict) -> None:
        """Import banking data from backup"""
        try:
            self.bank_accounts = []
            for account_data in data.get('bank_accounts', []):
                account = BankAccount(
                    account_id=account_data['account_id'],
                    bank_name=account_data['bank_name'],
                    account_number=account_data['account_number'],
                    account_type=account_data['account_type'],
                    balance=account_data['balance'],
                    currency=account_data['currency'],
                    created_at=datetime.fromisoformat(account_data['created_at'])
                )
                self.bank_accounts.append(account)
            
            self.transactions = []
            for trans_data in data.get('transactions', []):
                transaction = Transaction(
                    transaction_id=trans_data['transaction_id'],
                    account_id=trans_data['account_id'],
                    gateway=PaymentGateway(trans_data['gateway']),
                    amount=trans_data['amount'],
                    currency=trans_data['currency'],
                    status=TransactionStatus(trans_data['status']),
                    recipient=trans_data['recipient'],
                    description=trans_data['description'],
                    created_at=datetime.fromisoformat(trans_data['created_at']),
                    completed_at=datetime.fromisoformat(trans_data['completed_at']) if trans_data.get('completed_at') else None
                )
                self.transactions.append(transaction)
            
            self.nepal_banks = data.get('nepal_banks', self.nepal_banks)
            self.gateway_configs = data.get('gateway_configs', self.gateway_configs)
            
            logger.info(f"Imported {len(self.bank_accounts)} accounts and {len(self.transactions)} transactions")
            
        except Exception as e:
            logger.error(f"Failed to import banking data: {e}")
            raise
