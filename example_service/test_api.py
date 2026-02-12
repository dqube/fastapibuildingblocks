#!/usr/bin/env python3
"""
Quick test script to demonstrate the User Management API.
Run this while the service is running to test all endpoints.
"""

import asyncio
import sys
from uuid import UUID

# Use httpx for async HTTP requests
try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: pip install httpx")
    sys.exit(1)


BASE_URL = "http://localhost:8000"


async def test_api():
    """Test all API endpoints."""
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing User Management API\n")
        print("=" * 60)
        
        # Test health check
        print("\n1️⃣ Testing health check...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Create a user
        print("\n2️⃣ Creating a new user...")
        user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Software engineer passionate about DDD",
        }
        response = await client.post(f"{BASE_URL}/api/v1/users/", json=user_data)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        
        if result['success']:
            user = result['data']
            user_id = user['id']
            print(f"   User ID: {user_id}")
            print(f"   Email: {user['email']}")
            print(f"   Name: {user['first_name']} {user['last_name']}")
            
            # Get user by ID
            print(f"\n3️⃣ Getting user by ID: {user_id}")
            response = await client.get(f"{BASE_URL}/api/v1/users/{user_id}")
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Email: {result['data']['email']}")
            print(f"   Name: {result['data']['full_name']}")
            
            # Create another user
            print("\n4️⃣ Creating another user...")
            user_data2 = {
                "email": "jane.smith@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "bio": "DevOps specialist",
            }
            response = await client.post(f"{BASE_URL}/api/v1/users/", json=user_data2)
            print(f"   Status: {response.status_code}")
            result = response.json()
            user2_id = result['data']['id'] if result['success'] else None
            print(f"   Created: {result['success']}")
            
            # Get all users
            print("\n5️⃣ Getting all users...")
            response = await client.get(f"{BASE_URL}/api/v1/users/")
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Total users: {len(result['data'])}")
            for idx, user in enumerate(result['data'], 1):
                print(f"   {idx}. {user['email']} - {user['full_name']}")
            
            # Update user
            print(f"\n6️⃣ Updating user {user_id}...")
            update_data = {
                "first_name": "Johnny",
                "bio": "Senior software engineer with expertise in microservices",
            }
            response = await client.put(
                f"{BASE_URL}/api/v1/users/{user_id}",
                json=update_data
            )
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Updated name: {result['data']['first_name']}")
            print(f"   Updated bio: {result['data']['bio']}")
            
            # Get active users only
            print("\n7️⃣ Getting active users only...")
            response = await client.get(
                f"{BASE_URL}/api/v1/users/?active_only=true"
            )
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Active users: {len(result['data'])}")
            
            # Delete user
            print(f"\n8️⃣ Deleting user {user_id}...")
            response = await client.delete(f"{BASE_URL}/api/v1/users/{user_id}")
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Deleted: {result['data']['deleted']}")
            
            # Verify user is deactivated (not deleted from storage)
            print(f"\n9️⃣ Verifying user is deactivated...")
            response = await client.get(f"{BASE_URL}/api/v1/users/{user_id}")
            if response.status_code == 200:
                result = response.json()
                print(f"   User still exists: {result['success']}")
                print(f"   Is active: {result['data']['is_active']}")
            
            # Test error handling - user not found
            print("\n🔟 Testing error handling (user not found)...")
            fake_id = "00000000-0000-0000-0000-000000000000"
            response = await client.get(f"{BASE_URL}/api/v1/users/{fake_id}")
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Error message: {result['detail']}")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!\n")
        print("📖 For more details, visit: http://localhost:8000/docs")


if __name__ == "__main__":
    print("⚠️  Make sure the service is running first:")
    print("   cd example_service && ./start.sh\n")
    
    try:
        asyncio.run(test_api())
    except httpx.ConnectError:
        print("\n❌ Cannot connect to the service.")
        print("   Make sure it's running at http://localhost:8000")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
        sys.exit(0)
