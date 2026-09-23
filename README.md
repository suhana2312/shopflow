# ShopFlow: Real-Time E-Commerce Order & Inventory Management Engine

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.0-dc382d.svg)](https://redis.io)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-ff6600.svg)](https://www.rabbitmq.com)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814a.svg)](https://docs.celeryq.dev)
[![React](https://img.shields.io/badge/React-18%20%7C%2019-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x%20%7C%206.x-3178c6.svg)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-8.x-646cff.svg)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38bdf8.svg)](https://tailwindcss.com)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-2ea44f?style=for-the-badge&logo=github)](https://suhana2312.github.io/shopflow/)
[![GitHub Repo](https://img.shields.io/badge/Repository-suhana2312%2Fshopflow-blue?style=for-the-badge&logo=github)](https://github.com/suhana2312/shopflow)

> 🚀 **Live Interactive Demo**: Access the running system directly in your browser without local installation at **[https://suhana2312.github.io/shopflow/](https://suhana2312.github.io/shopflow/)**

**ShopFlow** is a production-style, portfolio-grade distributed e-commerce backend and real-time frontend platform engineered to handle **high-concurrency flash sales, atomic inventory reservations, asynchronous message-driven order fulfillment, and real-time state streaming**.

This project solves fundamental distributed systems challenges:
* **Zero-Overselling Concurrency**: Strict mathematical prevention of overselling when 500 requests compete for 1 remaining stock unit via database row-level locking (`SELECT ... FOR UPDATE`) paired with atomic conditional decrement (`WHERE available_quantity >= qty`).
* **Inventory Reservation State Machine**: Full lifecycle management (`AVAILABLE` &rarr; `RESERVED` &rarr; `SOLD` / `EXPIRED` / `CANCELLED`).
* **Transactional Outbox Pattern**: Elimination of dual-write discrepancies by persisting domain events within the primary ACID order transaction before dispatching to RabbitMQ.
* **Resilient Async Processing & DLQ**: Celery worker clusters with exponential backoff retries and Dead-Letter Exchanges (DLX) for poison-pill isolation.
* **Real-Time WebSocket Streaming**: Stateful bi-directional channels (`/ws/orders/{id}`) with JWT token handshake and strict ownership authorization.
* **Cache-Aside & Sliding-Window Rate Limiting**: Sub-millisecond Redis caching with deterministic invalidation and sorted-set sliding-window traffic throttling.
* **Multi-Signal AI Recommendation Engine**: Collaborative filtering and behavioral affinity scoring.

---

## 🏗️ System Architecture

```
                                      [ Browser Client / React 18 SPA ]
                                                      |
                                                      v
                                        +----------------------------+
                                        |   Nginx Reverse Proxy /    |
                                        |    Vite Dev Server (5173)  |
                                        +--------------+-------------+
                                                       |
                             +-------------------------+-------------------------+
                             | (REST API /api/v1)                                | (WebSockets /ws/orders)
                             v                                                   v
          +-------------------------------------------------------------------------------+
          |                        FastAPI Application Cluster                            |
          |  * Sliding-Window Rate Limiter (Redis ZSET)  * JWT Auth & Role Guard          |
          |  * Row-Locked Inventory Engine               * Centralized Order State Machine|
          +-------------------+--------------------+--------------------+-----------------+
                              |                    |                    |
                              v                    v                    v
                      +---------------+    +---------------+    +---------------+
                      |  PostgreSQL   |    | Redis Cluster |    |   RabbitMQ    |
                      |  (Master DB)  |    | Cache & Lock  |    | Message Broker|
                      +-------+-------+    +---------------+    +-------+-------+
                              |                                         |
                              v                                         v
                      +---------------+                         +---------------+
                      | Outbox Events | <--- Celery Beat Sweep -+ Celery Worker |
                      +---------------+                         | + DLQ Handler |
                                                                +---------------+
```

---

## 🔒 Concurrency Deep-Dive: Zero-Overselling Guarantee

### The Race Condition Problem
During flash sales, multiple checkout requests query available stock simultaneously. In a naive implementation:
1. Thread A reads: `stock = 1`
2. Thread B reads: `stock = 1`
3. Thread A saves: `stock = 0`, creates Order 1
4. Thread B saves: `stock = 0`, creates Order 2 (Oversold!)

### ShopFlow's Dual-Layer Concurrency Defense
ShopFlow implements two synchronized barriers inside `app/services/inventory_service.py`:

```python
# 1. Pessimistic Row-Level Lock: Blocks competing threads at the DB row level
inventory = db.execute(
    select(Inventory)
    .where(Inventory.product_id == product_id)
    .with_for_update()
).scalar_one_or_none()

# 2. Atomic Conditional Update: Guarantees atomicity even under non-locking engines
result = db.execute(
    update(Inventory)
    .where(
        Inventory.product_id == product_id,
        Inventory.available_quantity >= quantity  # Atomic predicate check
    )
    .values(
        available_quantity=Inventory.available_quantity - quantity,
        reserved_quantity=Inventory.reserved_quantity + quantity,
        version=Inventory.version + 1,
    )
)

if result.rowcount == 0:
    # Insufficient stock detected inside the lock manager
    raise InsufficientStockException(f"Insufficient stock for product {product_id}")
```

### Verification Test
Run the automated multi-threaded concurrency race test:
```powershell
backend\.venv\Scripts\pytest -k "test_concurrent_checkout_prevents_overselling" -v
```
**Result**: 2 simultaneous threads racing for a single unit of stock. Exactly **one** gets `201 Created`, the other gets `409 Conflict (OUT_OF_STOCK)`. Physical inventory reflects exactly 0 available units.

---

## 📊 Inventory Reservation State Machine

```
   [Inbound] ──> AVAILABLE ──(Checkout Started)──> RESERVED ──(Payment Success)──> SOLD
                    ^                                  │
                    │───(Declined / Cancelled)─────────┤
                    │───(Expired via Celery Beat)──────┘
```

* **Active TTL**: By default, inventory reservations expire after 15 minutes.
* **Celery Beat Sweeper**: `sweep_expired_reservations` runs periodically, identifying expired active reservations with `SELECT ... FOR UPDATE`, restoring `available_quantity`, and marking status `EXPIRED`.

---

## 🔄 Transactional Outbox Pattern

To eliminate the **Dual-Write Problem** where an order is placed in SQL but the RabbitMQ message fails to publish:
1. Every order creation appends an `OutboxEvent` row inside the **exact same ACID commit**.
2. A lightweight Celery Beat sweeper queries pending outbox events using `SELECT ... FOR UPDATE SKIP LOCKED` to allow horizontal concurrency without contention.
3. Once RabbitMQ acknowledges the message (`ACK`), the outbox event status is updated to `PROCESSED`.
4. If a message is rejected 3 times, RabbitMQ routes it to the **Dead-Letter Exchange (DLX)** for inspection in the Admin Portal.

---

## ⚡ Real-Time WebSockets Engine

* Endpoint: `/ws/orders/{order_id}?token={jwt_token}`
* Features:
  * Handshake validates user ownership or admin privileges before granting connection.
  * Connected clients receive instant push payloads whenever the order changes:
    ```json
    {
      "type": "ORDER_STATUS_UPDATED",
      "payload": {
        "order_id": 1,
        "previous_status": "CONFIRMED",
        "new_status": "PACKED",
        "timestamp": "2026-09-23T10:30:00Z"
      }
    }
    ```
  * Frontend animated stepper transitions live without page refreshes.

---

## 🤖 AI-Powered Recommendation Engine

Located in `app/services/recommendation_service.py`:
* Evaluates cross-product catalog signals:
  1. **Category Affinity**: Matches high-relevance items within the same category taxonomy.
  2. **Price Proximity Scoring**: Recommends items within a complementary price bracket ($\pm 40\%$).
  3. **Trending Inventory Velocity**: Weights items with active reservations and recent purchase velocity.
* Exposed via `/api/v1/recommendations/?product_id={id}&limit=4`.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.11+
* Node.js 20+ & npm
* (Optional) Docker & Docker Compose

### 2. Backend Setup
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed initial catalog, users, and flash-sale product (Stock = 1)
python -m app.db.seed

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 🐳 Docker Compose (Full Stack)

Launch the complete ecosystem (PostgreSQL 16, Redis 7, RabbitMQ 3.12, FastAPI backend, Celery worker, Celery beat, and Nginx React frontend):

```powershell
docker-compose up --build
```
* **Frontend**: `http://localhost:3000`
* **FastAPI Docs (Swagger UI)**: `http://localhost:8000/docs`
* **RabbitMQ Management UI**: `http://localhost:15672` (User: `shopflow`, Pass: `shopflow_secret`)

---

## 👥 Seed Accounts & Demo Credentials

| Role | Email | Password | Access |
|---|---|---|---|
| **System Admin** | `admin@shopflow.io` | `AdminPassword123!` | Full Admin Portal, Inventory Adjustment, DLQ & Audit Logs |
| **Customer 1** | `customer@shopflow.io` | `CustomerPassword123!` | Catalog, Shopping Cart, Atomic Checkout, Orders |
| **Customer 2** | `customer2@shopflow.io` | `CustomerPassword123!` | Secondary customer for multi-browser race condition testing |

*(One-click demo login buttons are also provided directly on the UI!)*

---

## 🧪 Automated Test Suite

ShopFlow includes an exhaustive automated test suite covering unit tests, integration workflows, idempotency verification, and multi-threaded race conditions:

```powershell
cd backend
.\.venv\Scripts\pytest -v
```

### Passing Tests Overview:
* `tests/test_auth.py`: Registration, login, JWT rotation, and profile queries.
* `tests/test_products.py`: Redis cache hits, pagination, category filtering.
* `tests/test_cart.py`: Cart item additions, quantity limits, and clears.
* `tests/test_checkout_and_orders.py`: Order generation and reservation state transitions.
* `tests/test_payment.py`: Payment simulation (success, insufficient funds, timeouts).
* `tests/test_failure_scenarios.py`: Idempotency keys, duplicate charge prevention, invalid order status transitions.
* `tests/test_concurrency.py`: **Multi-threaded checkout race condition testing on stock = 1.**

---

## ☁️ AWS Cloud Readiness Architecture

To scale ShopFlow to **1,000,000+ daily active users**:

1. **CDN & Edge**: Amazon CloudFront distribution serving static Vite build assets from an S3 bucket with TLS 1.3 termination and gzip/brotli compression.
2. **Compute**: AWS ECS Fargate or EKS running containerized FastAPI API tasks with autoscaling based on CPU and request latency metrics.
3. **Database**: Amazon RDS Aurora PostgreSQL (Multi-AZ) with **PgBouncer** / AWS RDS Proxy connection pooling for high-concurrency connection multiplexing. Read Replicas offload catalog browsing.
4. **Caching & Redis**: Amazon ElastiCache for Redis in Cluster Mode with in-memory replication.
5. **Message Broker**: Amazon MQ for RabbitMQ with multi-AZ broker replication.
6. **Telemetry**: AWS CloudWatch container insights + Prometheus `/metrics` scraping and OpenTelemetry distributed tracing.

---

## 💼 Portfolio & Resume Highlights

* **High-Concurrency Systems**: Architected and verified an atomic row-locking inventory reservation engine in FastAPI and PostgreSQL that mathematically eliminates overselling under concurrent load.
* **Distributed Reliability**: Implemented the Transactional Outbox Pattern with RabbitMQ and Celery, guaranteeing at-least-once event delivery while preventing dual-write inconsistencies.
* **Resilient Failure Handling**: Designed a Dead-Letter Exchange (DLX) pipeline with exponential backoff retries and idempotent request deduplication via `Idempotency-Key` headers.
* **Real-Time Architecture**: Built an authenticated WebSocket streaming channel (`/ws/orders/{id}`) enabling zero-polling order lifecycle updates.
* **Modern Frontend**: Developed a React 18 + TypeScript + Vite + Tailwind CSS single-page application featuring responsive catalog filtering, order tracking timeline, and administrative control centers.
