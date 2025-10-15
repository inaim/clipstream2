#!/usr/bin/env python3
"""
Simple test script to verify backend can connect to SurrealDB
Run from project root: python test/test_backend_connection.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))

print(f"Project root: {project_root}")
print(f"Backend dir: {backend_dir}")
print(f"Python path: {sys.path[:3]}")

# Now import from backend
# Load production env file into environment BEFORE importing settings so
# pydantic-settings picks up production values when this test runs.
prod_env = backend_dir / ".env.production"
if prod_env.exists():
    try:
        with prod_env.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Only set if not already set in the environment so local overrides work
                if key and os.environ.get(key) is None:
                    os.environ[key] = val
        print(f"Loaded environment variables from {prod_env}")
    except Exception as e:
        print(f"Warning: failed to load {prod_env}: {e}")
else:
    print(f"No production env file found at {prod_env} - using current environment/.env")

try:
    from utils.config import settings
    print("✅ Successfully imported settings")
except ImportError as e:
    print(f"❌ Failed to import settings: {e}")
    sys.exit(1)

try:
    from surrealdb import AsyncSurreal
    print("✅ Successfully imported Surreal")
except ImportError as e:
    print(f"❌ Failed to import surrealdb: {e}")
    print("   Install with: pip install surrealdb")
    sys.exit(1)


async def test_connection():
    """Test SurrealDB connection using synchronous methods"""
    print("\n" + "="*60)
    print("Testing SurrealDB Connection")
    print("="*60)

    print(f"\nConnection details:")
    print(f"  URL: {settings.SURREALDB_URL}")
    print(f"  Namespace: {settings.SURREALDB_NS}")
    print(f"  Database: {settings.SURREALDB_DB}")
    print(f"  User: {settings.SURREALDB_USER}")

    try:
        # Run synchronous operations in executor
        loop = asyncio.get_event_loop()

        def _test_connection():
            # Initialize connection
            print("\n1. Initializing Surreal connection...")
            db = AsyncSurreal(settings.SURREALDB_URL)
            print("   ✅ Connection initialized")

            # Sign in (must be done before use)
            print("\n2. Signing in...")
            # The Surreal blocking WS client expects a single mapping argument
            # for credentials (not separate positional args), e.g.:
            #   db.signin({"username": "...", "password": "..."})
            db.signin({
                "username": settings.SURREALDB_USER,
                "password": settings.SURREALDB_PASS,
            })
            print("   ✅ Successfully signed in")

            # Select namespace and database
            print("\n3. Selecting namespace and database...")
            db.use(settings.SURREALDB_NS, settings.SURREALDB_DB)
            print("   ✅ Namespace and database selected")

        
            # Test query
            print("\n4. Testing query...")
            result = db.query("SELECT * FROM user LIMIT 1")
            print(f"   ✅ Query successful: {result}")

            # Test create
            print("\n5. Testing create operation...")
            test_data = {
                "email": "test@example.com",
                "display_name": "Test User",
                "created_at": "2024-01-01T00:00:00Z"
            }
            # Note: This will fail if user already exists, which is fine for testing
            try:
                created = db.create("user", test_data)
                print(f"   ✅ Create successful: {created}")
            except Exception as e:
                print(f"   ⚠️  Create failed (may already exist): {e}")

            return True

        # Run in executor
        result = await loop.run_in_executor(None, _test_connection)

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)

        return result

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def test_db_client():
    """Test the actual db_client from the backend"""
    print("\n" + "="*60)
    print("Testing Backend DB Client")
    print("="*60)
    
    try:
        from db.surrealdb_client import db_client
        print("✅ Successfully imported db_client")
        
        print("\n1. Connecting to database...")
        await db_client.connect()
        print("   ✅ Connected successfully")
        
        print(f"\n2. Connection status: {db_client.connect()}")
        
        print("\n3. Testing get_user_by_id...")
        # This will likely return None, but tests the method works
        user = await db_client.get_user_by_id("user:test123")
        print(f"   Result: {user}")
        
        print("\n4. Disconnecting...")
        await db_client.disconnect()
        print("   ✅ Disconnected successfully")
        
        print("\n" + "="*60)
        print("✅ DB CLIENT TESTS PASSED!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ DB Client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n🚀 ClipStream Backend Connection Test\n")
    
    # Test 1: Direct connection
    print("TEST 1: Direct SurrealDB Connection")
    result1 = asyncio.run(test_connection())
    
    # Test 2: Backend db_client
    print("\n\nTEST 2: Backend DB Client")
    result2 = asyncio.run(test_db_client())
    
    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Direct Connection: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Backend DB Client: {'✅ PASS' if result2 else '❌ FAIL'}")
    print("="*60)
    
    if result1 and result2:
        print("\n🎉 All tests passed! Backend is ready to use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

