import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  it("links to every section of the app, with the app name leading home", () => {
    render(<SiteHeader />);

    const nav = within(screen.getByRole("navigation", { name: "Main" }));
    expect(
      nav.getByRole("link", { name: "Salary Management" }),
    ).toHaveAttribute("href", "/");
    expect(nav.getByRole("link", { name: "Pay by job title" })).toHaveAttribute(
      "href",
      "/insights",
    );
    expect(nav.getByRole("link", { name: "Add employee" })).toHaveAttribute(
      "href",
      "/employees/new",
    );
    expect(nav.getAllByRole("link")).toHaveLength(3);
  });
});
