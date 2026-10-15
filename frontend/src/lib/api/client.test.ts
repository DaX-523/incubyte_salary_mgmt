import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, buildUrl, request } from "./client";

function respondWith(status: number, body?: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), {
      status,
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("buildUrl", () => {
  it("prefixes the path with the versioned API base", () => {
    expect(buildUrl("/employees/1")).toBe(
      "http://localhost:8000/api/v1/employees/1",
    );
  });

  it("uses API_BASE_URL when it is set", () => {
    vi.stubEnv("API_BASE_URL", "https://api.example.com");

    expect(buildUrl("/filters")).toBe("https://api.example.com/api/v1/filters");
  });

  it("leaves out empty and missing query values", () => {
    const url = buildUrl("/employees", {
      month: "2026-10",
      name: "",
      country: undefined,
      page: 2,
    });

    expect(url).toBe(
      "http://localhost:8000/api/v1/employees?month=2026-10&page=2",
    );
  });

  it("encodes query values", () => {
    const url = buildUrl("/employees", {
      job_title: "HR Generalist",
      name: "100% & co",
    });

    expect(url).toBe(
      "http://localhost:8000/api/v1/employees?job_title=HR+Generalist&name=100%25+%26+co",
    );
  });
});

describe("request", () => {
  it("returns the parsed JSON body", async () => {
    respondWith(200, { id: 1 });

    await expect(request("GET", "/employees/1")).resolves.toEqual({ id: 1 });
  });

  it("sends a JSON body with its content type", async () => {
    const fetchMock = respondWith(201, { id: 2 });

    await request("POST", "/employees", { body: { name: "Ada" } });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/employees",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: '{"name":"Ada"}',
      },
    );
  });

  it("returns nothing for 204 No Content", async () => {
    respondWith(204);

    await expect(request("DELETE", "/employees/1")).resolves.toBeUndefined();
  });

  it("raises the API's message for errors like 404", async () => {
    respondWith(404, { detail: "Employee 9 not found" });

    await expect(request("GET", "/employees/9")).rejects.toEqual(
      new ApiError(404, "Employee 9 not found"),
    );
  });

  it("maps validation errors to the fields they belong to", async () => {
    respondWith(422, {
      detail: [
        { loc: ["body", "email"], msg: "not a valid email" },
        { loc: ["body", "email"], msg: "second email problem" },
        { loc: ["body"], msg: "send at least one field" },
      ],
    });

    const error = await request("PATCH", "/employees/1", { body: {} }).catch(
      (e: unknown) => e,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 422,
      message:
        "not a valid email; second email problem; send at least one field",
      fieldErrors: { email: "not a valid email" },
    });
  });

  it.each([
    ["no body", undefined],
    ["an unexpected body", { error: "boom" }],
  ])("falls back to the status code when the error has %s", async (_, body) => {
    respondWith(500, body);

    await expect(request("GET", "/filters")).rejects.toEqual(
      new ApiError(500, "The API responded with 500"),
    );
  });

  it("explains when the API cannot be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("fetch failed")),
    );

    await expect(request("GET", "/filters")).rejects.toThrow(
      "Could not reach the API at http://localhost:8000",
    );
  });
});
