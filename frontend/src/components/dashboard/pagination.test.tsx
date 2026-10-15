import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { DashboardQuery } from "@/lib/dashboard-query";

import { Pagination } from "./pagination";

vi.mock("next/navigation", () => ({ useRouter: vi.fn() }));

const QUERY: DashboardQuery = {
  month: "2026-10",
  country: "DE",
  sort_by: "name",
  sort_order: "asc",
  page: 2,
  page_size: 25,
};

describe("Pagination", () => {
  it("shows the range on screen and links to the neighbouring pages, keeping filters", () => {
    render(<Pagination query={QUERY} total={60} pageSize={25} />);

    expect(screen.getByText("Showing 26–50 of 60")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Previous page" })).toHaveAttribute(
      "href",
      "/?month=2026-10&country=DE",
    );
    expect(screen.getByRole("link", { name: "Next page" })).toHaveAttribute(
      "href",
      "/?month=2026-10&country=DE&page=3",
    );
  });

  it("keeps the chosen page size in the page links", () => {
    render(
      <Pagination
        query={{ ...QUERY, page_size: 50 }}
        total={160}
        pageSize={50}
      />,
    );

    expect(screen.getByText("Showing 51–100 of 160")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Next page" })).toHaveAttribute(
      "href",
      "/?month=2026-10&country=DE&page=3&page_size=50",
    );
    expect(screen.getByRole("combobox", { name: "Rows per page" })).toHaveValue(
      "50",
    );
  });

  it("has no previous link on the first page", () => {
    render(
      <Pagination query={{ ...QUERY, page: 1 }} total={60} pageSize={25} />,
    );

    expect(
      screen.queryByRole("link", { name: "Previous page" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Next page" })).toBeInTheDocument();
  });

  it("has no next link on the last page", () => {
    render(
      <Pagination query={{ ...QUERY, page: 3 }} total={60} pageSize={25} />,
    );

    expect(screen.getByText("Showing 51–60 of 60")).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Next page" }),
    ).not.toBeInTheDocument();
  });

  it("explains an empty page past the end", () => {
    render(
      <Pagination query={{ ...QUERY, page: 9 }} total={60} pageSize={25} />,
    );

    expect(screen.getByText("No results on page 9")).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Next page" }),
    ).not.toBeInTheDocument();
  });
});
