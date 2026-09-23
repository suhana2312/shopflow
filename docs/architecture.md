# ShopFlow Distributed Architecture & Sequence Flows

This document details the architectural mechanisms, state machines, and sequence flows powering **ShopFlow**.

---

## 1. Concurrency Control & Row-Level Locking Sequence

When multiple users race to purchase the final available stock of a product ($stock = 1$), ShopFlow uses pessimistic row-level locking with atomic conditional updates to guarantee zero overselling.

```mermaid
sequenceDiagram
    autonumber
    actor CustomerA as Customer A (Thread 1)
    actor CustomerB as Customer B (Thread 2)
    participant API as FastAPI Checkout Service
    participant DB as PostgreSQL (ACID)
    participant Outbox as Outbox Event Table

    CustomerA->>API: POST /api/v1/checkout (Product 10, Qty 1)
    CustomerB->>API: POST /api/v1/checkout (Product 10, Qty 1)

    critical Database Transaction A
        API->>DB: BEGIN TRANSACTION A
        API->>DB: SELECT * FROM inventory WHERE product_id=10 FOR UPDATE
        Note over DB: Row for Product 10 LOCKED by Tx A.<br/>Tx B waits on lock acquisition.
        API->>DB: UPDATE inventory SET available_quantity = available_quantity - 1<br/>WHERE product_id=10 AND available_quantity >= 1
        Note over DB: Row updated: available_quantity = 0. rowcount = 1.
        API->>DB: INSERT INTO inventory_reservations (status='ACTIVE', expires_at=NOW()+15m)
        API->>DB: INSERT INTO orders (status='PENDING')
        API->>DB: INSERT INTO outbox_events (event_type='ORDER_CREATED')
        API->>DB: COMMIT TRANSACTION A
    end

    Note over DB: Lock released. Tx B acquires row lock.

    critical Database Transaction B
        API->>DB: BEGIN TRANSACTION B
        API->>DB: SELECT * FROM inventory WHERE product_id=10 FOR UPDATE
        API->>DB: UPDATE inventory SET available_quantity = available_quantity - 1<br/>WHERE product_id=10 AND available_quantity >= 1
        Note over DB: Condition available_quantity >= 1 FAILS!<br/>rowcount = 0.
        API->>DB: ROLLBACK TRANSACTION B
    end

    API-->>CustomerA: 201 Created (Order #ORD-2026-0001 confirmed)
    API-->>CustomerB: 409 Conflict (Error: OUT_OF_STOCK)
```

---

## 2. Inventory Reservation State Machine

```mermaid
stateDiagram-v2
    [*] --> AVAILABLE : Initial Product Inbound
    AVAILABLE --> RESERVED : Checkout Begun (SELECT FOR UPDATE)
    RESERVED --> SOLD : Payment Authorized (Tx Completed)
    RESERVED --> AVAILABLE : Payment Declined / User Cancelled
    RESERVED --> AVAILABLE : Reservation Expired (Celery Beat Sweeper)
    SOLD --> REFUNDED : Return Approved (Admin Action)
    REFUNDED --> AVAILABLE : Restock to Inventory
    AVAILABLE --> [*] : Delisted
```

---

## 3. Transactional Outbox Pattern & Async RabbitMQ / Celery Pipeline

To solve the dual-write problem (writing to a database while simultaneously publishing to a message broker), events are persisted directly into PostgreSQL within the same atomic ACID transaction as the order.

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant CheckoutService as Checkout Service
    participant DB as PostgreSQL
    participant Sweeper as Celery Beat (Outbox Sweeper)
    participant Broker as RabbitMQ (Exchange: orders_exchange)
    participant Worker as Celery Worker
    participant DLQ as RabbitMQ Dead-Letter Exchange (DLX)

    Customer->>CheckoutService: POST /checkout
    CheckoutService->>DB: BEGIN TX: Insert Order + Insert OutboxEvent (status='PENDING')
    CheckoutService->>DB: COMMIT TX
    CheckoutService-->>Customer: 201 Order Placed

    loop Every 5 Seconds (Celery Beat)
        Sweeper->>DB: SELECT * FROM outbox_events WHERE status='PENDING' LIMIT 100 FOR UPDATE SKIP LOCKED
        Sweeper->>Broker: Publish Message (routing_key='order.created')
        Sweeper->>DB: UPDATE outbox_events SET status='PROCESSED', processed_at=NOW()
    end

    Broker->>Worker: Consume 'order.created' message
    alt Task Executes Successfully
        Worker->>Worker: Generate Invoice & Trigger Notification
        Worker-->>Broker: ACK Message
    else Transient Error (Max 3 Retries)
        Worker->>Worker: Retry with Exponential Backoff (countdown = 2^attempt)
    else Poison Pill / Unrecoverable Error
        Worker->>DLQ: Route to 'dead_letter_queue'
        Worker-->>Broker: NACK / Reject (requeue=False)
        Note over DLQ: Monitored in Admin Dashboard for human inspection
    end
```

---

## 4. Real-Time WebSockets Order Streaming Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Client as Browser (React App)
    participant Nginx as Reverse Proxy / Gateway
    participant WSManager as WebSocket Connection Manager
    participant DB as Database / State Machine
    participant Redis as Redis Pub/Sub Backplane

    Client->>Nginx: GET /ws/orders/{order_id}?token=JWT (Upgrade: websocket)
    Nginx->>WSManager: Pass WebSocket Handshake
    WSManager->>WSManager: Verify JWT Signature & User Ownership
    WSManager-->>Client: 101 Switching Protocols + Handshake ACK

    Note over Client,WSManager: Persistent Bi-directional Channel Open

    alt Order State Transition (e.g. Admin or Payment Webhook)
        DB->>WSManager: OrderStatusService.transition_status(order_id, 'PACKED')
        WSManager->>Redis: PUBLISH channel:order:{order_id} (JSON Payload)
        Redis->>WSManager: Broadcast to local subscribers
        WSManager-->>Client: Send TextFrame: {"type": "ORDER_STATUS_UPDATED", "new_status": "PACKED"}
        Note over Client: Animated Timeline advances in real time!
    end

    Client->>WSManager: Ping / Heartbeat Frame
    WSManager-->>Client: Pong
```

---

## 5. Redis Sliding-Window Rate Limiting (Sorted Sets)

ShopFlow uses Redis sorted sets (`ZSET`) where score is timestamp in milliseconds:

1. Remove expired timestamps outside the rolling window:
   `ZREMRANGEBYSCORE key 0 (current_timestamp - window_ms)`
2. Count remaining timestamps inside the window:
   `ZCARD key`
3. If count $\ge$ allowed limit, reject with `429 Too Many Requests`.
4. Otherwise, record the request:
   `ZADD key current_timestamp unique_request_id`
   `EXPIRE key window_seconds`
