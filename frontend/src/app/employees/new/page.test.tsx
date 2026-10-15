import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { getFilterOptions } from "@/lib/api";
import { OPTIONS } from "@/test/fixtures";

import NewEmployeePage from "./page";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getFilterOptions: vi.fn(),
}));

describe("NewEmployeePage", () => {
  it("shows an empty employee form with the allowed countries", async () => {
    vi.mocked(getFilterOptions).mockResolvedValue(OPTIONS);

    render(await NewEmployeePage());

    expect(
      screen.getByRole("heading", { level: 1, name: "Add employee" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Name" })).toHaveValue("");
    expect(
      screen.getByRole("option", { name: "India (INR)" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add employee" }),
    ).toBeInTheDocument();
  });
});
