"""
Demo: HTTP Client Wrapper

This example demonstrates how to use the HttpClient for external API communication
with various authentication methods, retry logic, circuit breaker, and automatic
correlation ID / consumer ID injection.
"""

import asyncio
import logging
from uuid import uuid4

from building_blocks.infrastructure.http import (
    HttpClient,
    HttpClientConfig,
    BearerAuth,
    BasicAuth,
    ApiKeyAuth,
    OAuth2ClientCredentials,
    ExponentialBackoff,
    NoRetry,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Simple GET Request with Bearer Token
# ============================================================================

async def example_bearer_auth():
    """Example: GET request with Bearer token authentication."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Bearer Token Authentication")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://api.github.com",
        auth_strategy=BearerAuth(token="your_github_token_here"),
        consumer_id="my-service-v1",
        timeout=10.0,
    )
    
    async with HttpClient(config) as client:
        try:
            # Correlation ID is automatically generated if not provided
            response = await client.get("/user")
            print(f"✓ Status: {response.status_code}")
            print(f"✓ User: {response.json().get('login', 'N/A')}")
        except Exception as e:
            print(f"✗ Error: {e}")


# ============================================================================
# Example 2: POST Request with Basic Auth
# ============================================================================

async def example_basic_auth():
    """Example: POST request with Basic authentication."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Basic Authentication")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://httpbin.org",
        auth_strategy=BasicAuth(username="user", password="pass"),
        consumer_id="demo-client",
        log_request_body=True,
        log_response_body=True,
    )
    
    async with HttpClient(config) as client:
        try:
            response = await client.post(
                "/basic-auth/user/pass",
                json={"message": "Hello from HTTP Client"}
            )
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Response: {response.json()}")
        except Exception as e:
            print(f"✗ Error: {e}")


# ============================================================================
# Example 3: API Key Authentication
# ============================================================================

async def example_api_key_auth():
    """Example: API Key authentication in header."""
    print("\n" + "="*80)
    print("EXAMPLE 3: API Key Authentication")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://api.openweathermap.org",
        auth_strategy=ApiKeyAuth(
            api_key="your_api_key_here",
            header_name="X-API-Key",
            location="header"
        ),
        consumer_id="weather-service",
    )
    
    async with HttpClient(config) as client:
        try:
            response = await client.get(
                "/data/2.5/weather",
                params={"q": "London", "units": "metric"}
            )
            print(f"✓ Status: {response.status_code}")
            data = response.json()
            print(f"✓ City: {data.get('name')}")
            print(f"✓ Temp: {data.get('main', {}).get('temp')}°C")
        except Exception as e:
            print(f"✗ Error: {e}")


# ============================================================================
# Example 4: OAuth2 Client Credentials
# ============================================================================

async def example_oauth2():
    """Example: OAuth2 Client Credentials flow."""
    print("\n" + "="*80)
    print("EXAMPLE 4: OAuth2 Client Credentials")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://api.example.com",
        auth_strategy=OAuth2ClientCredentials(
            token_url="https://auth.example.com/oauth/token",
            client_id="your_client_id",
            client_secret="your_client_secret",
            scope="read:api write:api"
        ),
        consumer_id="oauth-client",
    )
    
    async with HttpClient(config) as client:
        try:
            # Token is automatically fetched and refreshed
            response = await client.get("/protected/resource")
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Data: {response.json()}")
        except Exception as e:
            print(f"✗ Error: {e}")


# ============================================================================
# Example 5: Retry Logic with Exponential Backoff
# ============================================================================

async def example_retry_logic():
    """Example: Automatic retry with exponential backoff."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Retry Logic with Exponential Backoff")
    print("="*80)
    
    retry_policy = ExponentialBackoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    )
    
    config = HttpClientConfig(
        base_url="https://httpbin.org",
        retry_policy=retry_policy,
        consumer_id="retry-demo",
        timeout=5.0,
    )
    
    async with HttpClient(config) as client:
        try:
            # Simulate timeout scenario (httpbin/delay)
            response = await client.get("/delay/2")
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Completed after retries")
        except Exception as e:
            print(f"✗ Failed after all retries: {e}")


# ============================================================================
# Example 6: Circuit Breaker Pattern
# ============================================================================

async def example_circuit_breaker():
    """Example: Circuit breaker preventing cascading failures."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Circuit Breaker Pattern")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://httpbin.org",
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=3,
        circuit_breaker_timeout=10.0,
        retry_policy=NoRetry(),  # Disable retry to see circuit breaker
        consumer_id="circuit-demo",
    )
    
    async with HttpClient(config) as client:
        # Simulate multiple failures
        for i in range(5):
            try:
                # This will fail (status 500)
                response = await client.get("/status/500")
                print(f"  Attempt {i+1}: Success")
            except Exception as e:
                print(f"  Attempt {i+1}: Failed - {type(e).__name__}")
        
        # Check circuit breaker stats
        stats = client.get_circuit_breaker_stats()
        if stats:
            print(f"\n✓ Circuit Breaker Stats:")
            print(f"  State: {stats['state']}")
            print(f"  Failures: {stats['failure_count']}/{stats['failure_threshold']}")


# ============================================================================
# Example 7: Custom Correlation ID
# ============================================================================

async def example_custom_correlation_id():
    """Example: Using custom correlation ID for distributed tracing."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Custom Correlation ID")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://httpbin.org",
        consumer_id="trace-demo",
    )
    
    # Simulate a distributed request flow
    correlation_id = str(uuid4())
    print(f"Request Chain Correlation ID: {correlation_id}")
    
    async with HttpClient(config) as client:
        try:
            # Service A calls Service B
            response1 = await client.get(
                "/get",
                correlation_id=correlation_id
            )
            print(f"✓ Service A → Service B: {response1.status_code}")
            
            # Service B calls Service C (same correlation ID)
            response2 = await client.post(
                "/post",
                json={"from": "service_b", "to": "service_c"},
                correlation_id=correlation_id
            )
            print(f"✓ Service B → Service C: {response2.status_code}")
            
            print(f"\n✓ All requests traced with ID: {correlation_id}")
        except Exception as e:
            print(f"✗ Error: {e}")


# ============================================================================
# Example 8: Custom Headers with Consumer ID
# ============================================================================

async def example_custom_headers():
    """Example: Custom headers with automatic consumer ID."""
    print("\n" + "="*80)
    print("EXAMPLE 8: Custom Headers + Consumer ID")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://httpbin.org",
        consumer_id="mobile-app-v2.1.0",
        default_headers={
            "X-App-Version": "2.1.0",
            "X-Platform": "iOS",
            "Accept-Language": "en-US"
        }
    )
    
    async with HttpClient(config) as client:
        try:
            response = await client.get("/headers")
            print(f"✓ Status: {response.status_code}")
            
            headers = response.json().get("headers", {})
            print(f"\n✓ Headers sent:")
            print(f"  X-Correlation-Id: {headers.get('X-Correlation-Id')}")
            print(f"  X-Consumer-Id: {headers.get('X-Consumer-Id')}")
            print(f"  X-App-Version: {headers.get('X-App-Version')}")
            print(f"  X-Platform: {headers.get('X-Platform')}")
        except Exception as e:
            print(f"✗ Error: {e}")


# ============================================================================
# Example 9: Multiple Endpoints with Reusable Client
# ============================================================================

async def example_multiple_requests():
    """Example: Multiple requests with connection pooling."""
    print("\n" + "="*80)
    print("EXAMPLE 9: Multiple Requests (Connection Pooling)")
    print("="*80)
    
    config = HttpClientConfig(
        base_url="https://httpbin.org",
        consumer_id="batch-processor",
        max_connections=50,
        max_keepalive_connections=10,
    )
    
    async with HttpClient(config) as client:
        # Make multiple requests concurrently
        tasks = [
            client.get(f"/uuid") for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in responses if isinstance(r, httpx.Response))
        print(f"✓ Completed {successful} / {len(tasks)} requests")
        
        for i, response in enumerate(responses):
            if isinstance(response, httpx.Response):
                data = response.json()
                print(f"  Request {i+1}: UUID = {data.get('uuid')[:8]}...")


# ============================================================================
# Example 10: Complete Real-World Scenario
# ============================================================================

async def example_real_world_payment_api():
    """Example: Real-world payment API integration."""
    print("\n" + "="*80)
    print("EXAMPLE 10: Real-World Payment API Integration")
    print("="*80)
    
    # Configure client for payment gateway
    config = HttpClientConfig(
        base_url="https://api.payment-gateway.com",
        auth_strategy=ApiKeyAuth(
            api_key="sk_live_your_secret_key",
            header_name="Authorization",
            location="header"
        ),
        consumer_id="ecommerce-backend-v3",
        retry_policy=ExponentialBackoff(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0,
        ),
        enable_circuit_breaker=True,
        circuit_breaker_failure_threshold=5,
        circuit_breaker_timeout=120.0,
        timeout=30.0,
        default_headers={
            "X-API-Version": "2024-02-01",
            "Content-Type": "application/json"
        },
        log_requests=True,
        log_responses=True,
        log_request_body=False,  # Don't log sensitive payment data
        log_response_body=False,
    )
    
    # Simulate payment flow
    order_id = str(uuid4())
    correlation_id = str(uuid4())
    
    print(f"Processing Payment for Order: {order_id}")
    print(f"Correlation ID: {correlation_id}\n")
    
    async with HttpClient(config) as client:
        try:
            # Step 1: Create payment intent
            print("Step 1: Creating payment intent...")
            # response = await client.post(
            #     "/v1/payment_intents",
            #     json={
            #         "amount": 5000,
            #         "currency": "usd",
            #         "metadata": {"order_id": order_id}
            #     },
            #     correlation_id=correlation_id
            # )
            # payment_id = response.json()["id"]
            # print(f"✓ Payment Intent Created: {payment_id}\n")
            
            # Step 2: Confirm payment
            # print("Step 2: Confirming payment...")
            # response = await client.post(
            #     f"/v1/payment_intents/{payment_id}/confirm",
            #     json={"payment_method": "pm_card_visa"},
            #     correlation_id=correlation_id
            # )
            # print(f"✓ Payment Confirmed: {response.json()['status']}\n")
            
            # Step 3: Check payment status
            # print("Step 3: Checking payment status...")
            # response = await client.get(
            #     f"/v1/payment_intents/{payment_id}",
            #     correlation_id=correlation_id
            # )
            # status = response.json()["status"]
            # print(f"✓ Payment Status: {status}\n")
            
            print("✓ Payment flow completed successfully!")
            print(f"✓ All requests traced with correlation ID: {correlation_id}")
            
        except Exception as e:
            print(f"✗ Payment failed: {e}")
            logger.exception("Payment processing error", extra={
                "order_id": order_id,
                "correlation_id": correlation_id
            })


# ============================================================================
# Main
# ============================================================================

import httpx  # Import at top

async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("HTTP CLIENT WRAPPER DEMO")
    print("="*80)
    
    # Run examples (comment out ones that need real API keys)
    # await example_bearer_auth()
    await example_basic_auth()
    # await example_api_key_auth()
    # await example_oauth2()
    await example_retry_logic()
    await example_circuit_breaker()
    await example_custom_correlation_id()
    await example_custom_headers()
    await example_multiple_requests()
    # await example_real_world_payment_api()
    
    print("\n" + "="*80)
    print("✅ Demo completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
