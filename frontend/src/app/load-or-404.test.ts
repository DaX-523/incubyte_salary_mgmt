import { notFound } from "next/navigation";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";

import { loadOr404 } from "./load-or-404";

vi.mock("next/navigation", () => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
}));

describe("loadOr404", () => {
  it("returns what the API returned", async () => {
    await expect(loadOr404(Promise.resolve({ id: 1 }))).resolves.toEqual({
      id: 1,
    });
  });

  it("shows the not-found page when the API answers 404", async () => {
    await expect(
      loadOr404(Promise.reject(new ApiError(404, "Employee 9 not found"))),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    expect(notFound).toHaveBeenCalled();
  });

  it("lets other failures reach the error page", async () => {
    const failure = new ApiError(500, "The API responded with 500");

    await expect(loadOr404(Promise.reject(failure))).rejects.toBe(failure);
  });
});
