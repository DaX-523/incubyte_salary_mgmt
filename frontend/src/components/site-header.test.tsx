import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SiteHeader } from "./site-header";

// The account part loads the session on the server; it has its own tests.
vi.mock("@/components/account-nav", () => ({
  AccountNav: () => <p>Account</p>,
}));

describe("SiteHeader", () => {
  it("leads home from the app name and holds the account navigation", () => {
    render(<SiteHeader />);

    const nav = within(screen.getByRole("navigation", { name: "Main" }));
    expect(
      nav.getByRole("link", { name: "Salary Management" }),
    ).toHaveAttribute("href", "/");
    expect(nav.getByText("Account")).toBeInTheDocument();
  });
});
