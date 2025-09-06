#!/usr/bin/env python3
"""
Installation verification script for Stock Scanner backend.
Run this after installation to verify everything is working.
"""
import sys
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version < (3, 9):
        print("⚠️  Warning: Python 3.9+ recommended")
        return False
    return True

def check_virtual_env():
    """Check if running in virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✓ Virtual environment: Active")
        return True
    else:
        print("⚠️  Virtual environment: Not active (recommended)")
        return False

def check_dependencies():
    """Check required dependencies."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'pydantic_settings',
        'yfinance',
        'alpha_vantage',
        'pandas',
        'sqlalchemy',
        'psycopg2'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}: Installed")
        except ImportError:
            print(f"✗ {package}: Missing")
            missing.append(package)
    
    return len(missing) == 0

def check_config_files():
    """Check configuration files."""
    config_files = ['.env', 'requirements.txt']
    all_exist = True
    
    for file in config_files:
        if Path(file).exists():
            print(f"✓ {file}: Found")
        else:
            print(f"✗ {file}: Missing")
            all_exist = False
    
    return all_exist

def test_pydantic_import():
    """Test the specific Pydantic import that was causing issues."""
    try:
        from pydantic_settings import BaseSettings
        print("✓ pydantic-settings: Import successful")
        return True
    except ImportError as e:
        print(f"✗ pydantic-settings: Import failed - {e}")
        return False

def test_yfinance():
    """Test yfinance basic functionality."""
    try:
        import yfinance as yf
        # Quick test without making actual API call
        ticker = yf.Ticker('AAPL')
        print("✓ yfinance: Module loaded successfully")
        print("  Note: Actual data fetching may be rate-limited")
        return True
    except Exception as e:
        print(f"✗ yfinance: Error - {e}")
        return False

def test_alphavantage():
    """Test AlphaVantage module availability."""
    try:
        from alpha_vantage.timeseries import TimeSeries
        print("✓ alpha-vantage: Module loaded successfully")
        
        # Check if API key is configured
        from app.config import get_settings
        settings = get_settings()
        if settings.alphavantage_api_key == "demo":
            print("  ⚠️  Using demo API key (limited functionality)")
            print("  Get free key: https://www.alphavantage.co/support/#api-key")
        else:
            print("  ✓ API key configured")
        return True
    except ImportError:
        print("✗ alpha-vantage: Module not found")
        return False
    except Exception as e:
        print(f"✗ alpha-vantage: Error - {e}")
        return False

def main():
    """Run all verification checks."""
    print("Stock Scanner Backend - Installation Verification")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Dependencies", check_dependencies),
        ("Configuration Files", check_config_files),
        ("Pydantic Settings", test_pydantic_import),
        ("yfinance Module", test_yfinance),
        ("AlphaVantage Module", test_alphavantage),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Error during {name} check: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All checks passed ({passed}/{total})")
        print("🎉 Installation appears to be working correctly!")
        print("\nNext steps:")
        print("1. Start the server: python run_server.py")
        print("2. Visit: http://localhost:8000/docs")
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\nIssues found. Please:")
        print("1. Activate virtual environment: .\\venv\\Scripts\\Activate.ps1")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check configuration files")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)