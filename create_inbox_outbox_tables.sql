-- Create outbox table for transactional outbox pattern
CREATE TABLE IF NOT EXISTS outbox_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) NOT NULL DEFAULT '1.0',
    topic VARCHAR(255) NOT NULL,
    partition_key VARCHAR(255),
    payload TEXT NOT NULL,
    headers TEXT,
    correlation_id UUID,
    causation_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    published_at TIMESTAMP,
    locked_until TIMESTAMP,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    source_service VARCHAR(255),
    aggregate_id UUID
);

CREATE INDEX IF NOT EXISTS ix_outbox_event_id ON outbox_messages(event_id);
CREATE INDEX IF NOT EXISTS ix_outbox_status ON outbox_messages(status);
CREATE INDEX IF NOT EXISTS ix_outbox_status_created ON outbox_messages(status, created_at);

-- Create inbox table for exactly-once consumer pattern
CREATE TABLE IF NOT EXISTS inbox_messages (
    message_id UUID PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) NOT NULL DEFAULT '1.0',
    topic VARCHAR(255) NOT NULL,
    partition VARCHAR(50) NOT NULL,
    "offset" VARCHAR(50) NOT NULL,
    correlation_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    received_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP,
    locked_until TIMESTAMP,
    attempt_count VARCHAR(50) NOT NULL DEFAULT '0',
    last_error TEXT,
    handler_name VARCHAR(255),
    payload TEXT
);

CREATE INDEX IF NOT EXISTS ix_inbox_event_type ON inbox_messages(event_type);
CREATE INDEX IF NOT EXISTS ix_inbox_topic ON inbox_messages(topic);
CREATE INDEX IF NOT EXISTS ix_inbox_correlation_id ON inbox_messages(correlation_id);
CREATE INDEX IF NOT EXISTS ix_inbox_status ON inbox_messages(status);
CREATE INDEX IF NOT EXISTS ix_inbox_received_at ON inbox_messages(received_at);
CREATE INDEX IF NOT EXISTS ix_inbox_locked_until ON inbox_messages(locked_until);
CREATE INDEX IF NOT EXISTS ix_inbox_status_received ON inbox_messages(status, received_at);
CREATE INDEX IF NOT EXISTS ix_inbox_topic_partition_offset ON inbox_messages(topic, partition, "offset");
