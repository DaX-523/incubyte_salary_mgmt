import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { proxy } from "./proxy";

function visit(path: string, cookie?: string) {
  return proxy(
    new NextRequest(`http://localhost:3000${path}`, {
      headers: cookie ? { cookie } : {},
    }),
  );
}

describe("proxy", () => {
  it.each(["/", "/insights", "/employees/4"])(
    "sends a visitor without a session from %s to the login page",
    (path) => {
      const response = visit(path);

      expect(response.status).toBe(307);
      expect(response.headers.get("location")).toBe(
        "http://localhost:3000/login",
      );
    },
  );

  it("lets a visitor with a session through", () => {
    const response = visit("/insights", "session=abc");

    expect(response.headers.get("location")).toBeNull();
    expect(response.headers.get("x-middleware-next")).toBe("1");
  });

  it.each([undefined, "session=expired"])(
    "always lets the login page through (cookie: %s)",
    (cookie) => {
      const response = visit("/login", cookie);

      expect(response.headers.get("x-middleware-next")).toBe("1");
    },
  );
});
