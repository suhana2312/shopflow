# ShopFlow: Senior Engineering Interview Guide & System Design Q&A

This document serves as an exhaustive, portfolio-grade technical cheat sheet and interview prep guide based on the architectural decisions implemented in **ShopFlow**.

---

## 1. Concurrency Control & Database Locking

### Q1: How does ShopFlow guarantee zero overselling during a high-concurrency flash sale (e.g., 500 requests racing for stock = 1)?
**Answer:**
ShopFlow uses a **defense-in-depth concurrency model**:
1. **Pessimistic Row-Level Locking (`SELECT ... FOR UPDATE`)**:
   During the checkout transaction, the inventory row corresponding to the requested product is selected with `SELECT ... FOR UPDATE`. In PostgreSQL, this places an exclusive row-level lock (`RowExclusiveLock`) on that specific row. Any competing transaction attempting to read or lock the same row will block until the first transaction commits or rolls back.
2. **Atomic Conditional Decrement**:
   Even if the database engine does not strictly enforce row locks (e.g., during SQLite development/testing), the decrement query contains an atomic condition:
   ```sql
   UPDATE inventory
   SET available_quantity = available_quantity - :qty,
       reserved_quantity = reserved_quantity + :qty,
       version = version + 1
   WHERE product_id = :product_id AND available_quantity >= :qty;
   ```
   The database engine atomically checks `available_quantity >= :qty` inside its lock manager. If another transaction has already reduced stock to `0`, `rowcount` returns `0`. ShopFlow detects `rowcount == 0`, immediately rolls back the transaction, and returns an HTTP `409 Conflict` (`OUT_OF_STOCK`).

### Q2: What is the difference between Optimistic Concurrency Control (OCC) and Pessimistic Concurrency Control (PCC)? When would you choose OCC vs. PCC?
**Answer:**
* **Optimistic Concurrency Control (OCC)**:
  Assumes collisions are rare. Each row contains a `version` column. Updates verify `WHERE id = :id AND version = :current_version`. If a conflict occurs, the transaction fails and the client must retry.
  * *Best for*: Read-heavy workloads with low write contention (e.g., user profile updates, editing wiki articles).
* **Pessimistic Concurrency Control (PCC)**:
  Assumes collisions are frequent. Locks the resource (`SELECT ... FOR UPDATE`) upfront for the duration of the transaction.
  * *Best for*: Write-heavy, high-contention flash sales. In a flash sale where 1,000 users race for 1 unit, OCC would cause 999 retries with high CPU thrashing and cascade database locks, whereas PCC serializes the queue cleanly and fails fast.

### Q3: How do you prevent database deadlocks when an order contains multiple products?
**Answer:**
When an order contains multiple items (e.g., Product A and Product B), two concurrent transactions locking the items in opposite order can cause a circular wait deadlock:
* Tx 1: Locks A, waits for B
* Tx 2: Locks B, waits for A
* **Solution**: Sort the product IDs deterministically before acquiring locks:
  ```python
  sorted_product_ids = sorted([item.product_id for item in order_items])
  # Acquire locks strictly in ascending ID order
  for pid in sorted_product_ids:
      db.execute(select(Inventory).where(Inventory.product_id == pid).with_for_update())
  ```
  Because all transactions acquire locks in identical numerical order, circular wait is mathematically impossible.

---

## 2. Distributed Transactions, Outbox, and Messaging

### Q4: What is the Dual-Write Problem, and how does the Transactional Outbox Pattern solve it?
**Answer:**
* **The Problem**: If an application writes to a database (`db.commit()`) and then publishes an event to RabbitMQ/Kafka (`publisher.publish()`), network or server crashes between the two calls create inconsistent state. If the message fails to publish, the event is lost forever. If you publish before the commit, and the commit fails, external microservices act on phantom data.
* **The Outbox Solution**:
  1. An `outbox_events` table is created in the primary PostgreSQL database.
  2. Inside the exact same ACID database transaction that creates the `Order` and updates `Inventory`, an `OutboxEvent` row is inserted with status `PENDING`.
  3. Because both operations occur within the same database commit, atomicity is guaranteed: either both are saved, or neither is.
  4. An asynchronous background process (Celery Beat sweeper) reads `PENDING` events using `SELECT ... FOR UPDATE SKIP LOCKED`, pushes them to RabbitMQ, and marks them `PROCESSED`.

### Q5: Why use RabbitMQ + Celery instead of FastAPI background tasks (`asyncio.create_task`)?
**Answer:**
* `asyncio.create_task` or FastAPI `BackgroundTasks` run within the memory space of the Uvicorn web process.
* **Drawbacks of in-memory background tasks**:
  1. *Data Loss on Crash/Restart*: If a container crashes, restarts, or deploys a new revision, all pending tasks are permanently lost.
  2. *Resource Contention*: Heavy tasks (image processing, PDF invoice compilation, PDF hashing) block the Python event loop and starve HTTP request handling.
  3. *No Distributed Retries*: No native dead-letter queues, backoff policies, or cluster-wide visibility.
* RabbitMQ provides durable, persistent message storage decoupled across dedicated Celery worker clusters with automatic acknowledgements (ACKs) and rate-governed worker pooling.

### Q6: What is a Dead-Letter Queue (DLQ), and how is it configured in ShopFlow?
**Answer:**
* When a worker encounters an error during message consumption, it retries with exponential backoff (e.g., retry 1: 2s, retry 2: 4s, retry 3: 8s).
* If all retries are exhausted (e.g., corrupted JSON payload or unrecoverable third-party downstream outage), the message becomes a "poison pill". Continually re-queueing it would crash workers in an infinite loop.
* **ShopFlow DLQ Architecture**:
  * RabbitMQ queue arguments include `x-dead-letter-exchange: dlx_exchange` and `x-dead-letter-routing-key: dlq_key`.
  * After `max_retries=3`, the Celery worker rejects the message with `requeue=False`.
  * RabbitMQ automatically routes the rejected message to the Dead-Letter Queue (`dead_letter_queue`).
  * The ShopFlow Admin Dashboard exposes this queue via `/api/v1/admin/dlq` for SRE inspection, alerting, and manual re-driving.

---

## 3. Caching & Rate Limiting

### Q7: Explain the Cache-Aside pattern used for Product & Category lookups. How do you prevent stale data?
**Answer:**
1. **Read Path**:
   * App checks Redis (`GET product:{id}`).
   * If cache hit $\rightarrow$ deserialize JSON and return instantly ($<2\text{ms}$).
   * If cache miss $\rightarrow$ query PostgreSQL, write to Redis with a TTL (e.g., 300 seconds), and return.
2. **Write Invalidation Path**:
   * When an Admin updates product details or stock, or when an inventory reservation completes, the application proactively executes `DELETE product:{id}` and `DELETE products:list:*`.
   * The next read experiences a fresh database query, repopulating the cache with zero stale reads.

### Q8: How does the Sliding-Window Rate Limiter work in Redis using Sorted Sets (`ZSET`)?
**Answer:**
Fixed-window rate limiters suffer from the **boundary burst problem**: a user can make 100 requests at 00:59 and 100 requests at 01:01, effectively executing 200 requests within a 2-second span.
ShopFlow implements a true **Sliding Window Log** using Redis Sorted Sets:
1. Every incoming request generates a timestamp $T_{\text{now}}$ in milliseconds and a unique UUID.
2. **Purge**: Remove all entries older than the window:
   `ZREMRANGEBYSCORE key 0 (T_now - window_size_ms)`
3. **Count**: Retrieve current count in the active window:
   `count = ZCARD key`
4. **Evaluate**: If $count \ge limit$, reject with `429 Too Many Requests`.
5. **Log**: Otherwise, insert the current request:
   `ZADD key T_now unique_id`
   `EXPIRE key window_size_seconds`
All 4 operations are wrapped in an atomic Redis pipeline.

---

## 4. WebSockets & Real-Time Stateful Connections

### Q9: How do you authenticate and secure WebSocket endpoints?
**Answer:**
Unlike HTTP requests, the browser `WebSocket` constructor does not allow custom headers like `Authorization: Bearer <token>`.
* **ShopFlow Implementation**:
  1. The client passes the JWT access token in the query string: `ws://domain/ws/orders/{id}?token=<jwt>`.
  2. The FastAPI WebSocket endpoint interceptor immediately validates the JWT signature and expiration.
  3. **Strict Ownership Check**: The claims in the decoded token are cross-referenced with `order.user_id`. If the requesting user does not own the order and is not an Admin, the socket closes immediately with code `4003 Forbidden`.
  4. Once validated, the connection is admitted into memory.

### Q10: How do you scale WebSockets horizontally across multiple servers?
**Answer:**
WebSocket connections are persistent, stateful TCP sockets held by a specific server instance. If Server 1 holds User A's connection, but the Order Status Update is processed by a Celery worker communicating with Server 2, Server 2 cannot directly message User A.
* **Solution: Redis Pub/Sub Backplane**:
  * Each server instance subscribes to a shared Redis Pub/Sub channel pattern (e.g. `order:events:*`).
  * When any worker or server changes an order's status, it publishes the update to Redis (`PUBLISH order:events:123 payload`).
  * All running API server nodes receive the broadcast; whichever node owns the local socket for `order_id=123` relays the message down the client's TCP connection.

---

## 5. Scaling to 1,000,000 Active Users

### Q11: How would you architect ShopFlow for 1,000,000 Daily Active Users (DAU) and 20,000 Requests/sec?
**Answer:**
1. **Edge & CDN**:
   * CloudFront / Cloudflare terminates TLS and serves static Vite React assets from S3 with global edge caching.
   * Route53 with latency-based routing.
2. **API & Microservices**:
   * AWS ECS Fargate or EKS running multiple stateless FastAPI pods behind an Application Load Balancer (ALB).
   * Autoscaling based on CPU (70%) and target request count per target.
3. **Database Tier (PostgreSQL)**:
   * AWS Aurora PostgreSQL with multi-AZ replication.
   * Read-Write splitting: Master handles checkout transactions and inventory row locks; multiple Read Replicas serve catalog browsing, search queries, and historical reporting.
   * Connection pooling via **PgBouncer** or **AWS RDS Proxy** to multiplex 10,000+ client connections down to 100 database backend connections, avoiding PostgreSQL per-connection RAM overhead.
4. **Caching & Broker Tier**:
   * Redis Cluster (ElastiCache) with cluster sharding and read replicas for sub-millisecond cache-aside catalog queries.
   * Amazon MQ (RabbitMQ cluster) across multiple Availability Zones for durable message delivery.
5. **Inventory Sharding**:
   * For extreme flash sales (e.g. 100,000 orders/sec on a single SKU), row-locking a single PostgreSQL row causes lock queue saturation.
   * *Solution*: Partition the inventory into $N$ buckets (e.g., 10 inventory sub-rows each holding 10 units for 100 total units). Requests randomly select a bucket to reserve stock, distributing lock contention by a factor of $N$.
