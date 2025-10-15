# Deployment: [Name]

## Deployment Scope
Define what is being deployed and to which environment.

**Application/Service:**
- Name: [service name]
- Version: [version number]
- Repository: [git repository URL]
- Branch/Tag: [branch or tag to deploy]

**Target Environment:**
- Environment: [staging | production | development]
- Cloud Provider: [AWS | GCP | Azure | on-premise]
- Region/Zone: [deployment region]
- Cluster/Namespace: [if applicable]

## Deployment Procedure

### Pre-Deployment Steps
1. Verify all integration tests passed
2. Verify security scans passed
3. Backup current production state
4. Notify team of deployment window
5. [Add environment-specific steps]

### Deployment Steps
1. Pull latest code from [branch/tag]
2. Build application artifacts
3. Run database migrations (if applicable)
4. Deploy to [target environment]
5. Update configuration
6. Restart services
7. [Add deployment-specific steps]

### Post-Deployment Steps
1. Run smoke tests
2. Verify monitoring dashboards
3. Check error logs
4. Verify critical user flows
5. Update deployment documentation
6. [Add verification steps]

## Environment Configuration

**Required Environment Variables:**
```
DATABASE_URL=<production database connection string>
API_KEY=<external API key>
REDIS_URL=<redis connection string>
LOG_LEVEL=info
```

**Required Secrets:**
- AWS credentials (access key, secret key)
- Database credentials (username, password)
- API tokens (third-party services)

**Infrastructure Dependencies:**
- Database: PostgreSQL 14+
- Cache: Redis 6+
- Load Balancer: configured
- CDN: CloudFront distribution ready
- Monitoring: DataDog agent installed

## Rollback Procedure

### Rollback Triggers
- Smoke tests fail
- Error rate exceeds 5%
- Critical functionality broken
- Performance degradation > 50%
- Manual trigger required

### Rollback Steps
1. Stop new deployment
2. Revert to previous version [version]
3. Restore database to backup [timestamp]
4. Restart services
5. Verify system health
6. Notify team of rollback
7. [Add rollback-specific steps]

**Estimated Rollback Time:** [X minutes]

## Smoke Tests

### Critical User Flows
1. **User Login**
   - Endpoint: POST /api/auth/login
   - Expected: 200 OK, returns JWT token
   - Failure: Rollback immediately

2. **Data Retrieval**
   - Endpoint: GET /api/data
   - Expected: 200 OK, returns data
   - Failure: Rollback immediately

3. **[Add critical flows]**

### Health Checks
- Application health: GET /health
- Database connectivity: verified
- Cache connectivity: verified
- External API connectivity: verified

## Monitoring & Alerting

**Metrics to Monitor:**
- Request rate
- Error rate
- Response time (p95, p99)
- CPU/Memory usage
- Database connections
- Queue depth (if applicable)

**Alert Thresholds:**
- Error rate > 5%: Page on-call
- Response time p99 > 2s: Warning
- CPU > 80%: Warning
- Memory > 90%: Page on-call

## Documentation

**Update Required:**
- [ ] CHANGELOG updated with deployment notes
- [ ] Deployment runbook updated
- [ ] Architecture diagrams updated (if changes)
- [ ] API documentation updated (if API changes)
- [ ] Configuration documentation updated

## Dependencies

**Blocked By:**
- [List work items that must complete before deployment]

**Blocks:**
- [List work items that depend on this deployment]

## Acceptance Criteria

- [ ] All integration tests passed
- [ ] Security scans passed (no high/critical vulnerabilities)
- [ ] Deployment procedure validated in staging
- [ ] Rollback procedure tested successfully
- [ ] Smoke tests defined and tested
- [ ] Monitoring dashboards configured
- [ ] Documentation updated
- [ ] Team notified of deployment
- [ ] Deployment executed successfully
- [ ] Smoke tests passed in production
- [ ] No critical errors in logs
- [ ] Performance metrics within acceptable range
