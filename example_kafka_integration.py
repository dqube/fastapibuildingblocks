"""
Example: Kafka Integration Events

This example demonstrates how to use Kafka integration events similar to Wolverine.

Scenario:
- User service creates a user and publishes UserCreatedIntegrationEvent
- Email service consumes the event and sends a welcome email
- Both services use the mediator with automatic event publishing
"""

import asyncio
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from fastapi_building_blocks.domain.events import DomainEvent, IntegrationEvent
from fastapi_building_blocks.application.mediator import Mediator, Request, RequestHandler
from fastapi_building_blocks.infrastructure.messaging import (
    KafkaConfig,
    KafkaIntegrationEventPublisher,
    KafkaIntegrationEventConsumer,
    IntegrationEventHandler,
    EventMapper,
    create_integration_event_mediator,
)


# ============================================================================
# Domain Events (Internal to User Service)
# ============================================================================

class UserCreatedDomainEvent(DomainEvent):
    """Domain event fired when a user is created."""
    user_id: UUID
    email: str
    full_name: str


class UserUpdatedDomainEvent(DomainEvent):
    """Domain event fired when a user is updated."""
    user_id: UUID
    old_email: str
    new_email: str


# ============================================================================
# Integration Events (Cross-Service Communication)
# ============================================================================

class UserCreatedIntegrationEvent(IntegrationEvent):
    """Published to Kafka when a new user is created."""
    user_id: UUID
    email: str
    full_name: str
    created_at: datetime
    
    def get_topic_name(self) -> str:
        return "users.created"


class UserUpdatedIntegrationEvent(IntegrationEvent):
    """Published to Kafka when a user is updated."""
    user_id: UUID
    email: str
    
    def get_topic_name(self) -> str:
        return "users.updated"


# ============================================================================
# Commands and Queries
# ============================================================================

class CreateUserCommand(Request):
    """Command to create a new user."""
    email: str
    full_name: str


class CreateUserResult:
    """Result from creating a user."""
    def __init__(self, user_id: UUID, domain_events: List[DomainEvent]):
        self.user_id = user_id
        self.domain_events = domain_events  # Will be auto-published as integration events


class UpdateUserEmailCommand(Request):
    """Command to update user email."""
    user_id: UUID
    new_email: str


class UpdateUserResult:
    """Result from updating a user."""
    def __init__(self, integration_events: List[IntegrationEvent]):
        self.integration_events = integration_events  # Will be auto-published


# ============================================================================
# Command Handlers (User Service)
# ============================================================================

class CreateUserHandler(RequestHandler[CreateUserCommand, CreateUserResult]):
    """Handler for creating a user."""
    
    async def handle(self, command: CreateUserCommand) -> CreateUserResult:
        # Simulate user creation
        user_id = uuid4()
        print(f"✅ Creating user: {command.email}")
        
        # In real app, you would:
        # - Validate email
        # - Hash password
        # - Save to database
        # - etc.
        
        # Create domain event
        domain_event = UserCreatedDomainEvent(
            user_id=user_id,
            email=command.email,
            full_name=command.full_name,
            aggregate_id=user_id,
        )
        
        return CreateUserResult(
            user_id=user_id,
            domain_events=[domain_event]  # Will be auto-mapped to integration event
        )


class UpdateUserEmailHandler(RequestHandler[UpdateUserEmailCommand, UpdateUserResult]):
    """Handler for updating user email."""
    
    async def handle(self, command: UpdateUserEmailCommand) -> UpdateUserResult:
        print(f"✅ Updating user email: {command.user_id}")
        
        # In real app, you would:
        # - Load user from database
        # - Update email
        # - Save to database
        
        # Create integration event directly (no domain event)
        integration_event = UserUpdatedIntegrationEvent(
            user_id=command.user_id,
            email=command.new_email,
            aggregate_id=command.user_id,
        )
        
        return UpdateUserResult(
            integration_events=[integration_event]
        )


# ============================================================================
# Integration Event Handlers (Email Service, Analytics Service, etc.)
# ============================================================================

class SendWelcomeEmailHandler(IntegrationEventHandler):
    """Handles UserCreatedIntegrationEvent by sending welcome email."""
    
    async def handle(self, event: UserCreatedIntegrationEvent) -> None:
        print(f"\n📧 Email Service: Sending welcome email to {event.email}")
        print(f"   - User ID: {event.user_id}")
        print(f"   - Full Name: {event.full_name}")
        print(f"   - Created At: {event.occurred_at}")
        
        # In real app, you would:
        # - Load email template
        # - Personalize with user data
        # - Send via email service (SendGrid, SES, etc.)
        await asyncio.sleep(0.1)  # Simulate email sending
        
        print(f"   ✅ Welcome email sent successfully!")


class UpdateCRMHandler(IntegrationEventHandler):
    """Handles UserCreatedIntegrationEvent by syncing to CRM."""
    
    async def handle(self, event: UserCreatedIntegrationEvent) -> None:
        print(f"\n👥 CRM Service: Syncing user to CRM")
        print(f"   - User ID: {event.user_id}")
        print(f"   - Email: {event.email}")
        
        # In real app, you would:
        # - Connect to CRM API (Salesforce, HubSpot, etc.)
        # - Create/update contact
        await asyncio.sleep(0.1)  # Simulate CRM sync
        
        print(f"   ✅ User synced to CRM successfully!")


class TrackAnalyticsHandler(IntegrationEventHandler):
    """Handles UserCreatedIntegrationEvent by tracking in analytics."""
    
    async def handle(self, event: UserCreatedIntegrationEvent) -> None:
        print(f"\n📊 Analytics Service: Tracking user signup")
        print(f"   - User ID: {event.user_id}")
        print(f"   - Event: user_signed_up")
        
        # In real app, you would:
        # - Send to analytics service (Mixpanel, Amplitude, etc.)
        # - Track user properties
        await asyncio.sleep(0.1)  # Simulate analytics tracking
        
        print(f"   ✅ Analytics tracked successfully!")


# ============================================================================
# Setup and Configuration
# ============================================================================

async def setup_user_service():
    """Setup user service with mediator and Kafka publisher."""
    print("\n🚀 Setting up User Service...")
    
    # Configure Kafka
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="user-service",
        consumer_group_id="user-service-group",
    )
    
    # Create publisher
    publisher = KafkaIntegrationEventPublisher(config)
    await publisher.start()
    print("   ✅ Kafka publisher started")
    
    # Create event mapper
    mapper = EventMapper()
    
    # Map domain events to integration events
    mapper.register_mapping(
        UserCreatedDomainEvent,
        UserCreatedIntegrationEvent,
        transform=lambda e: {
            "user_id": e.user_id,
            "email": e.email,
            "full_name": e.full_name,
            "created_at": datetime.utcnow(),
        }
    )
    print("   ✅ Event mappings registered")
    
    # Create mediator with integration event publishing
    base_mediator = Mediator()
    mediator = create_integration_event_mediator(base_mediator, publisher, mapper)
    
    # Register handlers
    mediator.register_handler(CreateUserCommand, CreateUserHandler())
    mediator.register_handler(UpdateUserEmailCommand, UpdateUserEmailHandler())
    print("   ✅ Command handlers registered")
    
    print("✅ User Service ready!\n")
    
    return mediator, publisher


async def setup_consumer_services():
    """Setup consumer services (Email, CRM, Analytics)."""
    print("\n🚀 Setting up Consumer Services...")
    
    # Configure Kafka
    config = KafkaConfig(
        bootstrap_servers="localhost:9092",
        service_name="consumer-services",
        consumer_group_id="consumer-services-group",
    )
    
    # Create consumer
    consumer = KafkaIntegrationEventConsumer(config)
    
    # Register handlers for UserCreatedIntegrationEvent
    consumer.register_handler(UserCreatedIntegrationEvent, SendWelcomeEmailHandler())
    consumer.register_handler(UserCreatedIntegrationEvent, UpdateCRMHandler())
    consumer.register_handler(UserCreatedIntegrationEvent, TrackAnalyticsHandler())
    print("   ✅ Integration event handlers registered")
    
    # Start consuming
    await consumer.start(["users.created", "users.updated"])
    print("   ✅ Kafka consumer started")
    
    print("✅ Consumer Services ready!\n")
    
    return consumer


# ============================================================================
# Demo
# ============================================================================

async def run_demo():
    """Run the demo."""
    print("\n" + "="*80)
    print("🎯 Kafka Integration Events Demo (Wolverine-style)")
    print("="*80)
    
    try:
        # Setup services
        mediator, publisher = await setup_user_service()
        consumer = await setup_consumer_services()
        
        # Give consumer time to subscribe
        await asyncio.sleep(2)
        
        print("\n" + "="*80)
        print("📝 Creating Users...")
        print("="*80)
        
        # Create users using mediator
        # Integration events are automatically published!
        
        print("\n--- User 1 ---")
        result1 = await mediator.send(CreateUserCommand(
            email="john@example.com",
            full_name="John Doe"
        ))
        print(f"✅ User created with ID: {result1.user_id}")
        
        await asyncio.sleep(1)  # Wait for consumers to process
        
        print("\n--- User 2 ---")
        result2 = await mediator.send(CreateUserCommand(
            email="jane@example.com",
            full_name="Jane Smith"
        ))
        print(f"✅ User created with ID: {result2.user_id}")
        
        await asyncio.sleep(1)  # Wait for consumers to process
        
        print("\n--- User 3 ---")
        result3 = await mediator.send(CreateUserCommand(
            email="bob@example.com",
            full_name="Bob Johnson"
        ))
        print(f"✅ User created with ID: {result3.user_id}")
        
        # Wait for all events to be processed
        await asyncio.sleep(2)
        
        print("\n" + "="*80)
        print("✅ Demo completed successfully!")
        print("="*80)
        print("\nNotice how:")
        print("1. Commands were sent through the mediator")
        print("2. Domain events were automatically mapped to integration events")
        print("3. Integration events were published to Kafka")
        print("4. Multiple services consumed and processed the events")
        print("5. Everything was loosely coupled and async")
        print("\nThis is the Wolverine pattern in Python! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🧹 Cleaning up...")
        await publisher.stop()
        await consumer.stop()
        print("✅ Cleanup complete")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   Kafka Integration Events Example                          ║
║                      (Wolverine-style for Python)                           ║
║                                                                              ║
║  Prerequisites:                                                             ║
║  1. Start Kafka: docker-compose up -d kafka zookeeper                       ║
║  2. Install deps: pip install aiokafka pydantic-settings                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run the demo
    asyncio.run(run_demo())
