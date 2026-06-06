#!/usr/bin/env python3
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS System Healer CLI
===========================
One-command system healing and health check
Usage: python heal_system.py [check|heal|monitor|fix]
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

# Add AsimNexus to path
sys.path.insert(0, str(Path(__file__).parent))

from core.healing import get_system_healer, FrontendBackendMonitor, SystemBalanceChecker

async def main():
    """Main healing CLI"""
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    
    healer = get_system_healer()
    
    print("=" * 60)
    print("🧠 ASIMNEXUS System Healer")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    if command == "check":
        print("🔍 Running full system health check...\n")
        health = await healer.full_system_check()
        
        # Display results
        print(f"Overall Health: {health['overall_health'].upper()}")
        print(f"Checks Passed: {health['healthy_checks']}/{health['total_checks']}\n")
        
        # Backend status
        backend = health['checks']['backend']
        print(f"🖥️  Backend: {backend.get('status', 'unknown')}")
        if 'response_time' in backend:
            print(f"   Response Time: {backend['response_time']:.3f}s")
        if 'error' in backend:
            print(f"   ⚠️  Error: {backend['error']}")
        
        # Frontend status
        frontend = health['checks']['frontend']
        print(f"\n💻 Frontend: {frontend.get('status', 'unknown')}")
        if 'error' in frontend:
            print(f"   ⚠️  Error: {frontend['error']}")
        if 'recommendation' in frontend:
            print(f"   💡 Fix: {frontend['recommendation']}")
        
        # API connectivity
        api = health['checks']['api']
        print(f"\n🌐 API Endpoints: {api.get('up', 0)}/{api.get('total', 0)} UP")
        
        # System balance
        balance = health['checks']['balance']
        print(f"\n⚖️  System Balance:")
        print(f"   CPU: {balance.get('cpu_percent', 0)}%")
        print(f"   Memory: {balance.get('memory_percent', 0)}%")
        print(f"   Disk: {balance.get('disk_percent', 0)}%")
        if balance.get('issues'):
            for issue in balance['issues']:
                print(f"   ⚠️  {issue['component']}: {issue['message']}")
        
        # Bugs
        bugs = health['checks']['bugs']
        print(f"\n🐛 Bugs Detected: {bugs.get('total', 0)}")
        print(f"   Auto-fixable: {bugs.get('auto_fixable', 0)}")
        
        print("\n" + "=" * 60)
        
        # Save report
        report_path = Path("c:/AsimNexus/data/health_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(health, f, indent=2)
        print(f"📄 Report saved to: {report_path}")
    
    elif command == "heal":
        print("🧬 Starting full system healing...\n")
        result = await healer.heal_system()
        
        print(f"Healing Status: {result.get('status', 'unknown').upper()}")
        print(f"Actions Taken: {len(result.get('actions_taken', []))}")
        
        for action in result.get('actions_taken', []):
            print(f"  ✅ {action}")
        
        print("\n" + "-" * 60)
        print("Post-Heal System Health:")
        health = result.get('system_health', {})
        print(f"  Overall: {health.get('overall_health', 'unknown')}")
        print(f"  Checks Passed: {health.get('healthy_checks', 0)}/{health.get('total_checks', 0)}")
    
    elif command == "monitor":
        print("🔄 Starting continuous monitoring (Press Ctrl+C to stop)...\n")
        try:
            await healer.continuous_monitoring(interval_seconds=30)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
    
    elif command == "fix":
        print("🔧 Auto-fixing connection issues...\n")
        monitor = FrontendBackendMonitor()
        fixes = await monitor.fix_connection_issues()
        
        if fixes:
            print("Applied fixes:")
            for fix in fixes:
                print(f"  ✅ {fix}")
        else:
            print("No fixes needed or fixes failed")
    
    elif command == "balance":
        print("⚖️  Checking system balance...\n")
        checker = SystemBalanceChecker()
        balance = await checker.check_balance()
        
        print(f"Balanced: {balance.get('balanced', False)}")
        print(f"CPU: {balance.get('cpu_percent', 0)}%")
        print(f"Memory: {balance.get('memory_percent', 0)}%")
        print(f"Disk: {balance.get('disk_percent', 0)}%")
        
        if balance.get('issues'):
            print("\nIssues:")
            for issue in balance['issues']:
                print(f"  [{issue['severity'].upper()}] {issue['component']}: {issue['message']}")
                print(f"    Action: {issue['action']}")
    
    else:
        print(f"Unknown command: {command}")
        print("\nUsage: python heal_system.py [check|heal|monitor|fix|balance]")
        print("  check    - Run full health check")
        print("  heal     - Run full system healing")
        print("  monitor  - Continuous monitoring")
        print("  fix      - Auto-fix connections")
        print("  balance  - Check resource balance")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
