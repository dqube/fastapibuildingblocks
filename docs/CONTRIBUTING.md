# Contributing to FastAPI Building Blocks

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose (for running services)
- Git
- A code editor with Python support (VS Code, PyCharm, etc.)

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd fastapibuildingblocks
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"  # Includes development dependencies
   ```

4. **Start required services:**
   ```bash
   cd example_service
   docker-compose up -d postgres redis kafka
   ```

5. **Verify setup:**
   ```bash
   pytest tests/
   python examples/demo_http_client.py
   ```

## Project Structure

```
fastapibuildingblocks/
├── src/building_blocks/       # Core library package
│   ├── api/                   # API layer (exception handlers, responses)
│   ├── application/           # Application layer (mediator, CQRS)
│   ├── domain/                # Domain layer (entities, events)
│   ├── infrastructure/        # Infrastructure (DB, cache, HTTP)
│   └── observability/         # Logging, tracing, metrics
├── example_service/           # Reference implementation
│   ├── app/                   # Service application code
│   │   ├── api/v1/           # API versioning
│   │   ├── application/      # Commands, queries, handlers
│   │   ├── core/             # Configuration, database
│   │   ├── domain/           # Domain models
│   │   └── infrastructure/   # Repository implementations
│   ├── tests/                # Service-specific tests
│   └── docs/                 # Service documentation
├── examples/                  # Demo scripts & integration tests
├── tests/                     # Unit tests for building blocks
├── docs/                      # Project documentation
├── .cursorrules              # AI coding rules (Cursor)
├── .clinerules               # AI coding rules (Cline)
└── CONTRIBUTING.md           # This file
```

## Coding Standards

### Architecture Principles

We follow **Clean Architecture** with **Domain-Driven Design**:

1. **Domain Layer**: Core business logic, entities, value objects, domain events
   - No dependencies on outer layers
   - Pure Python, no framework code

2. **Application Layer**: Use cases, commands, queries, handlers
   - Depends only on domain layer
   - Orchestrates business workflows

3. **Infrastructure Layer**: External integrations, databases, APIs
   - Implements interfaces defined in domain
   - Depends on domain and application layers

4. **API Layer**: HTTP endpoints, request/response handling
   - Depends on all layers
   - FastAPI routes and models

### Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run before committing:
```bash
black .
isort .
flake8
mypy src/
```

### Python Conventions

1. **Type Hints**: Required for all functions and methods
   ```python
   async def get_user(user_id: int) -> Optional[User]:
       ...
   ```

2. **Async/Await**: Use for all I/O operations
   ```python
   async def fetch_data(url: str) -> dict:
       async with httpx.AsyncClient() as client:
           response = await client.get(url)
           return response.json()
   ```

3. **Dependency Injection**: Use FastAPI's DI system
   ```python
   @router.get("/users/{id}")
   async def get_user(
       id: int,
       db: AsyncSession = Depends(get_db),
       repository: IUserRepository = Depends(get_user_repository)
   ):
       ...
   ```

4. **Error Handling**: Use custom exceptions and global handlers
   ```python
   if not user:
       raise UserNotFoundException(user_id=id)
   ```

5. **Logging**: Use structured logging with context
   ```python
   logger.info(
       "User created",
       extra={"user_id": user.id, "correlation_id": correlation_id}
   )
   ```

### Security

1. **Never log sensitive data**: Passwords, tokens, API keys are automatically redacted
2. **Validate all inputs**: Use Pydantic models
3. **Use parameterized queries**: SQLAlchemy handles this
4. **Environment variables**: Use for configuration, never hardcode secrets

## Making Changes

### Feature Development Workflow

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow the layer-by-layer approach:**
   
   a. **Domain Layer**: Define entities, events, repository interfaces
   ```python
   # domain/entities/product.py
   class Product(Entity):
       name: str
       price: Decimal
       sku: str
   ```

   b. **Application Layer**: Create commands/queries and handlers
   ```python
   # application/commands/create_product.py
   @dataclass
   class CreateProductCommand:
       name: str
       price: Decimal
       sku: str
   
   class CreateProductCommandHandler(IRequestHandler[CreateProductCommand, ProductDto]):
       async def handle(self, request: CreateProductCommand) -> ProductDto:
           ...
   ```

   c. **Infrastructure Layer**: Implement repositories
   ```python
   # infrastructure/repositories/product_repository.py
   class ProductRepository(IProductRepository):
       async def add(self, product: Product) -> None:
           ...
   ```

   d. **API Layer**: Create endpoints
   ```python
   # api/v1/endpoints/products.py
   @router.post("/", response_model=ProductResponse)
   async def create_product(
       request: CreateProductRequest,
       mediator: Mediator = Depends(get_mediator)
   ):
       ...
   ```

3. **Write tests** (see Testing section)

4. **Update documentation** (see Documentation section)

5. **Run quality checks:**
   ```bash
   black .
   isort .
   flake8
   mypy src/
   pytest
   ```

6. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add product management endpoints"
   ```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add Redis caching support
fix: resolve async session leak in repository
docs: update API documentation with examples
refactor: extract HTTP client configuration
test: add integration tests for Kafka consumer
```

## Testing

### Unit Tests

Location: `tests/`

Test individual components in isolation:

```python
# tests/application/test_create_user_handler.py
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_create_user_command_handler():
    # Arrange
    mock_repo = AsyncMock(spec=IUserRepository)
    handler = CreateUserCommandHandler(mock_repo)
    command = CreateUserCommand(name="John", email="john@example.com")
    
    # Act
    result = await handler.handle(command)
    
    # Assert
    assert result.name == "John"
    mock_repo.add.assert_called_once()
```

### Integration Tests

Location: `examples/`

Test end-to-end workflows with real services:

```python
# examples/test_user_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user_api():
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/api/v1/users",
            json={"name": "John", "email": "john@example.com"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John"
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/

# Integration tests only
pytest examples/

# Specific test file
pytest tests/application/test_create_user_handler.py

# With coverage
pytest --cov=src/building_blocks --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Requirements

- All new features must include tests
- Aim for >80% code coverage
- Tests should be independent and idempotent
- Clean up test data after each test
- Use fixtures for common setup

## Documentation

### Code Documentation

1. **Docstrings**: Required for all public functions and classes

```python
async def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve a user by their email address.
    
    Args:
        email: The user's email address (case-insensitive)
        
    Returns:
        User object if found, None otherwise
        
    Raises:
        DatabaseError: If database connection fails
        
    Example:
        >>> user = await get_user_by_email("john@example.com")
        >>> print(user.name)
        'John Doe'
    """
```

2. **Type Hints**: Required for all parameters and return values

3. **Comments**: Use sparingly, explain "why" not "what"

### Project Documentation

Location: `docs/`

When adding new features:

1. **Update existing docs** if they're affected
2. **Create new docs** for major features
3. **Include examples** in documentation
4. **Add to README.md** if it's a core feature

### API Documentation

FastAPI generates automatic OpenAPI docs. Enhance them:

```python
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a new user account with the provided information",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid request data"},
        409: {"description": "User already exists"}
    }
)
async def create_user(request: CreateUserRequest):
    """
    Create a new user with the following information:
    
    - **name**: User's full name (1-100 characters)
    - **email**: Valid email address
    - **password**: Strong password (minimum 8 characters)
    """
```

## Submitting Changes

### Before Submitting

1. **Run all checks:**
   ```bash
   # Code formatting
   black .
   isort .
   
   # Linting
   flake8
   
   # Type checking
   mypy src/
   
   # Tests
   pytest
   
   # Integration tests (with Docker services running)
   pytest examples/
   ```

2. **Update documentation**
3. **Review your changes**
4. **Test manually** if applicable

### Pull Request Process

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** with:
   - Clear title and description
   - Reference to related issues
   - List of changes
   - Screenshots (if UI changes)
   - Breaking changes (if any)

3. **PR Template:**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Changes Made
   - Added X feature
   - Fixed Y issue
   - Updated Z documentation
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests added/updated
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   - [ ] Tests pass locally
   ```

4. **Address review feedback**

5. **After approval**, changes will be merged

## Additional Guidelines

### Adding Dependencies

1. Add to `pyproject.toml`
2. Document why it's needed
3. Ensure it's compatible with existing dependencies
4. Update documentation

### Breaking Changes

1. Document in PR description
2. Update CHANGELOG.md
3. Add migration guide if needed
4. Version bump accordingly

### Performance Considerations

1. Use async/await for I/O
2. Implement caching where appropriate
3. Use database indexes
4. Batch operations when possible
5. Profile before optimizing

### Accessibility

1. Use semantic HTML in documentation
2. Provide text alternatives
3. Ensure keyboard navigation
4. Test with screen readers (if UI)

## Getting Help

- **Documentation**: Check `docs/` folder
- **Examples**: See `examples/` folder
- **Reference Implementation**: See `example_service/`
- **AI Rules**: See `.cursorrules` and `.clinerules`

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Be patient with newcomers
- Follow project guidelines

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to FastAPI Building Blocks! 🚀
