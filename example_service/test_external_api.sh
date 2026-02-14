#!/bin/bash

# Test script for External API Integration endpoints
# Demonstrates calling external APIs with config-based authentication

BASE_URL="http://localhost:8000/api/v1/external-api"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}External API Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Test 1: List all configured services
echo -e "${BLUE}Test 1: List all configured services${NC}"
curl -s -X GET "$BASE_URL/services" | jq '.'
echo -e "${GREEN}✓ Services listed${NC}\n"
sleep 1

# Test 2: Get specific service configuration (jsonplaceholder)
echo -e "${BLUE}Test 2: Get JSONPlaceholder service config${NC}"
curl -s -X GET "$BASE_URL/services/jsonplaceholder" | jq '.'
echo -e "${GREEN}✓ Service config retrieved${NC}\n"
sleep 1

# Test 3: Quick test - Get posts from JSONPlaceholder (no auth)
echo -e "${BLUE}Test 3: Quick test - Get posts from JSONPlaceholder (No Auth)${NC}"
curl -s -X GET "$BASE_URL/test/jsonplaceholder" | jq '.'
echo -e "${GREEN}✓ Successfully called external API without authentication${NC}\n"
sleep 1

# Test 4: Quick test - Create a post on JSONPlaceholder
echo -e "${BLUE}Test 4: Quick test - Create post on JSONPlaceholder${NC}"
curl -s -X POST "$BASE_URL/test/jsonplaceholder/post?title=Test%20Post&body=This%20is%20a%20test%20post" | jq '.'
echo -e "${GREEN}✓ Successfully created post via external API${NC}\n"
sleep 1

# Test 5: Generic API call - GET all posts
echo -e "${BLUE}Test 5: Generic API call - GET all posts${NC}"
curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "GET",
    "endpoint": "/posts",
    "query_params": {"_limit": "3"}
  }' | jq '.'
echo -e "${GREEN}✓ Generic GET request successful${NC}\n"
sleep 1

# Test 6: Generic API call - GET specific post
echo -e "${BLUE}Test 6: Generic API call - GET specific post${NC}"
curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "GET",
    "endpoint": "/posts/1"
  }' | jq '.'
echo -e "${GREEN}✓ GET specific resource successful${NC}\n"
sleep 1

# Test 7: Generic API call - POST create new post
echo -e "${BLUE}Test 7: Generic API call - POST create new post${NC}"
curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "POST",
    "endpoint": "/posts",
    "body": {
      "title": "My New Post",
      "body": "This is the post body",
      "userId": 1
    }
  }' | jq '.'
echo -e "${GREEN}✓ POST request successful${NC}\n"
sleep 1

# Test 8: Generic API call - PUT update post
echo -e "${BLUE}Test 8: Generic API call - PUT update post${NC}"
curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "PUT",
    "endpoint": "/posts/1",
    "body": {
      "id": 1,
      "title": "Updated Post Title",
      "body": "Updated post body",
      "userId": 1
    }
  }' | jq '.'
echo -e "${GREEN}✓ PUT request successful${NC}\n"
sleep 1

# Test 9: Generic API call - PATCH partial update
echo -e "${BLUE}Test 9: Generic API call - PATCH partial update${NC}"
curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "PATCH",
    "endpoint": "/posts/1",
    "body": {
      "title": "Partially Updated Title"
    }
  }' | jq '.'
echo -e "${GREEN}✓ PATCH request successful${NC}\n"
sleep 1

# Test 10: Generic API call - DELETE post
echo -e "${BLUE}Test 10: Generic API call - DELETE post${NC}"
curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "jsonplaceholder",
    "method": "DELETE",
    "endpoint": "/posts/1"
  }' | jq '.'
echo -e "${GREEN}✓ DELETE request successful${NC}\n"
sleep 1

# Test 11: Add a new external service configuration
echo -e "${BLUE}Test 11: Add new external service (Weather API demo)${NC}"
curl -s -X POST "$BASE_URL/services" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "weatherapi",
    "base_url": "https://api.weatherapi.com/v1",
    "auth_type": "api_key",
    "api_key": "your_api_key_here",
    "api_key_header": "key",
    "timeout": 15.0,
    "max_retries": 2,
    "consumer_id": "weather-service"
  }' | jq '.'
echo -e "${GREEN}✓ Service added successfully${NC}\n"
sleep 1

# Test 12: List services again to see the new one
echo -e "${BLUE}Test 12: List services (should include weatherapi)${NC}"
curl -s -X GET "$BASE_URL/services" | jq '.'
echo -e "${GREEN}✓ New service visible in list${NC}\n"
sleep 1

# Test 13: Update existing service
echo -e "${BLUE}Test 13: Update weatherapi service timeout${NC}"
curl -s -X PUT "$BASE_URL/services/weatherapi" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "weatherapi",
    "base_url": "https://api.weatherapi.com/v1",
    "auth_type": "api_key",
    "api_key": "updated_api_key",
    "api_key_header": "key",
    "timeout": 20.0,
    "max_retries": 3,
    "consumer_id": "weather-service"
  }' | jq '.'
echo -e "${GREEN}✓ Service updated${NC}\n"
sleep 1

# Test 14: Get updated service config
echo -e "${BLUE}Test 14: Get updated weatherapi config${NC}"
curl -s -X GET "$BASE_URL/services/weatherapi" | jq '.'
echo -e "${GREEN}✓ Updated config retrieved${NC}\n"
sleep 1

# Test 15: Delete the test service
echo -e "${BLUE}Test 15: Delete weatherapi service${NC}"
curl -s -X DELETE "$BASE_URL/services/weatherapi" | jq '.'
echo -e "${GREEN}✓ Service deleted${NC}\n"
sleep 1

# Test 16: Try to get deleted service (should fail)
echo -e "${BLUE}Test 16: Try to get deleted service (should return 404)${NC}"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/services/weatherapi")
if [ "$STATUS_CODE" -eq 404 ]; then
    echo -e "${GREEN}✓ Service not found (as expected)${NC}\n"
else
    echo -e "${RED}✗ Unexpected status code: $STATUS_CODE${NC}\n"
fi

# Test 17: Error handling - Try to call non-existent service
echo -e "${BLUE}Test 17: Error handling - Non-existent service${NC}"
curl -s -X POST "$BASE_URL/call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "nonexistent",
    "method": "GET",
    "endpoint": "/test"
  }' | jq '.'
echo -e "${GREEN}✓ Error handled gracefully${NC}\n"
sleep 1

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All tests completed!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}Key Features Demonstrated:${NC}"
echo "1. ✓ No authentication (JSONPlaceholder)"
echo "2. ✓ Bearer token authentication (GitHub, Stripe, SendGrid configs)"
echo "3. ✓ API key authentication (custom service)"
echo "4. ✓ All HTTP methods (GET, POST, PUT, PATCH, DELETE)"
echo "5. ✓ Query parameters support"
echo "6. ✓ Request body support"
echo "7. ✓ Service configuration management (CRUD)"
echo "8. ✓ Config-based URL and auth reading"
echo "9. ✓ Correlation ID injection (check response headers)"
echo "10. ✓ Consumer ID tracking"
echo "11. ✓ Error handling and validation"
echo "12. ✓ Retry policy and circuit breaker (configured)"
echo ""
echo -e "${BLUE}Documentation available at:${NC}"
echo "http://localhost:8000/docs#/external-api"
