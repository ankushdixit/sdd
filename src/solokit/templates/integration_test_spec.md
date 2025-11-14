# Integration Test: [Name]

<!--
TEMPLATE INSTRUCTIONS:
- Replace [Name] with a descriptive name for the integration test
- Define all components and their integration points
- Include sequence diagrams using mermaid for complex flows
- Specify performance benchmarks and acceptance criteria
- Document all test scenarios with setup, actions, and expected results
- Remove these instructions before finalizing the spec
-->

## Scope

<!-- Define which components are being integrated and tested -->

Define which components are being integrated and tested.

**Example:**

> This integration test validates the end-to-end order processing flow, including the Order API, Payment Service, Inventory Service, and Notification Service. It tests the happy path, error scenarios, and ensures data consistency across all services.

**Components:**

- Order API: `v2.3.0` (receives order requests, orchestrates workflow)
- Payment Service: `v1.8.2` (processes payments via Stripe)
- Inventory Service: `v2.1.0` (checks and reserves inventory)
- Notification Service: `v1.5.0` (sends email confirmations)
- Database: PostgreSQL `14.2` (order and inventory data)
- Message Queue: RabbitMQ `3.11` (async communication)

**Integration Points:**

- REST API: Order API → Payment Service (`POST /api/payments`)
- REST API: Order API → Inventory Service (`POST /api/inventory/reserve`)
- Message Queue: Order API → Notification Service (queue: `order.completed`)
- Database: All services → PostgreSQL (shared database)
- External API: Payment Service → Stripe API

## Test Scenarios

<!-- Document all test scenarios with sequence diagrams, setup, actions, and expected results -->

### Scenario 1: Successful Order Processing (Happy Path)

**Description:**

> Customer places an order for an in-stock item. Payment is processed successfully, inventory is reserved, and confirmation email is sent.

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Client
    participant OrderAPI
    participant PaymentService
    participant InventoryService
    participant NotificationQueue
    participant Database

    Client->>OrderAPI: POST /api/orders (order data)
    OrderAPI->>Database: Create order record (status: pending)
    OrderAPI->>InventoryService: POST /api/inventory/reserve
    InventoryService->>Database: Check stock availability
    Database-->>InventoryService: Stock available
    InventoryService->>Database: Reserve inventory
    InventoryService-->>OrderAPI: 200 OK (reservation_id)
    OrderAPI->>PaymentService: POST /api/payments
    PaymentService->>Stripe: Process payment
    Stripe-->>PaymentService: Payment successful
    PaymentService->>Database: Record payment
    PaymentService-->>OrderAPI: 200 OK (payment_id)
    OrderAPI->>Database: Update order (status: completed)
    OrderAPI->>NotificationQueue: Publish order.completed event
    OrderAPI-->>Client: 201 Created (order_id, status)
    NotificationQueue->>NotificationService: Consume event
    NotificationService->>SMTP: Send confirmation email
```

**Setup:**

- All services running (Order API on 8001, Payment on 8002, Inventory on 8003, Notification on 8004)
- PostgreSQL database seeded with test data:
  - Product ID `prod_123` with stock quantity 50
  - Customer ID `cust_456` with valid email
- RabbitMQ running on port 5672
- Stripe test mode enabled with test API key
- Mock SMTP server running

**Actions:**

1. Send POST request to `/api/orders` with payload:

```json
{
  "customer_id": "cust_456",
  "items": [{ "product_id": "prod_123", "quantity": 2 }],
  "payment_method": "card",
  "card_token": "tok_visa_test"
}
```

2. Wait for order processing (max 5 seconds)
3. Check order status via `GET /api/orders/{order_id}`
4. Verify email sent via SMTP mock

**Expected Results:**

- HTTP 201 response with order details:

```json
{
  "order_id": "ord_789",
  "status": "completed",
  "total": 49.98,
  "payment_id": "pay_123",
  "reservation_id": "res_456"
}
```

- Database state:
  - Order record created with status `completed`
  - Payment record created
  - Inventory reduced by 2 (from 50 to 48)
- Notification sent:
  - Email queued in RabbitMQ
  - Email delivered via SMTP mock
  - Email contains order ID and confirmation details
- Logs show successful processing in all services
- Response time < 2000ms (p95)

### Scenario 2: Insufficient Inventory (Error Handling)

**Description:**

> Customer attempts to order more items than available in stock. Order should fail gracefully without charging payment or corrupting data.

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant Client
    participant OrderAPI
    participant InventoryService
    participant Database

    Client->>OrderAPI: POST /api/orders (quantity > stock)
    OrderAPI->>Database: Create order record (status: pending)
    OrderAPI->>InventoryService: POST /api/inventory/reserve
    InventoryService->>Database: Check stock availability
    Database-->>InventoryService: Insufficient stock
    InventoryService-->>OrderAPI: 409 Conflict (insufficient_stock)
    OrderAPI->>Database: Update order (status: failed)
    OrderAPI-->>Client: 409 Conflict (error details)
```

**Setup:**

- Product ID `prod_789` with stock quantity 5
- Customer requests quantity 10

**Actions:**

1. Send POST request with `quantity: 10` for product with stock 5
2. Observe order creation and inventory check

**Expected Results:**

- HTTP 409 Conflict response:

```json
{
  "error": "insufficient_stock",
  "message": "Requested quantity (10) exceeds available stock (5)",
  "product_id": "prod_789",
  "available": 5,
  "requested": 10
}
```

- Database state:
  - Order record created with status `failed`
  - Inventory unchanged (still 5)
  - No payment record created
- No email sent
- Logs contain error with context

## Performance Benchmarks

<!-- Define quantitative performance requirements for the integration -->

**Response Time Requirements:**

- p50 (median): < 500ms
- p95: < 2000ms
- p99: < 5000ms
- p99.9: < 10000ms

**Example:** Order processing should complete within 2 seconds for 95% of requests under normal load.

**Throughput Requirements:**

- Minimum: 50 orders/minute (baseline for production)
- Target: 200 orders/minute (target for peak traffic)
- Maximum tested: 500 orders/minute (stress test)

**Resource Limits:**

- CPU: < 70% utilization per service (average under load)
- Memory: < 1GB per service (Order API, Payment, Inventory, Notification)
- Database connections: < 50 active connections
- Message queue depth: < 1000 messages
- Disk I/O: < 50MB/s

**Load Test Configuration:**

```yaml
load_test:
  ramp_up: 5 minutes # Gradually increase load
  sustained: 15 minutes # Maintain peak load
  ramp_down: 5 minutes # Gradually decrease load
  scenarios:
    - name: "happy_path"
      weight: 80% # 80% of requests are successful orders
    - name: "insufficient_stock"
      weight: 15% # 15% fail due to stock issues
    - name: "payment_failure"
      weight: 5% # 5% fail due to payment issues
```

**Acceptance Criteria:**

- [ ] p95 response time < 2000ms under 200 orders/minute
- [ ] No errors under sustained load for 15 minutes
- [ ] All services recover gracefully after spike (500 orders/minute for 1 minute)
- [ ] No memory leaks detected (memory stable over 15 minute test)
- [ ] Database connection pool doesn't exhaust

## API Contracts

<!-- Document all API contracts between services to ensure compatibility -->

**Order API → Payment Service:**

- Contract file: `contracts/order-to-payment.yaml`
- Version: 2.1.0
- Breaking changes: None allowed without major version bump
- Example request:

```json
POST /api/payments
{
  "order_id": "ord_789",
  "amount": 49.98,
  "currency": "USD",
  "payment_method": "card",
  "card_token": "tok_visa_test"
}
```

- Example response:

```json
{
  "payment_id": "pay_123",
  "status": "succeeded",
  "amount_captured": 49.98
}
```

**Order API → Inventory Service:**

- Contract file: `contracts/order-to-inventory.yaml`
- Version: 1.8.0
- Example request:

```json
POST /api/inventory/reserve
{
  "product_id": "prod_123",
  "quantity": 2,
  "order_id": "ord_789"
}
```

**Database Schema:**

- Schema file: `schemas/integration_test_schema.sql`
- Tables: `orders`, `payments`, `inventory_reservations`, `notifications`
- Migrations: `migrations/014_add_order_processing.sql`

## Environment Requirements

<!-- List all services, configuration, and infrastructure needed to run the integration tests -->

**Services Required:**

- order-api:2.3.0 (port 8001)
- payment-service:1.8.2 (port 8002)
- inventory-service:2.1.0 (port 8003)
- notification-service:1.5.0 (port 8004)
- postgres:14.2 (port 5432)
- rabbitmq:3.11 (ports 5672, 15672)
- smtp-mock:latest (port 1025) - for email testing

**Configuration:**

- Environment: `integration-test`
- Config files: `config/integration-test/*.yaml`
- Environment variables loaded from `.env.integration-test`:

```bash
DATABASE_URL=postgresql://test:test@localhost:5432/integration_test
RABBITMQ_URL=amqp://guest:guest@localhost:5672
STRIPE_API_KEY=sk_test_xxxxx
SMTP_HOST=localhost
SMTP_PORT=1025
LOG_LEVEL=debug
```

**Infrastructure:**

- Docker Compose file: `docker-compose.integration-test.yml`

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:14.2
    environment:
      POSTGRES_DB: integration_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5432:5432"

  rabbitmq:
    image: rabbitmq:3.11-management
    ports:
      - "5672:5672"
      - "15672:15672"

  # ... other services
```

- Network: `integration-test-network`
- Volumes: `postgres-data`, `rabbitmq-data`

**Test Data Fixtures:**

- Location: `tests/fixtures/integration_test_data.sql`
- Includes: 10 test products, 5 test customers, sample inventory levels

## Dependencies

**Work Item Dependencies:**

- [ ] Component A implementation complete
- [ ] Component B implementation complete
- [ ] Integration test infrastructure ready
- [ ] Test data fixtures created

**Service Dependencies:**

- Component A depends on Component B API
- Component B depends on PostgreSQL database
- Both components depend on Redis cache

## Acceptance Criteria

<!-- Specific, measurable criteria that must be met for this integration test to pass -->

**Functional:**

- [ ] All integration test scenarios passing (100% success rate)
- [ ] Happy path (Scenario 1) completes successfully in <span>< 2000ms (p95)</span>
- [ ] Error handling scenarios validated (Scenario 2: insufficient stock handled correctly)
- [ ] Data consistency verified across all services (order status matches payment and inventory state)
- [ ] End-to-end flows complete successfully without manual intervention
- [ ] All services handle errors gracefully (no crashes, proper error responses)
- [ ] Message queue processing works reliably (notifications delivered)

**Performance:**

- [ ] All performance benchmarks met (p95 < 2000ms under 200 orders/minute)
- [ ] No performance regression from baseline (<10% slower than previous version)
- [ ] Resource utilization within limits (CPU < 70%, Memory < 1GB per service)
- [ ] Load tests passing for 15 minutes sustained load
- [ ] Services recover gracefully after traffic spike
- [ ] No memory leaks detected (heap size stable)
- [ ] Database connection pool doesn't exhaust

**Contracts:**

- [ ] API contracts validated (no breaking changes detected)
- [ ] Database schema matches expected version (migration 014 applied)
- [ ] Contract tests passing for all integration points (Order→Payment, Order→Inventory)
- [ ] Message queue contracts verified (order.completed event structure correct)
- [ ] External API contracts verified (Stripe API integration works)

**Documentation:**

- [ ] Integration architecture diagram created (shows all services and connections)
- [ ] Sequence diagrams for all scenarios (mermaid diagrams in spec)
- [ ] API contract documentation updated (YAML files current)
- [ ] Performance baseline documented (benchmark results recorded)
- [ ] Runbook created for troubleshooting integration failures
