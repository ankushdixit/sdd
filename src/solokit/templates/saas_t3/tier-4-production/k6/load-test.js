import http from "k6/http";
import { check, sleep } from "k6";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";

// Test configuration
export const options = {
  stages: [
    { duration: "30s", target: 20 }, // Ramp up to 20 users
    { duration: "1m", target: 20 }, // Stay at 20 users
    { duration: "30s", target: 0 }, // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"], // 95% of requests should be below 500ms
    http_req_failed: ["rate<0.01"], // Less than 1% of requests should fail
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:3000";

export default function () {
  // Test home page
  const homeRes = http.get(`${BASE_URL}/`);
  check(homeRes, {
    "home page status is 200": (r) => r.status === 200,
    "home page loads within 2s": (r) => r.timings.duration < 2000,
  });

  sleep(1);

  // Test API endpoint
  const apiRes = http.post(
    `${BASE_URL}/api/trpc/example.hello`,
    JSON.stringify({ text: "load test" }),
    {
      headers: { "Content-Type": "application/json" },
    }
  );
  check(apiRes, {
    "API status is 200": (r) => r.status === 200,
    "API responds within 500ms": (r) => r.timings.duration < 500,
  });

  sleep(1);
}

// Summary handler
export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: " ", enableColors: true }),
    "reports/load-test-summary.json": JSON.stringify(data),
  };
}
