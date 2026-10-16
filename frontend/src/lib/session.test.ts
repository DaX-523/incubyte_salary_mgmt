import { cookies } from "next/headers";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { endSession, getSessionToken, startSession } from "./session";

vi.mock("next/headers", () => ({ cookies: vi.fn() }));

const cookieStore = { get: vi.fn(), set: vi.fn(), delete: vi.fn() };
const EXPIRES_AT = new Date("2026-10-16T17:00:00Z");

beforeEach(() => {
  vi.mocked(cookies).mockResolvedValue(
    cookieStore as unknown as Awaited<ReturnType<typeof cookies>>,
  );
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("session cookie", () => {
  it("reads the token from the session cookie", async () => {
    cookieStore.get.mockReturnValue({ name: "session", value: "abc" });

    await expect(getSessionToken()).resolves.toBe("abc");
    expect(cookieStore.get).toHaveBeenCalledWith("session");
  });

  it("has no token without the cookie", async () => {
    cookieStore.get.mockReturnValue(undefined);

    await expect(getSessionToken()).resolves.toBeUndefined();
  });

  it("stores the token where scripts and other sites can't use it", async () => {
    await startSession("abc", EXPIRES_AT);

    expect(cookieStore.set).toHaveBeenCalledWith("session", "abc", {
      httpOnly: true,
      sameSite: "lax",
      secure: false,
      path: "/",
      expires: EXPIRES_AT,
    });
  });

  it("only sends the cookie over HTTPS in production", async () => {
    vi.stubEnv("NODE_ENV", "production");

    await startSession("abc", EXPIRES_AT);

    expect(cookieStore.set).toHaveBeenCalledWith(
      "session",
      "abc",
      expect.objectContaining({ secure: true }),
    );
  });

  it("deletes the cookie when the session ends", async () => {
    await endSession();

    expect(cookieStore.delete).toHaveBeenCalledWith("session");
  });
});
