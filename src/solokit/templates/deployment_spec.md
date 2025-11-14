# Deployment: [Name]

<!--
TEMPLATE INSTRUCTIONS:
- Replace [Name] with a descriptive name for this deployment
- Fill out all deployment procedures with specific commands
- Include rollback procedures and smoke tests
- Document all environment configuration
- Test the deployment in staging before production
- Remove these instructions before finalizing the spec
-->

## Deployment Scope

<!-- Define what is being deployed and to which environment -->

Define what is being deployed and to which environment.

**Example:**

> Deploy the Order Processing API v2.5.0 to production. This release includes performance improvements, bug fixes for payment processing, and new inventory integration features. Zero-downtime deployment using blue-green strategy.

**Application/Service:**

- Name: order-processing-api
- Version: 2.5.0
- Repository: https://github.com/company/order-api
- Branch/Tag: `v2.5.0` (tagged release)
- Build: `#1234` (CI/CD build number)
- Docker Image: `order-api:2.5.0-abc123`

**Target Environment:**

- Environment: Production
- Cloud Provider: AWS
- Region/Zone: us-east-1 (primary), us-west-2 (replica)
- Cluster/Namespace: `production/order-api`
- Load Balancer: ALB `order-api-prod`
- Deployment Strategy: Blue-Green (zero downtime)

**Scope of Changes:**

- Backend API code changes (15 files modified)
- Database migration: Add `order_metadata` column
- Configuration updates: New Stripe API key
- Infrastructure: No changes (existing resources)

## Deployment Procedure

<!-- Detailed step-by-step deployment instructions with specific commands -->

### Pre-Deployment Checklist

<!-- All items must be checked before deployment can proceed -->

- [ ] All integration tests passed in CI/CD (Build #1234: ✓ PASSED)
- [ ] Security scans passed (0 critical, 0 high vulnerabilities)
- [ ] Code review approved by 2+ engineers
- [ ] Product owner approved release notes
- [ ] Database migration tested in staging
- [ ] Rollback procedure documented and tested
- [ ] Deployment window scheduled (maintenance window if needed)
- [ ] Team notified via Slack #deployments channel
- [ ] On-call engineer identified and available
- [ ] Monitoring dashboards ready (DataDog, Grafana)
- [ ] Feature flags configured (if applicable)
- [ ] Backup of current production state completed

**Pre-Deployment Commands:**

```bash
# 1. Verify staging deployment successful
curl https://staging-api.example.com/health
# Expected: {"status": "healthy", "version": "2.5.0"}

# 2. Backup production database
pg_dump -h prod-db.example.com -U admin -d orders > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Verify backup integrity
pg_restore --list backup_*.sql | wc -l
# Expected: > 100 (tables and data)

# 4. Tag deployment in monitoring
curl -X POST https://api.datadoghq.com/api/v1/events \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -d '{"title":"Deployment Start","text":"v2.5.0 deployment to production starting"}'
```

### Deployment Steps

<!-- Execute these steps in order during the deployment window -->

**Step 1: Prepare New Version (Blue Environment)**

```bash
# Pull latest Docker image
docker pull order-api:2.5.0-abc123

# Verify image integrity
docker inspect order-api:2.5.0-abc123 | grep Created
```

**Step 2: Run Database Migrations**

```bash
# Connect to production database (read-write connection)
psql postgresql://admin:${DB_PASSWORD}@prod-db.example.com:5432/orders

# Run migration (idempotent, safe to re-run)
\i migrations/025_add_order_metadata.sql

# Verify migration
SELECT column_name FROM information_schema.columns
WHERE table_name = 'orders' AND column_name = 'order_metadata';
# Expected: order_metadata

# Check row count (should not change)
SELECT COUNT(*) FROM orders;
# Expected: same as before migration
```

**Step 3: Deploy to Blue Environment**

```bash
# Update ECS task definition with new image
aws ecs register-task-definition \
  --cli-input-json file://task-definition-v2.5.0.json

# Update service to use new task definition (Blue environment)
aws ecs update-service \
  --cluster production \
  --service order-api-blue \
  --task-definition order-api:42 \
  --desired-count 3

# Wait for deployment to complete (5-10 minutes)
aws ecs wait services-stable \
  --cluster production \
  --services order-api-blue
```

**Step 4: Run Smoke Tests on Blue**

```bash
# Execute smoke test suite against blue environment
npm run smoke-test -- --url https://blue.order-api.internal

# Expected output:
# ✓ Health check passed
# ✓ Create order endpoint working
# ✓ Payment processing functional
# ✓ Database connectivity verified
# All smoke tests passed (4/4)
```

**Step 5: Switch Traffic (Blue-Green Cutover)**

```bash
# Update load balancer to route traffic to Blue
aws elbv2 modify-rule \
  --rule-arn arn:aws:elasticloadbalancing:us-east-1:123456:rule/abc123 \
  --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456:targetgroup/order-api-blue

# Monitor traffic switch (gradual if using weighted routing)
watch -n 5 'aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456:targetgroup/order-api-blue'
```

**Step 6: Monitor New Version**

```bash
# Watch error rate in real-time (should stay < 1%)
watch -n 10 'curl -s "https://api.datadoghq.com/api/v1/query?query=sum:api.errors{service:order-api}.as_rate()" -H "DD-API-KEY: ${DD_API_KEY}"'

# Watch response time (p95 should be < 500ms)
watch -n 10 'curl -s "https://api.datadoghq.com/api/v1/query?query=p95:api.response_time{service:order-api}" -H "DD-API-KEY: ${DD_API_KEY}"'

# Check application logs
kubectl logs -n production -l app=order-api --tail=100 -f
```

### Post-Deployment Steps

<!-- Verify deployment success and complete deployment tasks -->

- [ ] Smoke tests passed on production (all 4 tests green)
- [ ] Error rate < 1% for 15 minutes post-deployment
- [ ] Response time p95 < 500ms (no regression)
- [ ] Database queries performing well (no slow query alerts)
- [ ] Critical user flows verified:
  - [ ] Place order and complete payment
  - [ ] View order history
  - [ ] Cancel order
- [ ] Monitoring dashboards show healthy metrics
- [ ] No alerts fired in past 15 minutes
- [ ] Application logs show no errors
- [ ] Team notified of successful deployment
- [ ] Deployment documented in changelog
- [ ] Old version (Green) scaled down after 1 hour soak time

**Post-Deployment Commands:**

```bash
# Tag successful deployment in monitoring
curl -X POST https://api.datadoghq.com/api/v1/events \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -d '{"title":"Deployment Complete","text":"v2.5.0 deployed successfully to production","tags":["deployment:success","version:2.5.0"]}'

# Scale down old version (Green) after soak period
aws ecs update-service \
  --cluster production \
  --service order-api-green \
  --desired-count 0
```

## Environment Configuration

<!-- Document all environment variables, secrets, and infrastructure dependencies -->

**Required Environment Variables:**

```bash
# Database
DATABASE_URL=postgresql://app_user:${DB_PASSWORD}@prod-db.example.com:5432/orders
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT=30000

# Cache
REDIS_URL=redis://:${REDIS_PASSWORD}@prod-redis.example.com:6379/0
REDIS_POOL_SIZE=10

# External APIs
STRIPE_API_KEY=${STRIPE_PROD_API_KEY}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET}

# Application
NODE_ENV=production
PORT=8080
LOG_LEVEL=info
LOG_FORMAT=json

# Feature Flags
FEATURE_NEW_INVENTORY=true
FEATURE_PAYMENT_V2=true

# Monitoring
DATADOG_API_KEY=${DD_API_KEY}
DATADOG_SERVICE_NAME=order-api
DATADOG_ENV=production
```

**Required Secrets (stored in AWS Secrets Manager):**

- `prod/order-api/db-password` - Database password
- `prod/order-api/redis-password` - Redis password
- `prod/order-api/stripe-api-key` - Stripe production API key
- `prod/order-api/stripe-webhook-secret` - Stripe webhook signing secret
- `prod/order-api/datadog-api-key` - DataDog API key

**Secrets Rotation Policy:**

- Database password: Rotate every 90 days
- API keys: Rotate every 180 days
- Webhook secrets: Rotate on compromise only

**Infrastructure Dependencies:**

- Database: PostgreSQL 14.2 (RDS instance: `prod-orders-db.cqx7.us-east-1.rds.amazonaws.com`)
- Cache: Redis 7.0 (ElastiCache cluster: `prod-orders-cache`)
- Load Balancer: ALB `order-api-prod` (arn:aws:elasticloadbalancing:...)
- CDN: CloudFront distribution `E1234ABCD` (for static assets)
- DNS: Route53 hosted zone `example.com`
- Monitoring: DataDog agent v7.40+
- Logging: CloudWatch Logs group `/aws/ecs/order-api`

**Resource Limits:**

- CPU: 2 vCPU per task
- Memory: 4 GB per task
- Disk: 20 GB ephemeral storage
- Network: 1 Gbps

## Rollback Procedure

<!-- Detailed procedure for rolling back if deployment fails -->

### Rollback Triggers

**Automatic Rollback (if enabled):**

- Smoke tests fail (any test fails)
- Error rate exceeds 5% for 5 consecutive minutes
- Response time p95 > 1000ms for 5 minutes
- Health check failures > 50% of instances

**Manual Rollback Decision:**

- Critical bug discovered in production
- Data corruption detected
- Performance degradation > 50%
- Security vulnerability discovered
- Customer-facing feature broken

### Rollback Steps

**IMPORTANT: Rollback must be executed within 30 minutes of deployment**

**Step 1: Stop New Deployments**

```bash
# Pause auto-scaling to prevent new tasks
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/production/order-api-blue \
  --scalable-dimension ecs:service:DesiredCount \
  --suspended-state DynamicScalingInSuspended=true,DynamicScalingOutSuspended=true
```

**Step 2: Switch Traffic Back to Green (Previous Version)**

```bash
# Immediate cutover back to old version
aws elbv2 modify-rule \
  --rule-arn arn:aws:elasticloadbalancing:us-east-1:123456:rule/abc123 \
  --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456:targetgroup/order-api-green

# Verify traffic switched
curl https://api.example.com/health
# Expected: {"status": "healthy", "version": "2.4.0"} (old version)
```

**Step 3: Rollback Database Migration (if needed)**

```bash
# ONLY if migration caused issues
psql postgresql://admin:${DB_PASSWORD}@prod-db.example.com:5432/orders

# Run rollback migration
\i migrations/025_add_order_metadata_rollback.sql

# Verify rollback
SELECT column_name FROM information_schema.columns
WHERE table_name = 'orders' AND column_name = 'order_metadata';
# Expected: (empty) - column removed
```

**Step 4: Scale Down Failed Version**

```bash
# Stop Blue environment (failed version)
aws ecs update-service \
  --cluster production \
  --service order-api-blue \
  --desired-count 0
```

**Step 5: Verify Rollback Success**

```bash
# Run smoke tests against rolled-back version
npm run smoke-test -- --url https://api.example.com

# Check error rate (should drop to normal < 1%)
# Check response times (should return to baseline)
# Verify critical user flows working
```

**Step 6: Post-Rollback Actions**

- [ ] Notify team of rollback via Slack
- [ ] Create incident post-mortem
- [ ] Document root cause
- [ ] Create bug fix work item
- [ ] Schedule fix deployment

### Rollback Time Estimate

- Traffic switch: < 1 minute
- Full rollback (with DB): < 5 minutes
- Verification: < 10 minutes
- **Total rollback time: < 15 minutes**

## Smoke Tests

<!-- Critical tests that must pass for deployment to be considered successful -->

### Test 1: Health Check

```bash
curl https://api.example.com/health
# Expected: {"status": "healthy", "version": "2.5.0", "database": "connected"}
# Pass criteria: HTTP 200, status = healthy
```

### Test 2: Create Order (End-to-End)

```bash
curl -X POST https://api.example.com/api/orders \
  -H "Authorization: Bearer ${TEST_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test_customer_123",
    "items": [{"product_id": "prod_456", "quantity": 1}],
    "payment_method": "card",
    "card_token": "tok_visa_test"
  }'
# Expected: HTTP 201, order_id returned, status = completed
# Pass criteria: Order created, payment processed, inventory reserved
```

### Test 3: Retrieve Order

```bash
curl https://api.example.com/api/orders/test_order_123 \
  -H "Authorization: Bearer ${TEST_TOKEN}"
# Expected: HTTP 200, order details returned
# Pass criteria: Order data matches expected structure
```

### Test 4: Database Connectivity

```bash
curl https://api.example.com/api/internal/db-check \
  -H "X-Internal-Token: ${INTERNAL_TOKEN}"
# Expected: {"database": "connected", "latency_ms": < 50}
# Pass criteria: Database reachable, latency < 100ms
```

### Smoke Test Execution

```bash
# Automated smoke test suite
npm run smoke-test -- \
  --url https://api.example.com \
  --token ${TEST_TOKEN} \
  --timeout 30000 \
  --retries 3

# Expected output:
# ✓ Health check passed (45ms)
# ✓ Create order passed (234ms)
# ✓ Retrieve order passed (12ms)
# ✓ Database connectivity passed (8ms)
#
# All smoke tests passed (4/4)
# Total time: 299ms
```

## Monitoring & Alerting

<!-- Key metrics to monitor during and after deployment -->

**Dashboard:** https://app.datadoghq.com/dashboard/order-api-production

**Key Metrics:**

- Error rate (target: < 1%, alert: > 5%)
- Response time p95 (target: < 500ms, alert: > 1000ms)
- Throughput (baseline: 100 req/min, alert: < 50 req/min)
- Database connection pool (target: < 80%, alert: > 90%)
- Memory usage (target: < 80%, alert: > 90%)
- CPU usage (target: < 70%, alert: > 85%)

**Alerts:**

- High error rate: > 5% for 5 minutes → Page on-call
- Slow responses: p95 > 1000ms for 5 minutes → Slack alert
- Health check failures: > 50% instances → Page on-call
- Database connection exhaustion: > 90% → Page on-call

**Log Queries:**

```bash
# View recent errors
aws logs tail /aws/ecs/order-api --follow --filter-pattern "ERROR"

# View deployment-related logs
aws logs tail /aws/ecs/order-api --follow --filter-pattern "deployment" --since 30m
```

## Acceptance Criteria

<!-- Deployment is considered successful when these criteria are met -->

- [ ] All pre-deployment checks passed
- [ ] Database migration completed successfully (column added)
- [ ] Blue environment deployed and stable (3 tasks running)
- [ ] All smoke tests passed (4/4 tests green)
- [ ] Traffic switched to new version (Blue)
- [ ] Error rate < 1% for 30 minutes post-deployment
- [ ] Response time p95 < 500ms (no regression)
- [ ] No critical alerts fired
- [ ] Critical user flows verified manually
- [ ] Old version (Green) scaled down after 1 hour soak period
- [ ] Deployment documented and team notified
- [ ] Rollback procedure tested and ready if needed

## Post-Deployment Monitoring Period

**Soak Time:** 1 hour (monitor new version before scaling down old)

**Monitoring checklist (during soak time):**

- [ ] 0-15 min: Watch error rate and response time closely
- [ ] 15-30 min: Verify no alerts, check logs for warnings
- [ ] 30-45 min: Verify database performance, check slow queries
- [ ] 45-60 min: Final check of all metrics, prepare to scale down old version

**If issues detected during soak time:**

1. Evaluate severity (critical vs minor)
2. Decide: rollback vs hotfix vs acceptable
3. If rollback: execute rollback procedure
4. If hotfix: create urgent fix and deploy
5. If acceptable: document issue and create follow-up work item

## Dependencies

<!-- Other work items or infrastructure that must be in place -->

- `feature_payment_v2` (must be completed - provides new Stripe integration)
- `integration_test_order_flow` (must pass - validates end-to-end flow)
- Infrastructure: ALB target groups for blue-green deployment (must exist)
- Database migration 024 (must be applied - adds required indexes)

## Estimated Effort

1 session (includes deployment, monitoring, and verification)

<!--
Breakdown:
- Pre-deployment prep: 0.25 sessions
- Deployment execution: 0.25 sessions
- Smoke testing: 0.25 sessions
- Post-deployment monitoring (1 hour soak): 0.25 sessions
-->
