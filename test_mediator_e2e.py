"""
End-to-end test demonstrating the mediator pattern in action.
This test shows how commands and queries flow through the mediator.
"""

import asyncio
import sys
from pathlib import Path

# Add example_service to path
sys.path.insert(0, str(Path(__file__).parent / "example_service"))

from fastapi_building_blocks.application import Mediator
from example_service.app.application.commands.user_commands import (
    CreateUserCommand,
    UpdateUserCommand,
)
from example_service.app.application.queries.user_queries import (
    GetUserByIdQuery,
    GetAllUsersQuery,
)
from example_service.app.application.handlers.user_command_handlers import (
    CreateUserCommandHandler,
    UpdateUserCommandHandler,
)
from example_service.app.application.handlers.user_query_handlers import (
    GetUserByIdQueryHandler,
    GetAllUsersQueryHandler,
)
from example_service.app.infrastructure.repositories.user_repository import (
    InMemoryUserRepository,
)


async def demonstrate_mediator():
    """Demonstrate mediator pattern with real handlers."""
    
    print("=" * 70)
    print("MEDIATOR PATTERN - END-TO-END DEMONSTRATION")
    print("=" * 70)
    
    # Create shared repository (simulating singleton in real app)
    repository = InMemoryUserRepository()
    print("\n✓ Created shared repository")
    
    # Create and configure mediator
    mediator = Mediator()
    
    # Register command handlers
    mediator.register_handler_factory(
        CreateUserCommand,
        lambda: CreateUserCommandHandler(repository)
    )
    mediator.register_handler_factory(
        UpdateUserCommand,
        lambda: UpdateUserCommandHandler(repository)
    )
    
    # Register query handlers
    mediator.register_handler_factory(
        GetUserByIdQuery,
        lambda: GetUserByIdQueryHandler(repository)
    )
    mediator.register_handler_factory(
        GetAllUsersQuery,
        lambda: GetAllUsersQueryHandler(repository)
    )
    
    print("✓ Mediator configured with all handlers")
    print("\n" + "-" * 70)
    
    # Test 1: Create first user via mediator
    print("\n1️⃣  CREATING USER VIA MEDIATOR (Command)")
    print("-" * 70)
    
    create_command = CreateUserCommand(
        email="alice@example.com",
        first_name="Alice",
        last_name="Johnson",
        bio="Software Engineer"
    )
    
    user1 = await mediator.send(create_command)
    print(f"✓ User created: {user1.first_name} {user1.last_name}")
    print(f"  Email: {user1.email}")
    print(f"  ID: {user1.id}")
    print(f"  Bio: {user1.bio}")
    
    # Test 2: Create second user
    print("\n2️⃣  CREATING ANOTHER USER (Command)")
    print("-" * 70)
    
    create_command2 = CreateUserCommand(
        email="bob@example.com",
        first_name="Bob",
        last_name="Smith",
        bio="Product Manager"
    )
    
    user2 = await mediator.send(create_command2)
    print(f"✓ User created: {user2.first_name} {user2.last_name}")
    print(f"  Email: {user2.email}")
    print(f"  ID: {user2.id}")
    
    # Test 3: Get user by ID via mediator
    print("\n3️⃣  GETTING USER BY ID VIA MEDIATOR (Query)")
    print("-" * 70)
    
    get_query = GetUserByIdQuery(user_id=user1.id)
    retrieved_user = await mediator.send(get_query)
    
    print(f"✓ Retrieved user: {retrieved_user.first_name} {retrieved_user.last_name}")
    print(f"  Email: {retrieved_user.email}")
    print(f"  Active: {retrieved_user.is_active}")
    
    # Test 4: Get all users via mediator
    print("\n4️⃣  GETTING ALL USERS VIA MEDIATOR (Query)")
    print("-" * 70)
    
    list_query = GetAllUsersQuery(skip=0, limit=10)
    all_users = await mediator.send(list_query)
    
    print(f"✓ Retrieved {len(all_users)} users:")
    for i, user in enumerate(all_users, 1):
        print(f"  {i}. {user.first_name} {user.last_name} ({user.email})")
    
    # Test 5: Update user via mediator
    print("\n5️⃣  UPDATING USER VIA MEDIATOR (Command)")
    print("-" * 70)
    
    update_command = UpdateUserCommand(
        user_id=user1.id,
        first_name="Alice",
        last_name="Johnson-Updated",
        bio="Senior Software Engineer"
    )
    
    updated_user = await mediator.send(update_command)
    print(f"✓ User updated: {updated_user.first_name} {updated_user.last_name}")
    print(f"  New Bio: {updated_user.bio}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ MEDIATOR PATTERN DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Benefits Demonstrated:")
    print("  ✓ Single mediator handles all commands and queries")
    print("  ✓ Clean separation between request types and handlers")
    print("  ✓ Type-safe command/query dispatching")
    print("  ✓ Simplified endpoint signatures (would use 1 dependency)")
    print("  ✓ Easy to test and mock")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demonstrate_mediator())
