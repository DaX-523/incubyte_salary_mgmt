import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getFilterOptions, getPayByJobTitle } from "@/lib/api";
import { GERMAN_PAY, OPTIONS } from "@/test/fixtures";

import InsightsPage from "./page";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getFilterOptions: vi.fn(),
  getPayByJobTitle: vi.fn(),
}));

async function renderInsights(searchParams: Record<string, string> = {}) {
  render(
    await InsightsPage({
      params: Promise.resolve({}),
      searchParams: Promise.resolve(searchParams),
    }),
  );
}

beforeEach(() => {
  vi.mocked(getFilterOptions).mockResolvedValue(OPTIONS);
  vi.mocked(getPayByJobTitle).mockResolvedValue(GERMAN_PAY);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("InsightsPage", () => {
  it("asks for a country before comparing salaries", async () => {
    await renderInsights();

    expect(
      screen.getByRole("heading", { level: 1, name: "Pay by job title" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Choose a country to see its salary ranges."),
    ).toBeInTheDocument();
    expect(getPayByJobTitle).not.toHaveBeenCalled();
  });

  it("shows the salary ranges for the chosen country", async () => {
    await renderInsights({ country: "DE" });

    expect(getPayByJobTitle).toHaveBeenCalledWith("DE");
    expect(
      screen.getByRole("table", {
        name: "Monthly salaries of active employees in Germany, in EUR",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Country" })).toHaveValue("DE");
  });

  it("ignores a country the API does not offer", async () => {
    await renderInsights({ country: "XX" });

    expect(getPayByJobTitle).not.toHaveBeenCalled();
    expect(
      screen.getByText("Choose a country to see its salary ranges."),
    ).toBeInTheDocument();
  });
});
