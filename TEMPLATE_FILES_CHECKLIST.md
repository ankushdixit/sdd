# Template Files Checklist - All 4 Stacks

This document provides an exhaustive checklist of all template files needed for the 4 validated stacks.

---

## 📋 Stack 1: SaaS T3 (saas_t3)

**Base Framework:** Next.js 16.0.1 + React 19.2.0 + tRPC 11.7.1 + Prisma 6.19.0

### ✅ Base Files (Always Included)

**Configuration Files:**
- [ ] `package.json.template` - Base package.json with placeholders
- [ ] `tsconfig.json` - TypeScript configuration (strict mode)
- [ ] `next.config.ts` - Next.js configuration
- [ ] `tailwind.config.ts` - Tailwind CSS configuration
- [ ] `postcss.config.mjs` - PostCSS configuration
- [ ] `.gitignore` - Next.js-specific gitignore

**Environment:**
- [ ] `.env.example` - Environment variables template

**Starter Code:**
- [ ] `app/layout.tsx` - Root layout with metadata
- [ ] `app/page.tsx` - Home page
- [ ] `app/globals.css` - Global styles with Tailwind imports
- [ ] `server/api/root.ts` - tRPC router root
- [ ] `server/api/routers/example.ts` - Example tRPC router
- [ ] `server/api/trpc.ts` - tRPC configuration
- [ ] `server/db.ts` - Prisma client singleton
- [ ] `prisma/schema.prisma` - Base Prisma schema
- [ ] `lib/api.ts` - tRPC client setup
- [ ] `lib/utils.ts` - Utility functions (cn, etc.)

### ✅ Tier 1: Essential

**Linting & Formatting:**
- [ ] `.eslintrc.json` - ESLint config with Next.js + TypeScript rules
- [ ] `.prettierrc` - Prettier configuration
- [ ] `.prettierignore` - Prettier ignore patterns

**Testing:**
- [ ] `jest.config.ts` - Jest configuration for Next.js
- [ ] `jest.setup.ts` - Jest setup with @testing-library/jest-dom
- [ ] `tests/unit/example.test.tsx` - Example unit test
- [ ] `tests/setup.ts` - Test setup utilities

**Scripts (in package.json.tier1.template):**
- [ ] Add: `test`, `test:coverage`, `lint`, `format`, `type-check`

### ✅ Tier 2: Standard

**Pre-commit Hooks:**
- [ ] `.husky/pre-commit` - Husky pre-commit hook
- [ ] `.lintstagedrc.json` - Lint-staged configuration

**Security:**
- [ ] `.git-secrets` - git-secrets configuration
- [ ] `.npmrc` - npm configuration with security settings

**Scripts (in package.json.tier2.template):**
- [ ] Add: `prepare` (husky install), `audit`

### ✅ Tier 3: Comprehensive

**Code Quality:**
- [ ] `.jscpd.json` - Code duplication detection config
- [ ] `stryker.conf.json` - Mutation testing config
- [ ] `type-coverage.json` - Type coverage config

**E2E Testing:**
- [ ] `playwright.config.ts` - Playwright configuration
- [ ] `tests/e2e/home.spec.ts` - Example E2E test
- [ ] `.axe-config.json` - Accessibility testing config

**Integration Testing:**
- [ ] `tests/integration/api.test.ts` - API integration test

**Scripts (in package.json.tier3.template):**
- [ ] Add: `test:e2e`, `test:mutation`, `test:integration`, `check:duplication`, `check:types`

### ✅ Tier 4: Production-Ready

**Monitoring & Error Tracking:**
- [ ] `sentry.client.config.ts` - Sentry client config
- [ ] `sentry.server.config.ts` - Sentry server config
- [ ] `sentry.edge.config.ts` - Sentry edge config
- [ ] `instrumentation.ts` - Next.js instrumentation

**Performance:**
- [ ] `next.config.ts` (updated) - Add bundle analyzer, performance settings
- [ ] `.lighthouserc.json` - Lighthouse CI config
- [ ] `k6/load-test.js` - Load testing script

**Deployment:**
- [ ] `vercel.json` - Vercel deployment config (optional)

**Scripts (in package.json.tier4.template):**
- [ ] Add: `analyze`, `lighthouse`, `load-test`

### ✅ CI/CD Option (ci-cd/)

**GitHub Actions:**
- [ ] `.github/workflows/quality-check.yml` - Lint, format, type-check
- [ ] `.github/workflows/test.yml` - Unit, integration, E2E tests
- [ ] `.github/workflows/security.yml` - Security scanning, audit
- [ ] `.github/workflows/build.yml` - Build verification
- [ ] `.github/workflows/deploy.yml` - Deployment workflow

### ✅ Docker Option (docker/)

- [ ] `Dockerfile` - Multi-stage production build
- [ ] `.dockerignore` - Docker ignore patterns
- [ ] `docker-compose.yml` - Local development with PostgreSQL
- [ ] `docker-compose.prod.yml` - Production configuration

### ✅ Pre-commit Option (pre-commit/)

- [ ] `.pre-commit-config.yaml` - Pre-commit hooks configuration
- [ ] Husky scripts (if not in tier-2)

### ✅ Environment Templates Option (env-templates/)

- [ ] `.editorconfig` - Universal editor configuration
- [ ] `.env.local.example` - Local development env
- [ ] `.env.test.example` - Test environment env
- [ ] `.env.production.example` - Production environment env

---

## 📋 Stack 2: ML/AI FastAPI (ml_ai_fastapi)

**Base Framework:** Python 3.11+ + FastAPI 0.115.6 + SQLModel 0.0.25

### ✅ Base Files (Always Included)

**Configuration Files:**
- [ ] `pyproject.toml.template` - Base Python project config
- [ ] `requirements.txt.template` - Base dependencies
- [ ] `.python-version` - Python version specification (3.11)
- [ ] `.gitignore` - Python-specific gitignore

**Environment:**
- [ ] `.env.example` - Environment variables template

**Starter Code:**
- [ ] `src/main.py` - FastAPI application entry point
- [ ] `src/__init__.py` - Package marker
- [ ] `src/api/__init__.py` - API package
- [ ] `src/api/routes/__init__.py` - Routes package
- [ ] `src/api/routes/health.py` - Health check endpoint
- [ ] `src/api/routes/example.py` - Example route
- [ ] `src/api/dependencies.py` - FastAPI dependencies
- [ ] `src/models/__init__.py` - Models package
- [ ] `src/models/example.py` - Example SQLModel model
- [ ] `src/services/__init__.py` - Services package
- [ ] `src/services/example.py` - Example service
- [ ] `src/core/__init__.py` - Core package
- [ ] `src/core/config.py` - Configuration management with pydantic-settings
- [ ] `src/core/database.py` - Database connection and session
- [ ] `alembic.ini` - Alembic configuration
- [ ] `alembic/env.py` - Alembic environment
- [ ] `alembic/versions/.gitkeep` - Keep versions directory

### ✅ Tier 1: Essential

**Linting & Formatting:**
- [ ] `ruff.toml` - Ruff linter/formatter configuration
- [ ] `pyrightconfig.json` - Pyright type checker config

**Testing:**
- [ ] `pytest.ini` - Pytest configuration
- [ ] `tests/__init__.py` - Tests package
- [ ] `tests/conftest.py` - Pytest fixtures
- [ ] `tests/unit/__init__.py` - Unit tests package
- [ ] `tests/unit/test_example.py` - Example unit test
- [ ] `tests/test_main.py` - Test FastAPI app startup

**Scripts (in pyproject.toml.tier1.template):**
- [ ] Add: test, lint, format, type-check commands

### ✅ Tier 2: Standard

**Security:**
- [ ] `.bandit` - Bandit security linter config
- [ ] `.secrets.baseline` - detect-secrets baseline
- [ ] `.pre-commit-config.yaml` - Pre-commit hooks

**Scripts (in pyproject.toml.tier2.template):**
- [ ] Add: security, audit commands

### ✅ Tier 3: Comprehensive

**Code Quality:**
- [ ] `.radon.cfg` - Complexity analysis config
- [ ] `.vulture` - Dead code detection config
- [ ] `mutmut_config.py` - Mutation testing config

**Load Testing:**
- [ ] `locustfile.py` - Locust load testing script

**Integration Testing:**
- [ ] `tests/integration/__init__.py` - Integration tests package
- [ ] `tests/integration/test_api.py` - API integration test
- [ ] `tests/integration/conftest.py` - Integration test fixtures

**Scripts (in pyproject.toml.tier3.template):**
- [ ] Add: test:mutation, test:integration, load-test, check:complexity

### ✅ Tier 4: Production-Ready

**Monitoring:**
- [ ] `src/core/monitoring.py` - Prometheus metrics setup
- [ ] `src/core/logging.py` - Structured logging with structlog
- [ ] `src/core/sentry.py` - Sentry error tracking

**Health & Observability:**
- [ ] `src/api/routes/metrics.py` - Prometheus metrics endpoint
- [ ] `src/middleware/logging.py` - Request logging middleware
- [ ] `src/middleware/tracing.py` - OpenTelemetry tracing

**Scripts (in pyproject.toml.tier4.template):**
- [ ] Add: monitoring, profiling commands

### ✅ CI/CD Option (ci-cd/)

**GitHub Actions:**
- [ ] `.github/workflows/quality-check.yml` - Lint, format, type-check
- [ ] `.github/workflows/test.yml` - Unit, integration tests
- [ ] `.github/workflows/security.yml` - Security scanning
- [ ] `.github/workflows/deploy.yml` - Deployment workflow

### ✅ Docker Option (docker/)

- [ ] `Dockerfile` - Multi-stage production build
- [ ] `.dockerignore` - Docker ignore patterns
- [ ] `docker-compose.yml` - Local dev with PostgreSQL, Redis
- [ ] `docker-compose.prod.yml` - Production configuration

### ✅ Pre-commit Option (pre-commit/)

- [ ] `.pre-commit-config.yaml` - Pre-commit configuration (if not in tier-2)

### ✅ Environment Templates Option (env-templates/)

- [ ] `.editorconfig` - Universal editor configuration
- [ ] `.env.local.example` - Local development env
- [ ] `.env.test.example` - Test environment env
- [ ] `.env.production.example` - Production environment env

---

## 📋 Stack 3: Dashboard Refine (dashboard_refine)

**Base Framework:** Next.js 16.0.1 + React 19.2.0 + Refine 5.0.5

### ✅ Base Files (Always Included)

**Configuration Files:**
- [ ] `package.json.template` - Base package.json
- [ ] `tsconfig.json` - TypeScript configuration
- [ ] `next.config.ts` - Next.js configuration
- [ ] `tailwind.config.ts` - Tailwind CSS configuration
- [ ] `components.json` - shadcn/ui configuration
- [ ] `.gitignore` - Next.js-specific gitignore

**Environment:**
- [ ] `.env.example` - Environment variables template

**Starter Code:**
- [ ] `app/layout.tsx` - Root layout with Refine provider
- [ ] `app/page.tsx` - Dashboard home
- [ ] `app/(dashboard)/layout.tsx` - Dashboard layout
- [ ] `app/(dashboard)/page.tsx` - Dashboard page
- [ ] `app/(dashboard)/users/page.tsx` - Example resource page
- [ ] `app/globals.css` - Global styles
- [ ] `components/ui/button.tsx` - shadcn button component
- [ ] `components/ui/card.tsx` - shadcn card component
- [ ] `components/ui/table.tsx` - shadcn table component
- [ ] `components/layout/header.tsx` - Dashboard header
- [ ] `components/layout/sidebar.tsx` - Dashboard sidebar
- [ ] `lib/refine.tsx` - Refine configuration
- [ ] `lib/utils.ts` - Utility functions
- [ ] `providers/refine-provider.tsx` - Refine provider component

### ✅ Tier 1: Essential

**Linting & Formatting:**
- [ ] `.eslintrc.json` - ESLint config
- [ ] `.prettierrc` - Prettier configuration
- [ ] `.prettierignore` - Prettier ignore patterns

**Testing:**
- [ ] `vitest.config.ts` - Vitest configuration (faster than Jest for dashboards)
- [ ] `tests/unit/example.test.tsx` - Example component test
- [ ] `tests/setup.ts` - Test setup

**Scripts (in package.json.tier1.template):**
- [ ] Add: `test`, `test:coverage`, `test:ui`, `lint`, `format`

### ✅ Tier 2: Standard

**Pre-commit Hooks:**
- [ ] `.husky/pre-commit` - Husky pre-commit hook
- [ ] `.lintstagedrc.json` - Lint-staged configuration

**Security:**
- [ ] `.git-secrets` - git-secrets configuration
- [ ] `.npmrc` - npm configuration

**Scripts (in package.json.tier2.template):**
- [ ] Add: `prepare`, `audit`

### ✅ Tier 3: Comprehensive

**Code Quality:**
- [ ] `.jscpd.json` - Code duplication config
- [ ] `stryker.conf.json` - Mutation testing
- [ ] `.axe-config.json` - Accessibility testing (critical for dashboards!)

**E2E Testing:**
- [ ] `playwright.config.ts` - Playwright configuration
- [ ] `tests/e2e/dashboard.spec.ts` - Dashboard E2E test
- [ ] `tests/e2e/user-management.spec.ts` - Example resource E2E test

**Integration Testing:**
- [ ] `tests/integration/dashboard.test.tsx` - Integration test

**Scripts (in package.json.tier3.template):**
- [ ] Add: `test:e2e`, `test:a11y`, `test:mutation`, `check:duplication`

### ✅ Tier 4: Production-Ready

**Monitoring:**
- [ ] `sentry.client.config.ts` - Sentry client
- [ ] `sentry.server.config.ts` - Sentry server
- [ ] `instrumentation.ts` - Next.js instrumentation

**Performance:**
- [ ] `.lighthouserc.json` - Lighthouse CI
- [ ] `k6/dashboard-load-test.js` - Load testing

**Scripts (in package.json.tier4.template):**
- [ ] Add: `analyze`, `lighthouse`

### ✅ CI/CD Option (ci-cd/)

**GitHub Actions:**
- [ ] `.github/workflows/quality-check.yml` - Quality gates
- [ ] `.github/workflows/test.yml` - All tests
- [ ] `.github/workflows/security.yml` - Security scanning
- [ ] `.github/workflows/a11y.yml` - Accessibility tests (important!)
- [ ] `.github/workflows/deploy.yml` - Deployment

### ✅ Docker Option (docker/)

- [ ] `Dockerfile` - Multi-stage build
- [ ] `.dockerignore` - Docker ignore
- [ ] `docker-compose.yml` - Local dev
- [ ] `docker-compose.prod.yml` - Production

### ✅ Pre-commit Option (pre-commit/)

- [ ] `.pre-commit-config.yaml` - Pre-commit hooks

### ✅ Environment Templates Option (env-templates/)

- [ ] `.editorconfig` - Editor configuration
- [ ] `.env.local.example` - Local env
- [ ] `.env.test.example` - Test env
- [ ] `.env.production.example` - Production env

---

## 📋 Stack 4: Full-Stack Next.js (fullstack_nextjs)

**Base Framework:** Next.js 16.0.1 + React 19.2.0 + Prisma 6.19.0

### ✅ Base Files (Always Included)

**Configuration Files:**
- [ ] `package.json.template` - Base package.json
- [ ] `tsconfig.json` - TypeScript configuration
- [ ] `next.config.ts` - Next.js configuration
- [ ] `tailwind.config.ts` - Tailwind CSS configuration
- [ ] `.gitignore` - Next.js-specific gitignore

**Environment:**
- [ ] `.env.example` - Environment variables template

**Starter Code:**
- [ ] `app/layout.tsx` - Root layout
- [ ] `app/page.tsx` - Home page
- [ ] `app/api/example/route.ts` - Example API route
- [ ] `app/globals.css` - Global styles
- [ ] `components/example-component.tsx` - Example component
- [ ] `lib/prisma.ts` - Prisma client singleton
- [ ] `lib/utils.ts` - Utility functions
- [ ] `lib/validations.ts` - Zod schemas
- [ ] `prisma/schema.prisma` - Base Prisma schema

### ✅ Tier 1: Essential

**Linting & Formatting:**
- [ ] `.eslintrc.json` - ESLint configuration
- [ ] `.prettierrc` - Prettier configuration
- [ ] `.prettierignore` - Prettier ignore

**Testing:**
- [ ] `jest.config.ts` - Jest configuration
- [ ] `jest.setup.ts` - Jest setup
- [ ] `tests/unit/example.test.ts` - Example test
- [ ] `tests/api/example.test.ts` - API route test

**Scripts (in package.json.tier1.template):**
- [ ] Add: `test`, `test:coverage`, `lint`, `format`

### ✅ Tier 2: Standard

**Pre-commit Hooks:**
- [ ] `.husky/pre-commit` - Husky pre-commit
- [ ] `.lintstagedrc.json` - Lint-staged config

**Security:**
- [ ] `.git-secrets` - git-secrets config
- [ ] `.npmrc` - npm configuration

**Scripts (in package.json.tier2.template):**
- [ ] Add: `prepare`, `audit`

### ✅ Tier 3: Comprehensive

**Code Quality:**
- [ ] `.jscpd.json` - Duplication detection
- [ ] `stryker.conf.json` - Mutation testing

**E2E Testing:**
- [ ] `playwright.config.ts` - Playwright config
- [ ] `tests/e2e/flow.spec.ts` - E2E test

**Integration Testing:**
- [ ] `tests/integration/api.test.ts` - Integration test

**Scripts (in package.json.tier3.template):**
- [ ] Add: `test:e2e`, `test:mutation`, `test:integration`

### ✅ Tier 4: Production-Ready

**Monitoring:**
- [ ] `sentry.client.config.ts` - Sentry client
- [ ] `sentry.server.config.ts` - Sentry server
- [ ] `instrumentation.ts` - Instrumentation

**Performance:**
- [ ] `.lighthouserc.json` - Lighthouse CI
- [ ] `k6/load-test.js` - Load testing

**Scripts (in package.json.tier4.template):**
- [ ] Add: `analyze`, `lighthouse`

### ✅ CI/CD Option (ci-cd/)

**GitHub Actions:**
- [ ] `.github/workflows/quality-check.yml` - Quality gates
- [ ] `.github/workflows/test.yml` - Tests
- [ ] `.github/workflows/security.yml` - Security
- [ ] `.github/workflows/deploy.yml` - Deployment

### ✅ Docker Option (docker/)

- [ ] `Dockerfile` - Multi-stage build
- [ ] `.dockerignore` - Docker ignore
- [ ] `docker-compose.yml` - Local dev with PostgreSQL
- [ ] `docker-compose.prod.yml` - Production

### ✅ Pre-commit Option (pre-commit/)

- [ ] `.pre-commit-config.yaml` - Pre-commit hooks

### ✅ Environment Templates Option (env-templates/)

- [ ] `.editorconfig` - Editor configuration
- [ ] `.env.local.example` - Local env
- [ ] `.env.test.example` - Test env
- [ ] `.env.production.example` - Production env

---

## 📊 Summary Statistics

### Total Files by Stack

**SaaS T3:** ~85 files
- Base: 16 files
- Tier 1: 8 files
- Tier 2: 4 files
- Tier 3: 10 files
- Tier 4: 9 files
- CI/CD: 5 files
- Docker: 4 files
- Pre-commit: 1 file
- Env templates: 4 files
- Tests: ~25 files

**ML/AI FastAPI:** ~75 files
- Base: 20 files
- Tier 1: 7 files
- Tier 2: 4 files
- Tier 3: 9 files
- Tier 4: 6 files
- CI/CD: 4 files
- Docker: 4 files
- Pre-commit: 1 file
- Env templates: 4 files
- Tests: ~17 files

**Dashboard Refine:** ~90 files
- Base: 20 files
- Tier 1: 7 files
- Tier 2: 4 files
- Tier 3: 11 files
- Tier 4: 7 files
- CI/CD: 5 files (includes a11y!)
- Docker: 4 files
- Pre-commit: 1 file
- Env templates: 4 files
- Tests: ~28 files

**Full-Stack Next.js:** ~70 files
- Base: 14 files
- Tier 1: 7 files
- Tier 2: 4 files
- Tier 3: 8 files
- Tier 4: 7 files
- CI/CD: 4 files
- Docker: 4 files
- Pre-commit: 1 file
- Env templates: 4 files
- Tests: ~18 files

### Grand Total: ~320 template files across all 4 stacks

---

## 🎯 Priority Order for Implementation

### Phase 1: Minimum Viable Template (SaaS T3 only)
1. Base files (16 files)
2. Tier 1 Essential (8 files)
3. Basic tests (3-5 test files)
**Total: ~30 files for initial testing**

### Phase 2: Complete SaaS T3
1. Tier 2, 3, 4 files (~25 files)
2. All test files (~25 files)
3. CI/CD option (~5 files)
4. Docker option (~4 files)
5. Env templates option (~4 files)
**Total: ~85 files for complete SaaS T3**

### Phase 3: Remaining Stacks
1. ML/AI FastAPI (~75 files)
2. Dashboard Refine (~90 files)
3. Full-Stack Next.js (~70 files)

---

## 📝 Notes

- All `.template` files need `{project_name}`, `{project_description}` placeholder support
- Package manager files (package.json, pyproject.toml) are cumulative across tiers
- Tests should be minimal but functional examples
- CI/CD workflows should be production-ready
- Docker files should follow multi-stage build best practices
- All stacks share same environment template structure (.editorconfig, .env files)
