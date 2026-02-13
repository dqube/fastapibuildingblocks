# Database Architecture - Layered Design

## Overview

The application now uses a properly layered architecture with database-agnostic infrastructure in the `fastapi-building-blocks` library, making it easy to switch between PostgreSQL, SQL Server, MySQL, or any other database supported by SQLAlchemy.

## Architecture Layers

### 1. Building Blocks Infrastructure (Generic/Reusable)

Located in `src/fastapi_building_blocks/infrastructure/`:

#### Database Session Management
- **`database/session.py`**: Abstract `DatabaseSession` base class
- **`database/sqlalchemy_session.py`**: Generic `SQLAlchemySession` implementation
  - Works with PostgreSQL, MySQL, SQL Server, SQLite, etc.
  - Configurable via connection string
  - Handles connection pooling, transactions, lifecycle

#### Repository Pattern
- **`persistence/repositories/base.py`**: In-memory `BaseRepository` (for testing/demo)
- **`persistence/repositories/sqlalchemy_repository.py`**: Generic `SQLAlchemyRepository`
  - Database-agnostic CRUD operations
  - Uses SQLAlchemy Core (not ORM) for flexibility
  - Subclasses only need to implement:
    - `table`: SQLAlchemy Table definition
    - `_row_to_entity()`: Convert DB row to domain entity
    - `_entity_to_dict()`: Convert domain entity to DB dict

### 2. Example Service Implementation (Domain-Specific)

Located in `example_service/app/`:

#### Database Configuration
- **`core/database.py`**: 
  - Creates `SQLAlchemySession` from building blocks
  - Configures connection string from settings
  - Provides `get_db()` dependency for FastAPI

#### Repository Implementation
- **`infrastructure/repositories/postgres_user_repository.py`**:
  - Extends `SQLAlchemyRepository[User]` from building blocks
  - Defines `users_table` schema
  - Implements domain → database mapping
  - Adds user-specific queries (`get_by_email`, `get_active_users`)

## How to Switch Databases

### PostgreSQL (Current)
```python
DATABASE_URL = "postgresql+asyncpg://user:pass@host:5432/dbname"
```

### SQL Server
```python
DATABASE_URL = "mssql+aioodbc://user:pass@host/dbname?driver=ODBC+Driver+18+for+SQL+Server"
```

### MySQL
```python
DATABASE_URL = "mysql+aiomysql://user:pass@host:3306/dbname"
```

### SQLite (Development/Testing)
```python
DATABASE_URL = "sqlite+aiosqlite:///./database.db"
```

## Steps to Add New Database Support

1. **Update connection string** in `example_service/app/core/config.py`:
   ```python
   DATABASE_URL: str = "your_database_connection_string"
   ```

2. **Install database driver** in `example_service/requirements.txt`:
   - PostgreSQL: `asyncpg`
   - SQL Server: `aioodbc`
   - MySQL: `aiomysql`
   - SQLite: `aiosqlite`

3. **Update table definitions** if needed (database-specific types):
   ```python
   # For SQL Server, you might use:
   from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
   
   # For MySQL, you might use:
   from sqlalchemy.dialects.mysql import CHAR
   ```

4. **No changes needed** to:
   - Building blocks infrastructure
   - Repository base classes
   - Business logic/handlers
   - API endpoints

## Benefits of This Architecture

1. **Separation of Concerns**: Generic infrastructure separated from domain-specific code
2. **Reusability**: Building blocks can be used across multiple microservices
3. **Testability**: Easy to swap real database with in-memory for testing
4. **Flexibility**: Switch databases by changing connection string
5. **Maintainability**: Database logic centralized in one place
6. **Migration Path**: Easy to migrate from PostgreSQL → SQL Server → etc.

## Current Stack

- **Database**: PostgreSQL 16 (Alpine)
- **Connection Pool**: SQLAlchemy AsyncEngine (5 connections + 10 overflow)
- **Driver**: asyncpg (PostgreSQL async driver)
- **ORM**: SQLAlchemy Core (Table API, not ORM)
- **Repository Pattern**: Generic base with domain-specific extensions

## Files Modified

### Building Blocks (Generic Infrastructure)
- `src/fastapi_building_blocks/infrastructure/database/sqlalchemy_session.py` ✨ NEW
- `src/fastapi_building_blocks/infrastructure/persistence/repositories/sqlalchemy_repository.py` ✨ NEW
- `src/fastapi_building_blocks/infrastructure/__init__.py` (exports updated)

### Example Service (Domain-Specific)
- `example_service/app/core/database.py` (refactored to use building blocks)
- `example_service/app/infrastructure/repositories/postgres_user_repository.py` (extends building blocks)
- `example_service/app/api/dependencies.py` (uses database session)
- `example_service/app/main.py` (lifecycle events)
- `example_service/requirements.txt` (added sqlalchemy + asyncpg)
- `example_service/init.sql` (PostgreSQL schema)

### Docker
- `docker-compose.observability.yml` (added postgres service)
- Environment variable: `DATABASE_URL` configured in docker-compose

## Testing

```bash
# Create a user
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","last_name":"Test","email":"alice@test.com","username":"alice"}'

# Get all users
curl -X GET "http://localhost:8000/api/v1/users/"

# Verify in database
docker exec -it user-management-db psql -U postgres -d user_management \
  -c "SELECT * FROM users;"
```

## Next Steps

1. **Add Alembic migrations** for schema version control
2. **Implement Unit of Work pattern** for transaction management across repositories
3. **Add connection retry logic** for database resilience
4. **Add read replicas support** for scaling reads
5. **Implement repository caching** with Redis
