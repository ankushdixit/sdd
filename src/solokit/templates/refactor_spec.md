# Refactor: [Refactor Title]

<!--
TEMPLATE INSTRUCTIONS:
- Replace [Refactor Title] with a concise description of what's being refactored
- Include before/after code examples to show the improvement
- Clearly document why this refactor is valuable
- Be explicit about scope to avoid scope creep
- Remove these instructions before finalizing the spec
-->

## Overview

<!-- What is being refactored and why is it important? -->

What is being refactored and why?

**Example:**

> Refactor the UserService class to use dependency injection instead of direct instantiation of dependencies. This will improve testability, reduce coupling, and make the codebase more maintainable as we scale.

## Current State

<!-- Description of the current implementation with code examples -->

**Example:**

> The `UserService` class directly instantiates its dependencies (DatabaseClient, EmailService, CacheManager), making it difficult to test and tightly coupled to specific implementations.

**Current Code:**

```typescript
// src/services/UserService.ts (BEFORE)
class UserService {
  private db: DatabaseClient;
  private email: EmailService;
  private cache: CacheManager;

  constructor() {
    // Hard-coded dependencies - difficult to test!
    this.db = new DatabaseClient(config.database);
    this.email = new EmailService(config.email);
    this.cache = new CacheManager(config.redis);
  }

  async createUser(data: UserData): Promise<User> {
    const user = await this.db.insert("users", data);
    await this.email.sendWelcomeEmail(user.email);
    await this.cache.set(`user:${user.id}`, user);
    return user;
  }
}
```

## Problems with Current Approach

<!-- Specific issues with the current implementation -->

- **Tight Coupling:** Service is tightly coupled to specific implementations of DatabaseClient, EmailService, and CacheManager
- **Difficult to Test:** Cannot mock dependencies in unit tests without complex workarounds
- **Configuration Hardcoding:** Config is accessed directly, making it hard to override for different environments
- **Single Responsibility Violation:** Constructor is responsible for both dependency creation and initialization
- **No Interface Contracts:** Dependencies don't implement interfaces, making swapping implementations impossible

**Test Difficulty Example:**

```typescript
// Current test - requires real dependencies!
describe("UserService", () => {
  it("creates a user", async () => {
    const service = new UserService(); // Can't inject mocks!
    // Test requires real database, email server, Redis...
  });
});
```

## Proposed Refactor

### New Approach

<!-- Description of the refactored implementation with code examples -->

**Example:**

> Introduce dependency injection using constructor injection with interface-based dependencies. Create interfaces for each dependency and inject them through the constructor.

**Refactored Code:**

```typescript
// src/interfaces/IDatabase.ts (NEW)
interface IDatabase {
  insert(table: string, data: any): Promise<any>;
  find(table: string, id: string): Promise<any>;
}

// src/interfaces/IEmailService.ts (NEW)
interface IEmailService {
  sendWelcomeEmail(email: string): Promise<void>;
}

// src/interfaces/ICacheManager.ts (NEW)
interface ICacheManager {
  set(key: string, value: any): Promise<void>;
  get(key: string): Promise<any>;
}

// src/services/UserService.ts (AFTER)
class UserService {
  constructor(
    private db: IDatabase,
    private email: IEmailService,
    private cache: ICacheManager,
  ) {
    // Dependencies injected - easy to test!
  }

  async createUser(data: UserData): Promise<User> {
    const user = await this.db.insert("users", data);
    await this.email.sendWelcomeEmail(user.email);
    await this.cache.set(`user:${user.id}`, user);
    return user;
  }
}

// src/container.ts (NEW) - Dependency injection container
export const container = {
  userService: new UserService(new DatabaseClient(config.database), new EmailService(config.email), new CacheManager(config.redis)),
};
```

### Benefits

<!-- Concrete benefits of the refactored approach -->

- **Testability:** Can easily inject mocks/stubs in tests
- **Loose Coupling:** Service depends on interfaces, not concrete implementations
- **Flexibility:** Easy to swap implementations (e.g., use different cache provider)
- **Maintainability:** Clear dependency contracts via interfaces
- **Single Responsibility:** Constructor only receives dependencies, doesn't create them

**Testing Improvement:**

```typescript
// New test - easy to mock dependencies!
describe("UserService", () => {
  it("creates a user", async () => {
    const mockDb = { insert: jest.fn().mockResolvedValue({ id: "123" }) };
    const mockEmail = { sendWelcomeEmail: jest.fn() };
    const mockCache = { set: jest.fn() };

    const service = new UserService(mockDb, mockEmail, mockCache);
    await service.createUser({ name: "Test" });

    expect(mockDb.insert).toHaveBeenCalled();
    expect(mockEmail.sendWelcomeEmail).toHaveBeenCalled();
  });
});
```

### Trade-offs

<!-- Any downsides or considerations -->

- **Slightly More Boilerplate:** Need to define interfaces for dependencies
- **Container Setup:** Need to set up dependency injection container
- **Learning Curve:** Team needs to understand DI pattern
- **Migration Effort:** Existing code needs to be updated to use new pattern

## Implementation Plan

<!-- Step-by-step plan for implementing the refactor -->

1. **Phase 1: Create Interfaces** (0.5 sessions)
   - Define `IDatabase`, `IEmailService`, `ICacheManager` interfaces
   - Ensure existing implementations satisfy interfaces

2. **Phase 2: Refactor UserService** (0.5 sessions)
   - Update `UserService` constructor to accept injected dependencies
   - Update all methods to use injected dependencies

3. **Phase 3: Create DI Container** (0.5 sessions)
   - Create `src/container.ts` with dependency wiring
   - Update application entry point to use container

4. **Phase 4: Update Tests** (1 session)
   - Refactor all UserService tests to use mocks
   - Add new tests for edge cases now easy to test

5. **Phase 5: Update Callers** (0.5 sessions)
   - Update all code that instantiates UserService
   - Ensure all use container.userService instead

## Scope

### In Scope

<!-- What will be refactored in this work item -->

- UserService class refactoring
- Interface definitions for Database, EmailService, CacheManager
- Basic dependency injection container
- UserService test refactoring
- Documentation updates

### Out of Scope

<!-- What will NOT be refactored -->

- Refactoring other services (future work)
- Advanced DI container features (auto-wiring, decorators)
- Refactoring DatabaseClient, EmailService, CacheManager internals
- Performance optimization (separate work item)

## Risk Assessment

<!-- Identify and mitigate risks -->

- **Risk Level:** Medium
- **Risks:**
  - Breaking existing functionality if dependency wiring is incorrect
  - Tests might miss integration issues if mocking is too aggressive
  - Performance regression if DI container adds overhead
- **Mitigation:**
  - Comprehensive test coverage before and after refactor
  - Integration tests to verify end-to-end functionality
  - Performance benchmarks to detect regressions
  - Gradual rollout with feature flag
  - Code review focusing on dependency correctness

## Acceptance Criteria

<!-- Define specific, measurable criteria for considering this refactor complete -->
<!-- Minimum 3 items required for spec validation -->

- [ ] All code in scope has been refactored according to the proposed approach
- [ ] All existing functionality preserved (no breaking changes)
- [ ] All existing tests pass without modification
- [ ] Code quality metrics improved (complexity, coupling, testability)
- [ ] No performance regressions detected
- [ ] New tests added for previously untestable scenarios
- [ ] Code review completed and approved
- [ ] Documentation updated to reflect new structure

**Example criteria for a specific refactor:**

- [ ] UserService uses dependency injection with interface-based contracts
- [ ] All UserService dependencies injected through constructor
- [ ] Unit test code reduced by >30% due to improved mockability
- [ ] Cyclomatic complexity reduced from 12 to 6
- [ ] 100% test coverage maintained or improved

## Testing Strategy

<!-- How to verify the refactor doesn't break anything -->

### Automated Tests

- [ ] All existing UserService tests pass with new implementation
- [ ] New tests added for previously untestable scenarios
- [ ] Integration tests verify end-to-end functionality
- [ ] Performance tests show no regression (< 5% latency increase)

### Manual Testing

- [ ] User creation flow works end-to-end
- [ ] Error handling works correctly
- [ ] Email notifications are sent
- [ ] Cache is populated correctly

### Code Quality Metrics

- [ ] Cyclomatic complexity reduced by at least 20%
- [ ] Test coverage increased from 65% to 85%+
- [ ] No new linting errors introduced
- [ ] Code duplication reduced

## Dependencies

<!-- List any dependencies on other work -->

- None (this is a self-contained refactor)

## Estimated Effort

3 sessions

<!--
Breakdown:
- Phase 1: 0.5 sessions
- Phase 2: 0.5 sessions
- Phase 3: 0.5 sessions
- Phase 4: 1 session
- Phase 5: 0.5 sessions
-->
