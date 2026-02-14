#!/bin/bash
# Test Redis API Endpoints

BASE_URL="http://localhost:8000/api/v1/redis"

echo "======================================================================"
echo "Redis API Testing Suite"
echo "======================================================================"
echo ""

# === Health Check ===
echo "1. Health Check"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# === Basic Cache Operations ===
echo "2. Set Cache Value"
echo "----------------------------------------------------------------------"
curl -s -X POST "$BASE_URL/cache" \
  -H "Content-Type: application/json" \
  -d '{"key": "message", "value": "Hello from Redis!", "ttl": 300}' | python3 -m json.tool
echo ""

echo "3. Get Cache Value"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/cache/message" | python3 -m json.tool
echo ""

echo "4. Set Multiple Values"
echo "----------------------------------------------------------------------"
curl -s -X POST "$BASE_URL/cache" \
  -H "Content-Type: application/json" \
  -d '{"key": "config", "value": {"debug": true, "timeout": 30}}' | python3 -m json.tool
echo ""

# === User Profile (Hash Operations) ===
echo "5. Create User Profile (Hash)"
echo "----------------------------------------------------------------------"
curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john_doe",
    "name": "John Doe",
    "email": "john@example.com",
    "age": 35,
    "city": "New York"
  }' | python3 -m json.tool
echo ""

echo "6. Get User Profile"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/users/john_doe" | python3 -m json.tool
echo ""

echo "7. Create Another User"
echo "----------------------------------------------------------------------"
curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "jane_smith",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "age": 28,
    "city": "San Francisco"
  }' | python3 -m json.tool
echo ""

# === Rate Limiting (Lua Script) ===
echo "8. Rate Limiting Test (10 requests per 60s)"
echo "----------------------------------------------------------------------"
for i in {1..12}; do
  echo "Request $i:"
  curl -s -X POST "$BASE_URL/rate-limit/check" \
    -H "Content-Type: application/json" \
    -d '{"user_id": "test_user", "limit": 10, "window": 60}' | python3 -m json.tool | grep -E '"allowed"|"current_count"|"remaining"'
done
echo ""

# === Task Queue (List Operations) ===
echo "9. Add Tasks to Queue"
echo "----------------------------------------------------------------------"
curl -s -X POST "$BASE_URL/queue/tasks" \
  -H "Content-Type: application/json" \
  -d '{"id": "1", "title": "Send welcome email", "priority": "high"}' | python3 -m json.tool
curl -s -X POST "$BASE_URL/queue/tasks" \
  -H "Content-Type: application/json" \
  -d '{"id": "2", "title": "Process payment", "priority": "urgent"}' | python3 -m json.tool
curl -s -X POST "$BASE_URL/queue/tasks" \
  -H "Content-Type: application/json" \
  -d '{"id": "3", "title": "Generate report", "priority": "normal"}' | python3 -m json.tool
echo ""

echo "10. View All Tasks"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/queue/tasks/all" | python3 -m json.tool
echo ""

echo "11. Get Next Task (FIFO)"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/queue/tasks" | python3 -m json.tool
echo ""

echo "12. View Remaining Tasks"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/queue/tasks/all" | python3 -m json.tool
echo ""

# === Distributed Locking ===
echo "13. Distributed Lock (Sequential)"
echo "----------------------------------------------------------------------"
curl -s -X POST "$BASE_URL/lock/payment_gateway?processing_time=1" | python3 -m json.tool
echo ""

# === List Cache Keys ===
echo "14. List All Cache Keys"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/cache?pattern=*&limit=50" | python3 -m json.tool
echo ""

# === Cache Statistics ===
echo "15. Cache Statistics"
echo "----------------------------------------------------------------------"
curl -s "$BASE_URL/stats" | python3 -m json.tool
echo ""

echo "======================================================================"
echo "✅ All tests completed!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  • Open Swagger UI: http://localhost:8000/docs"
echo "  • View Redis data: http://localhost:5540 (RedisInsight - if started)"
echo "  • Check container logs: docker logs user-management-api"
echo ""
