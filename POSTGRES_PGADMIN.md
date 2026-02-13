# PostgreSQL and pgAdmin Setup

## Overview

The application uses PostgreSQL as the database with pgAdmin for database management. All data is persisted using Docker volumes.

## Services

### PostgreSQL Database
- **Container**: `user-management-db`
- **Port**: `5432` (exposed to host)
- **Image**: `postgres:16-alpine`
- **Database**: `user_management`
- **Username**: `postgres`
- **Password**: `postgres`
- **Volume**: `postgres-data` (persists all database data)

### pgAdmin
- **Container**: `pgadmin`
- **Port**: `5050` (exposed to host)
- **Image**: `dpage/pgadmin4:latest`
- **Web URL**: http://localhost:5050
- **Login Email**: `admin@admin.com`
- **Login Password**: `admin`
- **Volume**: `pgadmin-data` (persists pgAdmin configuration)

## Access pgAdmin

1. **Open web browser**: http://localhost:5050

2. **Login**:
   - Email: `admin@admin.com`
   - Password: `admin`

3. **Server automatically configured**:
   - Name: "User Management DB"
   - Host: `postgres`
   - Port: `5432`
   - Database: `user_management`
   - Username: `postgres`
   - Password: (saved automatically)

## Data Persistence

All data is stored in Docker volumes that persist even when containers are stopped or removed:

### Volumes
```bash
# List all volumes
docker volume ls --filter "name=fastapibuildingblocks"

# Inspect postgres volume
docker volume inspect fastapibuildingblocks_postgres-data

# Inspect pgadmin volume
docker volume inspect fastapibuildingblocks_pgadmin-data
```

### Data Persistence Guarantees
- **PostgreSQL data**: Tables, rows, indexes, sequences all persist
- **pgAdmin settings**: Server connections, saved queries, preferences persist
- **Survives**: Container restart, container removal, Docker restart
- **Destroyed only if**: Volume is explicitly deleted with `docker volume rm`

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    bio TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Indexes
- `idx_users_email` on `email` (unique)
- `idx_users_is_active` on `is_active`
- `idx_users_created_at` on `created_at` (descending)

## Common Operations

### Query Database via CLI
```bash
# Connect to PostgreSQL
docker exec -it user-management-db psql -U postgres -d user_management

# Run a query
docker exec -it user-management-db psql -U postgres -d user_management \
  -c "SELECT * FROM users;"

# Check table structure
docker exec -it user-management-db psql -U postgres -d user_management \
  -c "\d users"
```

### Backup Database
```bash
# Create backup
docker exec -t user-management-db pg_dump -U postgres user_management > backup.sql

# Restore backup
docker exec -i user-management-db psql -U postgres user_management < backup.sql
```

### Reset Database (Warning: Deletes all data)
```bash
# Stop services
docker-compose -f docker-compose.observability.yml down

# Remove postgres volume
docker volume rm fastapibuildingblocks_postgres-data

# Start services (will recreate with init.sql)
docker-compose -f docker-compose.observability.yml up -d
```

### Manage Volumes
```bash
# View volume details
docker volume inspect fastapibuildingblocks_postgres-data

# Backup volume
docker run --rm -v fastapibuildingblocks_postgres-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v fastapibuildingblocks_postgres-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

## Monitoring Database

### Check Connection
```bash
# Health check
docker exec user-management-db pg_isready -U postgres

# Active connections
docker exec -it user-management-db psql -U postgres -d user_management \
  -c "SELECT count(*) FROM pg_stat_activity WHERE datname='user_management';"
```

### Performance Queries
```bash
# Table sizes
docker exec -it user-management-db psql -U postgres -d user_management \
  -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
      FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');"

# Index usage
docker exec -it user-management-db psql -U postgres -d user_management \
  -c "SELECT schemaname, tablename, indexname, idx_scan 
      FROM pg_stat_user_indexes ORDER BY idx_scan DESC;"
```

## Troubleshooting

### pgAdmin Not Loading
```bash
# Check logs
docker logs pgadmin

# Restart pgadmin
docker restart pgadmin
```

### Can't Connect to Database from pgAdmin
- Ensure PostgreSQL container is running: `docker ps | grep postgres`
- Verify network connectivity: Both should be on `observability` network
- Check credentials in pgadmin_servers.json

### Database Connection from Application
The application connects using:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/user_management
```

Note: `postgres` is the Docker network hostname, not `localhost`

## Configuration Files

### `example_service/init.sql`
Initial database schema, executed only on first container creation

### `example_service/pgadmin_servers.json`
Pre-configured server connections for pgAdmin

### `example_service/pgpass`
Stored password file for automatic authentication

## Security Notes

**For Production**:
1. Change default passwords
2. Use secrets management (Docker secrets, Kubernetes secrets)
3. Enable SSL/TLS for PostgreSQL connections
4. Restrict pgAdmin access with proper authentication
5. Use read-only users for reporting/analytics
6. Enable audit logging
7. Configure backup strategy with retention policy

## Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/16/
- pgAdmin Documentation: https://www.pgadmin.org/docs/
- Docker Volumes: https://docs.docker.com/storage/volumes/
- SQLAlchemy AsyncPG: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.asyncpg
