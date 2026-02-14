"""
Simple example showing before/after redaction.
"""

from src.building_blocks.observability.redaction import RedactionFilter

# Create a redaction filter
filter = RedactionFilter()

print("="*80)
print("LOG REDACTION - BEFORE & AFTER COMPARISON")
print("="*80)

# Example 1: User Login
print("\n1. USER LOGIN REQUEST")
print("-"*80)
before = {
    "event": "user_login",
    "username": "john_doe",
    "password": "MySecretPassword123!",
    "api_key": "sk_live_1234567890abcdef",
    "ip_address": "192.168.1.100"
}
after = filter.redact_dict(before.copy())

print("BEFORE (UNSAFE):")
print(before)
print("\nAFTER (SAFE):")
print(after)

# Example 2: Payment Processing
print("\n\n2. PAYMENT PROCESSING")
print("-"*80)
before = {
    "transaction": "txn_abc123",
    "amount": 99.99,
    "customer": {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "credit_card": "4242-4242-4242-4242",
        "cvv": "123"
    }
}
after = filter.redact_dict(before.copy())

print("BEFORE (UNSAFE):")
print(before)
print("\nAFTER (SAFE):")
print(after)

# Example 3: API Call
print("\n\n3. API CALL WITH AUTHORIZATION")
print("-"*80)
before = {
    "method": "POST",
    "url": "https://api.example.com/users",
    "headers": {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "X-API-Key": "secret_key_abc123"
    }
}
after = filter.redact_dict(before.copy())

print("BEFORE (UNSAFE):")
print(before)
print("\nAFTER (SAFE):")
print(after)

# Example 4: String Redaction
print("\n\n4. STRING MESSAGE REDACTION")
print("-"*80)
messages = [
    "User authenticated with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature",
    "Calling API: https://api.example.com/data?api_key=sk_live_1234567890&user=john",
    "Request with Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=",
]

for msg in messages:
    print(f"\nBEFORE: {msg}")
    print(f"AFTER:  {filter.redact_string(msg)}")

print("\n" + "="*80)
print("✅ SUMMARY: All sensitive data has been masked!")
print("="*80)
