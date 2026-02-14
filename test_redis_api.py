"""
Test Redis Cache API Endpoints

This script demonstrates all the Redis cache API features.
Run the API first: python demo_redis_api.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"


def print_section(title: str):
    """Print section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_response(response: requests.Response, description: str = ""):
    """Print response in a formatted way."""
    if description:
        print(f"\n{description}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_basic_cache():
    """Test basic cache operations."""
    print_section("1. Basic Cache Operations")
    
    # Set cache
    print("\n📝 Setting cache value...")
    response = requests.post(f"{BASE_URL}/cache", json={
        "key": "hello",
        "value": "world",
        "ttl": 300
    })
    print_response(response, "✓ POST /cache")
    
    # Get cache
    print("\n📖 Getting cache value...")
    response = requests.get(f"{BASE_URL}/cache/hello")
    print_response(response, "✓ GET /cache/hello")
    
    # List keys
    print("\n📋 Listing all cache keys...")
    response = requests.get(f"{BASE_URL}/cache")
    print_response(response, "✓ GET /cache")


def test_user_profile():
    """Test user profile caching."""
    print_section("2. User Profile Caching")
    
    # Create user
    print("\n👤 Creating user profile...")
    response = requests.post(f"{BASE_URL}/users", json={
        "user_id": "user123",
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "city": "San Francisco"
    })
    print_response(response, "✓ POST /users")
    
    # Get user
    print("\n📖 Getting user profile (should hit cache)...")
    response = requests.get(f"{BASE_URL}/users/user123")
    print_response(response, "✓ GET /users/user123")
    
    # Create another user
    print("\n👤 Creating another user...")
    response = requests.post(f"{BASE_URL}/users", json={
        "user_id": "user456",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "age": 28,
        "city": "New York"
    })
    print_response(response, "✓ POST /users")


def test_rate_limiting():
    """Test rate limiting with Lua scripts."""
    print_section("3. Rate Limiting (Lua Script)")
    
    print("\n⏱️  Testing rate limit (10 requests/minute)...")
    
    # Make 12 requests to trigger rate limit
    for i in range(12):
        response = requests.get(
            f"{BASE_URL}/rate-limit/check",
            params={"user_id": "test_user", "limit": 10, "window": 60}
        )
        data = response.json()
        status = "✅ Allowed" if data["allowed"] else "⛔ Rate limited"
        print(f"Request {i+1}: {status} - Count: {data['current_count']}/{data['limit']}")


def test_distributed_lock():
    """Test distributed locking."""
    print_section("4. Distributed Locking")
    
    print("\n🔒 Processing resource with lock (2 seconds)...")
    response = requests.post(
        f"{BASE_URL}/lock/payment_gateway",
        params={"processing_time": 2}
    )
    print_response(response, "✓ POST /lock/payment_gateway")
    
    print("\n💡 Try making another request immediately - it will fail to acquire lock!")


def test_task_queue():
    """Test task queue operations."""
    print_section("5. Task Queue (List Operations)")
    
    # Add tasks
    print("\n📝 Adding tasks to queue...")
    tasks = [
        {"id": "task1", "title": "Send email", "description": "Send welcome email", "priority": "high"},
        {"id": "task2", "title": "Process order", "description": "Process order #123", "priority": "medium"},
        {"id": "task3", "title": "Generate report", "description": "Monthly sales report", "priority": "low"}
    ]
    
    for task in tasks:
        response = requests.post(f"{BASE_URL}/queue/tasks", json=task)
        print(f"✓ Added: {task['title']}")
    
    # View all tasks
    print("\n📋 Viewing all tasks in queue...")
    response = requests.get(f"{BASE_URL}/queue/tasks/all")
    print_response(response, "✓ GET /queue/tasks/all")
    
    # Process tasks
    print("\n⚙️  Processing tasks (FIFO)...")
    for i in range(2):
        response = requests.get(f"{BASE_URL}/queue/tasks")
        data = response.json()
        print(f"✓ Processed: {data['task']['title']} (Remaining: {data['remaining_tasks']})")


def test_statistics():
    """Test cache statistics."""
    print_section("6. Cache Statistics")
    
    print("\n📊 Getting cache statistics...")
    response = requests.get(f"{BASE_URL}/stats")
    print_response(response, "✓ GET /stats")


def test_cleanup():
    """Clean up test data."""
    print_section("7. Cleanup")
    
    print("\n🧹 Deleting test data...")
    
    # Delete specific keys
    keys_to_delete = [("hello", "cache"), ("user123", "users"), ("user456", "users")]
    
    for key, endpoint in keys_to_delete:
        try:
            response = requests.delete(f"{BASE_URL}/{endpoint}/{key}")
            if response.status_code == 200:
                print(f"✓ Deleted: {endpoint}/{key}")
        except:
            pass
    
    # Clear queue
    try:
        response = requests.delete(f"{BASE_URL}/queue/tasks")
        if response.status_code == 200:
            print(f"✓ Cleared task queue")
    except:
        pass


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  🚀 REDIS CACHE API DEMO")
    print("="*70)
    print("\n⚠️  Make sure the API is running: python demo_redis_api.py")
    print("📚 API Documentation: http://localhost:8002/docs")
    
    try:
        # Test connection
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("\n❌ API is not responding. Please start it first.")
            return
        
        print("\n✅ API is running!\n")
        
        # Run tests
        test_basic_cache()
        test_user_profile()
        test_rate_limiting()
        test_distributed_lock()
        test_task_queue()
        test_statistics()
        test_cleanup()
        
        print("\n" + "="*70)
        print("  ✅ ALL TESTS COMPLETED!")
        print("="*70)
        print("\n💡 Visit http://localhost:8002/docs for interactive API documentation")
        print("\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API at http://localhost:8002")
        print("   Please start the API first: python demo_redis_api.py\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
