import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useRouter } from "next/navigation";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DashboardQuery } from "@/lib/dashboard-query";

import { RowsPerPage } from "./rows-per-page";

vi.mock("next/navigation", () => ({ useRouter: vi.fn() }));

const push = vi.fn();

const QUERY: DashboardQuery = {
  month: "2026-10",
  country: "DE",
  sort_by: "monthly_salary",
  sort_order: "desc",
  page: 4,
  page_size: 25,
};

function optionLabels() {
  const select = screen.getByRole("combobox", {
    name: "Rows per page",
  }) as HTMLSelectElement;
  return Array.from(select.options).map((option) => option.textContent);
}

beforeEach(() => {
  vi.mocked(useRouter).mockReturnValue({
    push,
  } as unknown as ReturnType<typeof useRouter>);
});

describe("RowsPerPage", () => {
  it("offers 25, 50 or 100 rows and shows the current choice", () => {
    render(<RowsPerPage query={QUERY} />);

    expect(optionLabels()).toEqual(["25", "50", "100"]);
    expect(screen.getByRole("combobox", { name: "Rows per page" })).toHaveValue(
      "25",
    );
  });

  it("goes back to the first page with the new size, keeping filters and sort", async () => {
    const user = userEvent.setup();
    render(<RowsPerPage query={QUERY} />);

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Rows per page" }),
      "100",
    );

    expect(push).toHaveBeenCalledWith(
      "/?month=2026-10&country=DE&sort_by=monthly_salary&sort_order=desc&page_size=100",
    );
  });

  it("drops the page size from the URL when going back to the default", async () => {
    const user = userEvent.setup();
    render(<RowsPerPage query={{ ...QUERY, page_size: 50 }} />);

    await user.selectOptions(
      screen.getByRole("combobox", { name: "Rows per page" }),
      "25",
    );

    expect(push).toHaveBeenCalledWith(
      "/?month=2026-10&country=DE&sort_by=monthly_salary&sort_order=desc",
    );
  });
});
