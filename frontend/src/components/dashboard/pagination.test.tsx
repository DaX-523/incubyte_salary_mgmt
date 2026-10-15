import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { DashboardQuery } from "@/lib/dashboard-query";

import { Pagination } from "./pagination";

const QUERY: DashboardQuery = {
  month: "2026-10",
  country: "DE",
  sort_by: "id",
  sort_order: "asc",
  page: 2,
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
