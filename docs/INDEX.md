# Documentation Index

Welcome to the FastAPI Building Blocks documentation. This index helps you navigate all available documentation.

## 📚 Getting Started

- **[Getting Started](GETTING_STARTED.md)** - Quick start guide and installation
- **[Contributing](CONTRIBUTING.md)** - Guidelines for contributing to the project

## 🏗️ Architecture & Patterns

### Core Patterns
- **[Mediator Pattern](MEDIATOR_PATTERN.md)** - CQRS implementation with Mediator
- **[Mediator Implementation Summary](MEDIATOR_IMPLEMENTATION_SUMMARY.md)** - Detailed implementation guide
- **[Inbox/Outbox Pattern](INBOX_OUTBOX_PATTERN.md)** - Reliable event publishing pattern
- **[Configurable Patterns Summary](CONFIGURABLE_PATTERNS_SUMMARY.md)** - Overview of configurable patterns

### Architecture Documentation
- **[Database Architecture](DATABASE_ARCHITECTURE.md)** - Database design and patterns
- **[Inbox/Outbox Configuration](INBOX_OUTBOX_CONFIG.md)** - Configuration guide for Inbox/Outbox

## 🔧 Infrastructure Components

### HTTP & External APIs
- **[HTTP Client](HTTP_CLIENT.md)** - HTTP client wrapper with auth strategies
- **[Exception Handler](EXCEPTION_HANDLER.md)** - Global exception handling with Problem Details

### Caching & Data Store
- **[Redis Cache](REDIS_CACHE.md)** - Redis caching implementation
- **[Redis API Guide](REDIS_API_GUIDE.md)** - Redis API endpoints and usage
- **[Redis UI Guide](REDIS_UI_GUIDE.md)** - RedisInsight setup and usage

### Database
- **[PostgreSQL & pgAdmin](POSTGRES_PGADMIN.md)** - PostgreSQL setup with pgAdmin

### Messaging
- **[Kafka Integration](KAFKA_INTEGRATION.md)** - Kafka integration guide
- **[Kafka Implementation Summary](KAFKA_IMPLEMENTATION_SUMMARY.md)** - Detailed Kafka implementation
- **[Kafka Quick Start](KAFKA_QUICKSTART.md)** - Quick start guide for Kafka

## 📊 Observability

- **[Observability](OBSERVABILITY.md)** - Logging, tracing, and metrics
- **[Middleware Logging](MIDDLEWARE_LOGGING.md)** - Request/response logging middleware
- **[Redaction Summary](REDACTION_SUMMARY.md)** - Sensitive data redaction

## 🚀 Deployment & Operations

- **[Deployment Summary](DEPLOYMENT_SUMMARY.md)** - Deployment guidelines and best practices
- **[Docker Guide](DOCKER_GUIDE.md)** - Docker and docker-compose setup
- **[Running Services](RUNNING_SERVICES.md)** - Guide to running all services

## 📦 Release Information

- **[Release Summary](RELEASE_SUMMARY.md)** - Latest release notes and changes

## 🎯 Quick Reference

### By Use Case

**Setting Up Your Project**
1. [Getting Started](GETTING_STARTED.md)
2. [Docker Guide](DOCKER_GUIDE.md)
3. [Database Architecture](DATABASE_ARCHITECTURE.md)

**Implementing Business Logic**
1. [Mediator Pattern](MEDIATOR_PATTERN.md)
2. [Inbox/Outbox Pattern](INBOX_OUTBOX_PATTERN.md)
3. [Database Architecture](DATABASE_ARCHITECTURE.md)

**Integrating External Services**
1. [HTTP Client](HTTP_CLIENT.md)
2. [Kafka Integration](KAFKA_INTEGRATION.md)

**Adding Caching**
1. [Redis Cache](REDIS_CACHE.md)
2. [Redis API Guide](REDIS_API_GUIDE.md)

**Monitoring & Debugging**
1. [Observability](OBSERVABILITY.md)
2. [Middleware Logging](MIDDLEWARE_LOGGING.md)
3. [Redis UI Guide](REDIS_UI_GUIDE.md)

**Deploying Your Application**
1. [Deployment Summary](DEPLOYMENT_SUMMARY.md)
2. [Docker Guide](DOCKER_GUIDE.md)
3. [Running Services](RUNNING_SERVICES.md)

## 🤖 AI Assistance

For AI-assisted development, see:
- **`.cursorrules`** (root) - Comprehensive AI coding rules for Cursor/Claude
- **`.clinerules`** (root) - Quick reference for Cline and other AI assistants

## 📖 Additional Resources

### Code Examples
- **`/examples/`** - Demo scripts and integration tests
- **`/example_service/`** - Complete reference implementation

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs (when service is running)
- **ReDoc**: http://localhost:8000/redoc (when service is running)

### Testing
- **`/tests/`** - Unit tests for building blocks
- **`/examples/`** - Integration tests
- **`/example_service/tests/`** - Service-specific tests

## 📝 Documentation Standards

All documentation follows these principles:
- **Clear structure** with table of contents
- **Code examples** for all features
- **Step-by-step guides** for complex topics
- **Troubleshooting sections** for common issues
- **Links to related documentation**

## 🔍 Search Tips

To find specific information:
1. **Use your editor's search** across all markdown files
2. **Check this index** for topic organization
3. **Look at code examples** in `/examples/`
4. **Review reference implementation** in `/example_service/`

## 🆘 Getting Help

If you can't find what you're looking for:
1. Check the [Getting Started](GETTING_STARTED.md) guide
2. Review the [Contributing](CONTRIBUTING.md) guidelines
3. Look at the example service implementation
4. Check the AI rules files for patterns

## 📜 Document Categories

### 📘 Guides (Step-by-step instructions)
- Getting Started
- Kafka Quick Start
- Docker Guide
- Contributing

### 📙 References (Detailed specifications)
- HTTP Client
- Redis API Guide
- Database Architecture
- Mediator Pattern

### 📗 Summaries (High-level overviews)
- Release Summary
- Deployment Summary
- Implementation Summaries

### 📕 Configurations (Setup instructions)
- Inbox/Outbox Configuration
- Running Services
- Redis UI Guide

---

**Last Updated**: February 14, 2026

**Note**: This documentation is continuously updated. Check git history for recent changes.
