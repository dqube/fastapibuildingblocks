"""Test script to verify mediator implementation."""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi_building_blocks.application import (
    Command,
    CommandHandler,
    Query,
    QueryHandler,
    Mediator,
    Request,
)


# Define test command
class TestCommand(Command):
    """Test command."""
    value: str


# Define test query  
class TestQuery(Query):
    """Test query."""
    id: int


# Define test handlers
class TestCommandHandler(CommandHandler[str]):
    """Test command handler."""
    
    async def handle(self, command: TestCommand) -> str:
        """Handle test command."""
        return f"Command executed: {command.value}"


class TestQueryHandler(QueryHandler[dict]):
    """Test query handler."""
    
    async def handle(self, query: TestQuery) -> dict:
        """Handle test query."""
        return {"id": query.id, "result": "Query executed"}


async def test_mediator():
    """Test the mediator implementation."""
    print("Testing Mediator Pattern Implementation...")
    print("-" * 50)
    
    # Create mediator
    mediator = Mediator()
    print("✓ Mediator created")
    
    # Register handlers
    mediator.register_handler_factory(
        TestCommand,
        lambda: TestCommandHandler()
    )
    print("✓ Command handler registered")
    
    mediator.register_handler_factory(
        TestQuery,
        lambda: TestQueryHandler()
    )
    print("✓ Query handler registered")
    
    # Send command
    command = TestCommand(value="test data")
    result = await mediator.send(command)
    print(f"✓ Command result: {result}")
    assert result == "Command executed: test data"
    
    # Send query
    query = TestQuery(id=123)
    result = await mediator.send(query)
    print(f"✓ Query result: {result}")
    assert result == {"id": 123, "result": "Query executed"}
    
    # Test missing handler
    class UnregisteredCommand(Command):
        pass
    
    try:
        await mediator.send(UnregisteredCommand())
        print("✗ Should have raised ValueError")
        sys.exit(1)
    except ValueError as e:
        print(f"✓ Missing handler error: {str(e)[:50]}...")
    
    print("-" * 50)
    print("✓ All tests passed!")
    print("\nMediator pattern implementation is working correctly!")


if __name__ == "__main__":
    asyncio.run(test_mediator())
