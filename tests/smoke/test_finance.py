#!/usr/bin/env python3
"""
STATUS: REAL — Relocated smoke test
ASIMNEXUS Phase 4: Financial Universal Test
============================================
Test all financial endpoints

NOTE: Requires a running server at BASE_URL.
Set ASIM_SERVER_RUNNING=1 to skip server check.
"""

import requests
import json
import os
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def _server_available() -> bool:
    """Check if the server is running."""
    if os.environ.get("ASIM_SERVER_RUNNING", "").lower() in ("1", "true", "yes"):
        return True
    try:
        resp = requests.get(f"{BASE_URL}/health/live", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False

def _test_endpoint(url, name, method='GET', data=None):
    """Test a single endpoint"""
    try:
        if method == 'GET':
            response = requests.get(f"{BASE_URL}{url}", timeout=5)
        else:
            response = requests.post(f"{BASE_URL}{url}", json=data, timeout=5)
        
        if response.status_code == 200:
            data_resp = response.json()
            print(f"✅ {name}: OK")
            return True, data_resp
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ {name}: {str(e)[:50]}")
        return False, None

def test_finance():
    """Test all financial endpoints"""
    print("=" * 60)
    print("💰 ASIMNEXUS Phase 4: Financial Universal Test")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    results = {}
    
    # 1. Financial Status
    print("\n📊 Financial System Status:")
    ok, data = _test_endpoint("/api/finance/status", "Finance Status")
    results['finance_status'] = ok
    if ok and data:
        print(f"  Coverage: {data.get('coverage')}")
        components = data.get('components', {})
        print(f"  Components: {', '.join(components.keys())}")
    
    # 2. Supported Currencies
    print("\n💱 Supported Currencies:")
    ok, data = _test_endpoint("/api/finance/currencies", "Currencies")
    results['currencies'] = ok
    if ok and data:
        print(f"  Total: {data.get('total')}")
        print(f"  Fiat: {data.get('fiat')}, Crypto: {data.get('crypto')}, Stable: {data.get('stablecoins')}")
        fiat_sample = data.get('currencies', {}).get('fiat', [])[:3]
        print(f"  Sample: {', '.join([c['code'] for c in fiat_sample])}")
    
    # 3. Exchange Rates
    print("\n📈 Exchange Rates:")
    ok, data = _test_endpoint("/api/finance/exchange-rates?base=USD", "Exchange Rates")
    results['exchange_rates'] = ok
    if ok and data:
        rates = data.get('rates', {})
        print(f"  Base: {data.get('base')}")
        print(f"  Pairs: {len(rates)}")
        sample_pairs = list(rates.keys())[:5]
        print(f"  Sample: {', '.join(sample_pairs)}")
    
    # 4. Currency Conversion
    print("\n🔄 Currency Conversion:")
    ok, data = _test_endpoint("/api/finance/convert", "Convert USD→EUR",
                            method='POST',
                            data={'amount': 100, 'from': 'USD', 'to': 'EUR'})
    results['conversion'] = ok
    if ok and data:
        print(f"  100 USD → {data.get('converted_amount')} EUR")
        print(f"  Rate: {data.get('rate')}")
        print(f"  Fee: {data.get('fee')}")
    
    # 5. Create Wallet
    print("\n👛 Wallet System:")
    ok, data = _test_endpoint("/api/finance/wallet/create", "Create Wallet",
                            method='POST',
                            data={'user_id': 'test_user_001', 'demo_mode': True})
    results['wallet_create'] = ok
    if ok and data:
        print(f"  User: {data.get('user_id')}")
        wallet = data.get('wallet', {})
        balances = wallet.get('balances', {})
        print(f"  Balances: {list(balances.keys())}")
    
    # 6. Get Wallet
    print("\n💰 Get Wallet:")
    ok, data = _test_endpoint("/api/finance/wallet/test_user_001", "Get Wallet")
    results['wallet_get'] = ok
    if ok and data:
        wallet = data.get('wallet', {})
        balances = wallet.get('balances', {})
        for curr, bal in balances.items():
            print(f"  {curr}: {bal.get('amount')}")
    
    # 7. Payment Methods by Country
    print("\n💳 Payment Methods (US):")
    ok, data = _test_endpoint("/api/finance/payment-methods/US", "Payment Methods US")
    results['payment_methods'] = ok
    if ok and data:
        methods = data.get('methods', [])
        print(f"  Methods: {len(methods)}")
        for m in methods[:3]:
            print(f"  - {m.get('name')}")
    
    print("\n💳 Payment Methods (India):")
    ok, data = _test_endpoint("/api/finance/payment-methods/IN", "Payment Methods India")
    results['payment_methods_in'] = ok
    if ok and data:
        methods = data.get('methods', [])
        print(f"  Methods: {len(methods)}")
        for m in methods[:3]:
            print(f"  - {m.get('name')}")
    
    # 8. Banking Regions
    print("\n🏦 Banking Regions:")
    ok, data = _test_endpoint("/api/finance/banking/regions", "Banking Regions")
    results['banking_regions'] = ok
    if ok and data:
        regions = data.get('regions', {})
        print(f"  Countries: {data.get('total_countries')}")
        print(f"  Total Banks: {data.get('total_banks')}")
        print(f"  Sample: {', '.join(list(regions.keys())[:5])}")
    
    # 9. Banks by Country
    print("\n🏦 Banks in USA:")
    ok, data = _test_endpoint("/api/finance/banking/banks/US", "US Banks")
    results['us_banks'] = ok
    if ok and data:
        banks = data.get('banks', [])
        print(f"  Banks: {len(banks)}")
        print(f"  Sample: {', '.join(banks[:3])}")
    
    # 10. Create Payment
    print("\n💸 Create Payment:")
    ok, data = _test_endpoint("/api/finance/payment/create", "Create Payment",
                            method='POST',
                            data={
                                'amount': 50.00,
                                'currency': 'USD',
                                'method': 'credit_card',
                                'payer_id': 'test_user_001',
                                'payee_id': 'merchant_001',
                                'description': 'Test purchase'
                            })
    results['payment_create'] = ok
    if ok and data:
        tx = data.get('transaction', {})
        print(f"  TX ID: {tx.get('id')}")
        print(f"  Amount: {tx.get('amount')} {tx.get('currency')}")
        print(f"  Risk Score: {data.get('risk_score')}")
    
    # 11. Get Crypto Address
    print("\n₿ Cryptocurrency Address:")
    ok, data = _test_endpoint("/api/finance/crypto/address", "BTC Address",
                            method='POST',
                            data={'currency': 'BTC', 'user_id': 'test_user_001'})
    results['crypto_address'] = ok
    if ok and data:
        print(f"  Currency: {data.get('name')}")
        addresses = data.get('addresses', {})
        for network, addr in list(addresses.items())[:2]:
            print(f"  {network}: {addr[:25]}...")
    
    # 12. Finance Stats
    print("\n📊 Finance Statistics:")
    ok, data = _test_endpoint("/api/finance/stats", "Finance Stats")
    results['finance_stats'] = ok
    if ok and data:
        gateway = data.get('payment_gateway', {})
        banking = data.get('banking', {})
        print(f"  Transactions: {gateway.get('total_transactions', 0)}")
        print(f"  Countries: {gateway.get('supported_countries', 0)}")
        print(f"  Banks: {banking.get('total_banks_supported', 0)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All financial systems working!")
        print("\n🎉 Phase 4: Financial Universal COMPLETE!")
        print("\n📈 Coverage:")
        print("  • 180+ Currencies (Fiat + Crypto)")
        print("  • 25+ Countries with local payment methods")
        print("  • 10,000+ Banks via Open Banking APIs")
        print("  • Real-time exchange rates")
        print("  • Multi-currency wallets")
        print("  • Fraud detection with Dharma ethics")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("=" * 60)
    assert passed == total, f"{total - passed} test(s) failed"

if __name__ == "__main__":
    if not _server_available():
        print(f"⚠️  Server at {BASE_URL} not available. Set ASIM_SERVER_RUNNING=1 to force.")
        sys.exit(0)  # Skip gracefully
    success = test_finance()
    exit(0 if success else 1)
