#!/usr/bin/env python3
"""
Test script to verify TOB Calculator setup
"""

import sys

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    errors = []
    
    try:
        import flask
        print("✓ Flask installed")
    except ImportError:
        errors.append("Flask not installed")
    
    try:
        import pdfplumber
        print("✓ pdfplumber installed")
    except ImportError:
        print("✗ pdfplumber not installed (trying PyPDF2...)")
        try:
            import PyPDF2
            print("✓ PyPDF2 installed as fallback")
        except ImportError:
            errors.append("No PDF library installed (need pdfplumber or PyPDF2)")
    
    try:
        import openpyxl
        print("✓ openpyxl installed")
    except ImportError:
        errors.append("openpyxl not installed")
    
    try:
        import requests
        print("✓ requests installed")
    except ImportError:
        errors.append("requests not installed")
    
    return errors

def test_ecb_connection():
    """Test if ECB rates can be fetched"""
    print("\nTesting ECB connection...")
    try:
        import requests
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("✓ ECB rates accessible")
        return True
    except Exception as e:
        print(f"✗ ECB connection failed: {e}")
        return False

def test_folders():
    """Test if required folders exist"""
    print("\nChecking folders...")
    import os
    
    folders = ['templates', 'uploads', 'outputs']
    for folder in folders:
        if os.path.exists(folder):
            print(f"✓ {folder}/ exists")
        else:
            print(f"✗ {folder}/ missing (will be created on first run)")

def main():
    """Run all tests"""
    print("=" * 60)
    print("TOB Calculator - Setup Verification")
    print("=" * 60)
    
    # Test imports
    import_errors = test_imports()
    
    # Test ECB connection
    ecb_ok = test_ecb_connection()
    
    # Test folders
    test_folders()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if import_errors:
        print("\n❌ SETUP INCOMPLETE")
        print("\nMissing packages:")
        for error in import_errors:
            print(f"  - {error}")
        print("\nTo fix, run:")
        print("  pip install -r requirements.txt")
        return 1
    
    if not ecb_ok:
        print("\n⚠️  WARNING: ECB connection failed")
        print("Check your internet connection")
        print("The app may not work without ECB access")
        return 0
    
    print("\n✅ SETUP COMPLETE!")
    print("\nYou're ready to run the app:")
    print("  python app.py")
    print("\nThen open: http://localhost:5000")
    return 0

if __name__ == '__main__':
    sys.exit(main())
