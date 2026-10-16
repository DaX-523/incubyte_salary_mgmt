import { redirect } from "next/navigation";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, login, logout } from "@/lib/api";
import { endSession, startSession } from "@/lib/session";

import { loginAction, logoutAction } from "./actions";

vi.mock("next/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("next/navigation")>()),
  redirect: vi.fn(),
}));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  login: vi.fn(),
  logout: vi.fn(),
}));
vi.mock("@/lib/session", () => ({
  startSession: vi.fn(),
  endSession: vi.fn(),
}));

const IDLE = { status: "idle" } as const;
const CREDENTIALS = { email: "hr@acme.example", password: "secret" };

function formData(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    data.set(key, value);
  }
  return data;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("loginAction", () => {
  it("starts a session that expires with the token, then opens the dashboard", async () => {
    vi.mocked(login).mockResolvedValue({
      access_token: "abc",
      token_type: "bearer",
      expires_at: "2026-10-16T17:00:00Z",
    });

    await loginAction(IDLE, formData(CREDENTIALS));

    expect(login).toHaveBeenCalledWith("hr@acme.example", "secret");
    expect(startSession).toHaveBeenCalledWith(
      "abc",
      new Date("2026-10-16T17:00:00Z"),
    );
    expect(redirect).toHaveBeenCalledWith("/");
  });

  it("shows wrong credentials as a message, keeping the email but not the password", async () => {
    vi.mocked(login).mockRejectedValue(
      new ApiError(401, "Email or password is incorrect"),
    );

    const state = await loginAction(IDLE, formData(CREDENTIALS));

    expect(state).toMatchObject({
      status: "error",
      message: "Email or password is incorrect",
    });
    expect(state.values).toEqual({ email: "hr@acme.example" });
    expect(startSession).not.toHaveBeenCalled();
    expect(redirect).not.toHaveBeenCalled();
  });

  it.each([
    [{ email: " ", password: "secret" }, { email: "Enter your email" }, " "],
    [{ password: "secret" }, { email: "Enter your email" }, ""],
    [
      { email: "hr@acme.example", password: "" },
      { password: "Enter your password" },
      "hr@acme.example",
    ],
  ])(
    "asks for missing fields without calling the API or returning the password (%o)",
    async (submitted, fieldErrors, email) => {
      const state = await loginAction(IDLE, formData(submitted));

      expect(state).toMatchObject({ status: "error", fieldErrors });
      expect(state.values).toEqual({ email });
      expect(login).not.toHaveBeenCalled();
    },
  );
});

describe("logoutAction", () => {
  it("ends the session in the API and the browser, then opens the login page", async () => {
    await logoutAction();

    expect(logout).toHaveBeenCalledOnce();
    expect(endSession).toHaveBeenCalledOnce();
    expect(redirect).toHaveBeenCalledWith("/login");
  });
});
