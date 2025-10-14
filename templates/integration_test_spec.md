# Integration Test: [Name]

## Scope
Define which components are being integrated and tested.

**Components:**
- Component A: [name and version]
- Component B: [name and version]
- Component C: [name and version]

**Integration Points:**
- API endpoints being tested
- Database connections
- Message queues
- External services

## Test Scenarios

### Scenario 1: [Happy Path Description]
**Setup:**
- Service A running on port 8001
- Service B running on port 8002
- Database seeded with test data

**Actions:**
1. Client sends request to Service A
2. Service A calls Service B
3. Service B updates database
4. Response propagates back

**Expected Results:**
- HTTP 200 response
- Database contains expected records
- All services log successful operation

### Scenario 2: [Error Handling Description]
**Setup:**
- Service B intentionally unavailable
- Retry logic configured

**Actions:**
1. Client sends request to Service A
2. Service A attempts to call Service B (fails)
3. Service A retries with backoff

**Expected Results:**
- HTTP 503 response after retries exhausted
- Error logged appropriately
- No data corruption

## Performance Benchmarks

**Response Time Requirements:**
- p50: < 100ms
- p95: < 500ms
- p99: < 1000ms

**Throughput Requirements:**
- Minimum: 100 requests/second
- Target: 500 requests/second

**Resource Limits:**
- CPU: < 80% utilization
- Memory: < 2GB per service
- Disk I/O: < 50MB/s

**Load Test Duration:**
- Ramp-up: 5 minutes
- Sustained load: 15 minutes
- Ramp-down: 5 minutes

## API Contracts

**Service A → Service B:**
- Contract file: `contracts/service-a-to-b.yaml`
- Version: 1.2.0
- Breaking changes: None allowed

**Service B → Database:**
- Schema file: `schemas/database-v2.sql`
- Migrations: `migrations/002_add_integration_fields.sql`

## Environment Requirements

**Services Required:**
- service-a:latest
- service-b:latest
- postgres:14
- redis:7

**Configuration:**
- Environment: integration-test
- Config files: `config/integration/*.yaml`
- Secrets: Loaded from `.env.integration-test`

**Infrastructure:**
- Docker Compose file: `docker-compose.integration.yml`
- Network: `integration-test-network`
- Volumes: `postgres-data`, `redis-data`

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

**Functional:**
- [ ] All integration test scenarios passing
- [ ] Error handling scenarios validated
- [ ] Data consistency verified across components
- [ ] End-to-end flows complete successfully

**Performance:**
- [ ] All performance benchmarks met
- [ ] No performance regression from baseline
- [ ] Resource utilization within limits
- [ ] Load tests passing

**Contracts:**
- [ ] API contracts validated (no breaking changes)
- [ ] Database schema matches expected version
- [ ] Contract tests passing for all integration points

**Documentation:**
- [ ] Integration architecture diagram created
- [ ] Sequence diagrams for all scenarios
- [ ] API contract documentation updated
- [ ] Performance baseline documented
