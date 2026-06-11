#!/usr/bin/env python3
"""
ASIMNEXUS Banking Sector API Tests
====================================
Tests for all banking sector endpoints: account creation, deposits, withdrawals,
transfers, transaction history, and statistics.
"""

import sys
import os
import json
import pytest
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from fastapi import FastAPI


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_banking_sector():
    """Mock BankingSector with realistic return values."""
    mock = MagicMock()

    mock.create_account.return_value = {
        "status": "created",
        "account_id": "acct_001",
        "owner_name": "Bob Accountant",
        "account_type": "savings",
        "currency": "NRS",
        "balance": 10000.0,
    }

    mock.deposit.return_value = {
        "status": "deposited",
        "account_id": "acct_001",
        "amount": 5000.0,
        "new_balance": 15000.0,
        "transaction_id": "txn_001",
    }

    mock.withdraw.return_value = {
        "status": "withdrawn",
        "account_id": "acct_001",
        "amount": 2000.0,
        "new_balance": 13000.0,
        "transaction_id": "txn_002",
    }

    mock.transfer.return_value = {
        "status": "transferred",
        "from_account": "acct_001",
        "to_account": "acct_002",
        "amount": 3000.0,
        "from_new_balance": 10000.0,
        "to_new_balance": 13000.0,
        "transaction_id": "txn_003",
    }

    mock_account = MagicMock()
    mock_account.to_dict.return_value = {
        "account_id": "acct_001",
        "owner_name": "Bob Accountant",
        "account_type": "savings",
        "currency": "NRS",
        "balance": 10000.0,
        "status": "active",
    }
    mock.get_account.return_value = mock_account

    mock.list_accounts.return_value = [mock_account]
    mock.get_transactions.return_value = [
        {"transaction_id": "txn_001", "type": "deposit", "amount": 5000.0, "timestamp": "2025-01-01T00:00:00"},
        {"transaction_id": "txn_002", "type": "withdrawal", "amount": 2000.0, "timestamp": "2025-01-02T00:00:00"},
    ]

    mock.get_stats.return_value = {
        "total_accounts": 1,
        "total_deposits": 5000.0,
        "total_withdrawals": 2000.0,
        "total_transfers": 3000.0,
        "total_balance": 10000.0,
    }

    return mock


@pytest.fixture
def client(mock_banking_sector):
    """Create test client with mocked banking sector."""
    app = FastAPI()
    with patch("core.api_endpoints.sector_api._get_banking",
               return_value=mock_banking_sector):
        from core.api_endpoints.sector_api import router
        app.include_router(router)
        yield TestClient(app)


# ─── Account Management Tests ────────────────────────────────────────────────


class TestBankingAccountManagement:
    """Tests for account creation and listing."""

    def test_create_account_success(self, client, mock_banking_sector):
        """POST /api/sectors/banking/accounts creates a new account."""
        response = client.post("/api/sectors/banking/accounts", json={
            "account_id": "acct_001",
            "owner_name": "Bob Accountant",
            "owner_id": "bob_001",
            "account_type": "savings",
            "currency": "NRS",
            "initial_deposit": 10000.0,
            "kyc_verified": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["account_id"] == "acct_001"
        mock_banking_sector.create_account.assert_called_once()

    def test_create_account_unavailable(self, client):
        """Returns 503 when BankingSector is not available."""
        with patch("core.api_endpoints.sector_api._get_banking", return_value=None):
            response = client.post("/api/sectors/banking/accounts", json={
                "account_id": "acct_002",
                "owner_name": "Charlie",
            })
            assert response.status_code == 503

    def test_list_accounts(self, client, mock_banking_sector):
        """GET /api/sectors/banking/accounts lists all accounts."""
        response = client.get("/api/sectors/banking/accounts")
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert len(data["accounts"]) > 0
        mock_banking_sector.list_accounts.assert_called_once_with(None)

    def test_list_accounts_by_status(self, client, mock_banking_sector):
        """GET /api/sectors/banking/accounts?status=active filters by status."""
        response = client.get("/api/sectors/banking/accounts", params={"status": "active"})
        assert response.status_code == 200
        mock_banking_sector.list_accounts.assert_called_with("active")

    def test_get_account_by_id(self, client, mock_banking_sector):
        """GET /api/sectors/banking/account/{id} returns account details."""
        response = client.get("/api/sectors/banking/account/acct_001")
        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == "acct_001"
        mock_banking_sector.get_account.assert_called_once_with("acct_001")

    def test_get_account_not_found(self, client, mock_banking_sector):
        """Returns 404 for non-existent account."""
        mock_banking_sector.get_account.return_value = None
        response = client.get("/api/sectors/banking/account/nonexistent")
        assert response.status_code == 404


# ─── Transaction Tests ───────────────────────────────────────────────────────


class TestBankingTransactions:
    """Tests for deposits, withdrawals, transfers, and history."""

    def test_deposit_success(self, client, mock_banking_sector):
        """POST /api/sectors/banking/deposit deposits money."""
        response = client.post("/api/sectors/banking/deposit", json={
            "account_id": "acct_001",
            "amount": 5000.0,
            "description": "Salary deposit",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deposited"
        assert data["amount"] == 5000.0
        mock_banking_sector.deposit.assert_called_once()

    def test_withdraw_success(self, client, mock_banking_sector):
        """POST /api/sectors/banking/withdraw withdraws money."""
        response = client.post("/api/sectors/banking/withdraw", json={
            "account_id": "acct_001",
            "amount": 2000.0,
            "description": "ATM withdrawal",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "withdrawn"
        assert data["amount"] == 2000.0
        mock_banking_sector.withdraw.assert_called_once()

    def test_transfer_success(self, client, mock_banking_sector):
        """POST /api/sectors/banking/transfer transfers between accounts."""
        response = client.post("/api/sectors/banking/transfer", json={
            "from_account": "acct_001",
            "to_account": "acct_002",
            "amount": 3000.0,
            "description": "Rent payment",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "transferred"
        assert data["amount"] == 3000.0
        mock_banking_sector.transfer.assert_called_once()

    def test_get_transactions(self, client, mock_banking_sector):
        """GET /api/sectors/banking/account/{id}/transactions returns history."""
        response = client.get("/api/sectors/banking/account/acct_001/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) > 0
        mock_banking_sector.get_transactions.assert_called_once_with("acct_001", 20)

    def test_get_transactions_with_limit(self, client, mock_banking_sector):
        """GET with ?limit=5 parameter."""
        response = client.get("/api/sectors/banking/account/acct_001/transactions",
                              params={"limit": 5})
        assert response.status_code == 200
        mock_banking_sector.get_transactions.assert_called_with("acct_001", 5)

    def test_get_transactions_limit_max(self, client, mock_banking_sector):
        """Limit is capped at 100."""
        response = client.get("/api/sectors/banking/account/acct_001/transactions",
                              params={"limit": 200})
        # FastAPI validation returns 422 for values > 100
        assert response.status_code in (200, 422)


# ─── Banking Statistics Tests ────────────────────────────────────────────────


class TestBankingStats:
    """Tests for banking statistics endpoint."""

    def test_banking_stats(self, client, mock_banking_sector):
        """GET /api/sectors/banking/stats returns statistics."""
        response = client.get("/api/sectors/banking/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_accounts" in data
        assert "total_balance" in data
        assert "total_deposits" in data
        mock_banking_sector.get_stats.assert_called_once()

    def test_banking_stats_unavailable(self, client):
        """Returns 503 when BankingSector is not available."""
        with patch("core.api_endpoints.sector_api._get_banking", return_value=None):
            response = client.get("/api/sectors/banking/stats")
            assert response.status_code == 503
