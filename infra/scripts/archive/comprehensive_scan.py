"""
STATUS: REAL — System scan script

Comprehensive ASIMNEXUS System Scan
Scans all files, folders, and code lines
"""

import os
import sys
import ast
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def count_lines_in_file(file_path):
    """Count lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def check_python_syntax(file_path):
    """Check Python syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

def scan_directory(root_dir):
    """Scan directory recursively"""
    results = {
        'total_files': 0,
        'python_files': 0,
        'total_lines': 0,
        'python_lines': 0,
        'folders': 0,
        'syntax_errors': [],
        'file_types': {}
    }
    
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__ and .git
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.venv', 'node_modules']]
        
        results['folders'] += len(dirs)
        results['total_files'] += len(files)
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Count file type
            ext = os.path.splitext(file)[1]
            results['file_types'][ext] = results['file_types'].get(ext, 0) + 1
            
            # Count lines
            lines = count_lines_in_file(file_path)
            results['total_lines'] += lines
            
            # Python specific checks
            if file.endswith('.py'):
                results['python_files'] += 1
                results['python_lines'] += lines
                
                # Check syntax
                is_valid, error = check_python_syntax(file_path)
                if not is_valid:
                    results['syntax_errors'].append({
                        'file': file_path,
                        'error': error
                    })
    
    return results

def test_imports():
    """Test if all core modules can be imported"""
    modules_to_test = [
        'core.advanced_reasoning',
        'core.multi_modal',
        'core.security.zero_trust',
        'core.blockchain',
        'core.ethics',
        'core.voice',
        'core.animation',
        'core.quantum',
        'core.bci',
        'core.ar_vr',
        'core.agent_coordination',
        'core.analytics',
        'core.data_management',
        'core.rpa',
        'core.self_building.reinforcement_learning',
        'core.vedic_ai.digital_dharma_chakra',
        'core.founder_clones.founder_manager',
        'core.worker_agents.agent_manager',
        'core.api.gateway',
        'core.events.bus',
        'core.webhooks.system',
        'virtual_office.platform'
    ]
    
    import_results = {}
    for module in modules_to_test:
        try:
            __import__(module)
            import_results[module] = True
        except Exception as e:
            import_results[module] = False
            logger.error(f"Failed to import {module}: {e}")
    
    return import_results

def main():
    """Main scan function"""
    print("="*70)
    print("  ASIMNEXUS COMPREHENSIVE SYSTEM SCAN")
    print("="*70)
    
    root_dir = r'c:\AsimNexus'
    
    # Scan directory
    print("\n📁 Scanning directory structure...")
    results = scan_directory(root_dir)
    
    print(f"\n📊 Scan Results:")
    print(f"  Total Folders: {results['folders']}")
    print(f"  Total Files: {results['total_files']}")
    print(f"  Python Files: {results['python_files']}")
    print(f"  Total Lines: {results['total_lines']:,}")
    print(f"  Python Lines: {results['python_lines']:,}")
    
    print(f"\n📄 File Types:")
    for ext, count in sorted(results['file_types'].items()):
        print(f"  {ext}: {count}")
    
    print(f"\n🔍 Syntax Errors: {len(results['syntax_errors'])}")
    if results['syntax_errors']:
        for error in results['syntax_errors']:
            print(f"  ❌ {error['file']}: {error['error']}")
    else:
        print("  ✅ No syntax errors found!")
    
    # Test imports
    print("\n🧪 Testing module imports...")
    import_results = test_imports()
    
    passed = sum(1 for v in import_results.values() if v)
    total = len(import_results)
    
    print(f"\n  Import Results: {passed}/{total} passed")
    
    if passed == total:
        print("  ✅ All modules imported successfully!")
    else:
        print("  ❌ Some modules failed to import:")
        for module, success in import_results.items():
            if not success:
                print(f"    ❌ {module}")
    
    # Summary
    print("\n" + "="*70)
    print("  SCAN SUMMARY")
    print("="*70)
    print(f"\nTotal Files: {results['total_files']}")
    print(f"Python Files: {results['python_files']}")
    print(f"Total Lines of Code: {results['total_lines']:,}")
    print(f"Python Lines: {results['python_lines']:,}")
    print(f"Syntax Errors: {len(results['syntax_errors'])}")
    print(f"Import Success: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if len(results['syntax_errors']) == 0 and passed == total:
        print("\n🎉 SYSTEM SCAN PASSED - ALL SYSTEMS OPERATIONAL!")
        return True
    else:
        print("\n⚠️ SYSTEM SCAN FOUND ISSUES")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
