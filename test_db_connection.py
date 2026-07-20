"""
Test script to verify PostgreSQL database connection.
Run this to ensure the database is configured correctly.

Usage:
    python test_db_connection.py
"""

import sys
from app.database import test_connection, engine, SessionLocal, Base

def main():
    """Test database connection and session factory."""
    
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    
    # Test 1: Test connection
    print("\n[Test 1] Testing PostgreSQL Connection...")
    result = test_connection()
    print(f"Status: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    if result['status'] == 'error':
        print(f"Error: {result['message']}")
        sys.exit(1)
    
    # Test 2: Test engine
    print("\n[Test 2] Testing SQLAlchemy Engine...")
    try:
        with engine.connect() as conn:
            print("✓ Engine created successfully")
            print(f"  Engine: {engine.url}")
    except Exception as e:
        print(f"✗ Engine error: {e}")
        sys.exit(1)
    
    # Test 3: Test session factory
    print("\n[Test 3] Testing SessionLocal Factory...")
    try:
        db = SessionLocal()
        print("✓ Session created successfully")
        db.close()
    except Exception as e:
        print(f"✗ Session error: {e}")
        sys.exit(1)
    
    # Test 4: Test Base
    print("\n[Test 4] Testing SQLAlchemy Base...")
    try:
        print(f"✓ Base class initialized: {Base}")
        print(f"  Models will inherit from: {Base.__class__.__name__}")
    except Exception as e:
        print(f"✗ Base error: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print("\nConfiguration Summary:")
    print(f"  Database Engine: PostgreSQL")
    print(f"  Connection Pool Size: 5")
    print(f"  Max Overflow: 10")
    print(f"  Base Class Ready: Yes")
    print(f"  Session Factory Ready: Yes")
    print("\nNext: Define models by inheriting from Base")
    print("=" * 60)

if __name__ == "__main__":
    main()
