# Kafka Integration - Quick Start Guide

This guide will help you get started with Kafka integration events in just 5 minutes.

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- FastAPI Building Blocks installed

## Step 1: Start Kafka

```bash
docker-compose -f docker-compose.kafka.yml up -d
```

This starts:
- Kafka broker on `localhost:9092`
- Zookeeper on `localhost:2181`
- Kafka UI on `http://localhost:8080`
- Schema Registry on `localhost:8081`

Wait ~30 seconds for services to be ready.

## Step 2: Install Dependencies

```bash
pip install aiokafka pydantic-settings
```

Or install the full messaging extras:

```bash
pip install -e ".[messaging]"
```

## Step 3: Run the Example

```bash
python example_kafka_integration.py
```

You should see:
1. User service creating users
2. Integration events being published to Kafka
3. Multiple services consuming and processing events:
   - Email service sending welcome emails
   - CRM service syncing users
   - Analytics service tracking signups

## Step 4: View Kafka UI

Open http://localhost:8080 to see:
- Topics: `users.created`, `users.updated`
- Messages in each topic
- Consumer groups
- Real-time message flow

## What Just Happened?

1. **Commands** → Mediator handles commands
2. **Domain Events** → Created internally
3. **Event Mapping** → Automatic conversion to integration events
4. **Kafka Publishing** → Events sent to Kafka topics
5. **Consumers** → Multiple services process events independently
6. **Observability** → Full tracing and logging

This is the **Wolverine pattern** in Python! 🎉

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Service                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST /users                                                    │
│      ↓                                                          │
│  CreateUserCommand                                              │
│      ↓                                                          │
│  Mediator.send()                                                │
│      ↓                                                          │
│  CreateUserHandler                                              │
│      ↓                                                          │
│  UserCreatedDomainEvent ──→ EventMapper                         │
│                              ↓                                  │
│                         UserCreatedIntegrationEvent             │
│                              ↓                                  │
│                         KafkaProducer                           │
│                              ↓                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               ↓
                          Kafka Topic
                       (users.created)
                               ↓
        ┌──────────────────────┼──────────────────────┐
        ↓                      ↓                      ↓
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│Email Service │      │ CRM Service  │      │Analytics Svc │
├──────────────┤      ├──────────────┤      ├──────────────┤
│              │      │              │      │              │
│ Consumer     │      │ Consumer     │      │ Consumer     │
│    ↓         │      │    ↓         │      │    ↓         │
│ Handler      │      │ Handler      │      │ Handler      │
│    ↓         │      │    ↓         │      │    ↓         │
│ Send Email   │      │ Sync to CRM  │      │ Track Event  │
│              │      │              │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

## Next Steps

1. **Read the full documentation**: [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md)
2. **Customize event mappings**: Define your own domain → integration event mappings
3. **Add more handlers**: Create handlers for different event types
4. **Production setup**: Configure SASL/SSL, multiple brokers, monitoring
5. **Test thoroughly**: Write integration tests with embedded Kafka

## Common Commands

### View Kafka Topics
```bash
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Create a Topic Manually
```bash
docker exec -it kafka kafka-topics --create \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092
```

### Consume Messages (CLI)
```bash
docker exec -it kafka kafka-console-consumer \
  --topic users.created \
  --from-beginning \
  --bootstrap-server localhost:9092
```

### View Consumer Groups
```bash
docker exec -it kafka kafka-consumer-groups --list --bootstrap-server localhost:9092
```

### Check Consumer Lag
```bash
docker exec -it kafka kafka-consumer-groups \
  --describe \
  --group consumer-services-group \
  --bootstrap-server localhost:9092
```

## Troubleshooting

### Kafka not starting
```bash
# Check logs
docker-compose -f docker-compose.kafka.yml logs kafka

# Restart services
docker-compose -f docker-compose.kafka.yml restart
```

### Connection refused
- Wait 30-60 seconds after starting Kafka
- Check Kafka health: `docker ps | grep kafka`
- Verify port 9092 is not in use: `lsof -i :9092`

### Events not being consumed
- Check consumer group status
- Verify topic exists
- Check consumer logs
- Ensure consumer is subscribed to correct topics

## Configuration Examples

### Local Development
```python
config = KafkaConfig(
    bootstrap_servers="localhost:9092",
    service_name="my-service",
)
```

### Production
```python
config = KafkaConfig(
    bootstrap_servers="broker1:9092,broker2:9092,broker3:9092",
    security_protocol="SASL_SSL",
    sasl_mechanism="SCRAM-SHA-256",
    sasl_username=os.getenv("KAFKA_USERNAME"),
    sasl_password=os.getenv("KAFKA_PASSWORD"),
    ssl_cafile="/path/to/ca-cert.pem",
    producer_acks="all",
    enable_idempotence=True,
)
```

## Clean Up

```bash
# Stop all services
docker-compose -f docker-compose.kafka.yml down

# Remove volumes (deletes all data)
docker-compose -f docker-compose.kafka.yml down -v
```

## Need Help?

- 📖 Full documentation: [KAFKA_INTEGRATION.md](KAFKA_INTEGRATION.md)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/fastapi-building-blocks/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/fastapi-building-blocks/discussions)

---

**Enjoy building event-driven microservices with Kafka! 🚀**
