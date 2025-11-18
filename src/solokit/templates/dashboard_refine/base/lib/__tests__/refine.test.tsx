import {
  refineDataProvider,
  refineResources,
  refineOptions,
  refineRouterProvider,
} from "../refine";

describe("refineDataProvider", () => {
  describe("getList", () => {
    it("returns mock user data for users resource", async () => {
      const result = await refineDataProvider.getList({
        resource: "users",
        pagination: { currentPage: 1, pageSize: 10 },
        filters: [],
        sorters: [],
        meta: {},
      });

      expect(result.data).toHaveLength(3);
      expect(result.total).toBe(3);
      expect(result.data[0]).toHaveProperty("id");
      expect(result.data[0]).toHaveProperty("name");
      expect(result.data[0]).toHaveProperty("email");
    });

    it("returns specific mock user data", async () => {
      const result = await refineDataProvider.getList({
        resource: "users",
        pagination: { currentPage: 1, pageSize: 10 },
        filters: [],
        sorters: [],
        meta: {},
      });

      expect(result.data[0]).toEqual({
        id: 1,
        name: "John Doe",
        email: "john@example.com",
      });
      expect(result.data[1]).toEqual({
        id: 2,
        name: "Jane Smith",
        email: "jane@example.com",
      });
      expect(result.data[2]).toEqual({
        id: 3,
        name: "Bob Johnson",
        email: "bob@example.com",
      });
    });

    it("returns empty data for non-users resource", async () => {
      const result = await refineDataProvider.getList({
        resource: "products",
        pagination: { currentPage: 1, pageSize: 10 },
        filters: [],
        sorters: [],
        meta: {},
      });

      expect(result.data).toHaveLength(0);
      expect(result.total).toBe(0);
    });
  });

  describe("getOne", () => {
    it("returns a single mock user", async () => {
      const result = await refineDataProvider.getOne({
        resource: "users",
        id: 1,
        meta: {},
      });

      expect(result.data).toEqual({
        id: 1,
        name: "John Doe",
        email: "john@example.com",
      });
    });

    it("returns mock user with custom id", async () => {
      const result = await refineDataProvider.getOne({
        resource: "users",
        id: 999,
        meta: {},
      });

      expect(result.data.id).toBe(999);
      expect(result.data.name).toBe("John Doe");
      expect(result.data.email).toBe("john@example.com");
    });

    it("returns empty object for non-users resource", async () => {
      const result = await refineDataProvider.getOne({
        resource: "products",
        id: 1,
        meta: {},
      });

      expect(result.data).toEqual({});
    });
  });

  describe("create", () => {
    it("creates a new record with mock id", async () => {
      const variables = {
        name: "New User",
        email: "new@example.com",
      };

      const result = await refineDataProvider.create({
        resource: "users",
        variables,
        meta: {},
      });

      expect(result.data).toEqual({
        id: 1,
        name: "New User",
        email: "new@example.com",
      });
    });

    it("preserves all provided variables", async () => {
      const variables = {
        name: "Test User",
        email: "test@example.com",
        role: "admin",
      };

      const result = await refineDataProvider.create({
        resource: "users",
        variables,
        meta: {},
      });

      expect(result.data).toMatchObject(variables);
    });
  });

  describe("update", () => {
    it("updates a record", async () => {
      const variables = {
        name: "Updated User",
        email: "updated@example.com",
      };

      const result = await refineDataProvider.update({
        resource: "users",
        id: 1,
        variables,
        meta: {},
      });

      expect(result.data).toEqual({
        id: 1,
        name: "Updated User",
        email: "updated@example.com",
      });
    });

    it("preserves the id when updating", async () => {
      const result = await refineDataProvider.update({
        resource: "users",
        id: 42,
        variables: { name: "Test" },
        meta: {},
      });

      expect(result.data.id).toBe(42);
    });
  });

  describe("deleteOne", () => {
    it("deletes a record", async () => {
      const result = await refineDataProvider.deleteOne({
        resource: "users",
        id: 1,
        meta: {},
      });

      expect(result.data).toEqual({ id: 1 });
    });

    it("returns correct id for deleted record", async () => {
      const result = await refineDataProvider.deleteOne({
        resource: "users",
        id: 99,
        meta: {},
      });

      expect(result.data.id).toBe(99);
    });
  });

  describe("getApiUrl", () => {
    it("returns empty string", () => {
      expect(refineDataProvider.getApiUrl()).toBe("");
    });
  });
});

describe("refineResources", () => {
  it("defines users resource correctly", () => {
    const usersResource = refineResources.find((r) => r.name === "users");
    expect(usersResource).toBeDefined();
    expect(usersResource?.list).toBe("/users");
    expect(usersResource?.create).toBe("/users/create");
    expect(usersResource?.edit).toBe("/users/edit/:id");
    expect(usersResource?.show).toBe("/users/show/:id");
    expect(usersResource?.meta?.canDelete).toBe(true);
  });

  it("defines orders resource correctly", () => {
    const ordersResource = refineResources.find((r) => r.name === "orders");
    expect(ordersResource).toBeDefined();
    expect(ordersResource?.list).toBe("/orders");
    expect(ordersResource?.create).toBe("/orders/create");
    expect(ordersResource?.edit).toBe("/orders/edit/:id");
    expect(ordersResource?.show).toBe("/orders/show/:id");
  });

  it("defines products resource correctly", () => {
    const productsResource = refineResources.find((r) => r.name === "products");
    expect(productsResource).toBeDefined();
    expect(productsResource?.list).toBe("/products");
    expect(productsResource?.create).toBe("/products/create");
    expect(productsResource?.edit).toBe("/products/edit/:id");
    expect(productsResource?.show).toBe("/products/show/:id");
    expect(productsResource?.meta?.canDelete).toBe(true);
  });

  it("has exactly 3 resources", () => {
    expect(refineResources).toHaveLength(3);
  });
});

describe("refineOptions", () => {
  it("has correct default options", () => {
    expect(refineOptions.syncWithLocation).toBe(true);
    expect(refineOptions.warnWhenUnsavedChanges).toBe(true);
    expect(refineOptions.useNewQueryKeys).toBe(true);
    expect(refineOptions.projectId).toBe("refine-dashboard");
  });
});

describe("refineRouterProvider", () => {
  it("is defined", () => {
    expect(refineRouterProvider).toBeDefined();
  });
});
