import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { getProfile } from "@/lib/api";

import { AccountNav } from "./account-nav";

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  getProfile: vi.fn(),
}));
vi.mock("@/app/login/actions", () => ({ logoutAction: vi.fn() }));

describe("AccountNav", () => {
  it("links to every section and shows who is logged in, for which organization", async () => {
    vi.mocked(getProfile).mockResolvedValue({
      name: "ACME HR",
      email: "hr@acme.example",
      organization: "ACME",
    });

    render(await AccountNav());

    expect(
      screen.getByRole("link", { name: "Pay by job title" }),
    ).toHaveAttribute("href", "/insights");
    expect(screen.getByRole("link", { name: "Add employee" })).toHaveAttribute(
      "href",
      "/employees/new",
    );
    expect(screen.getByText("ACME")).toBeInTheDocument();
    expect(screen.getByText("ACME HR")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log out" })).toHaveAttribute(
      "type",
      "submit",
    );
  });

  it("shows nothing when nobody is logged in", async () => {
    vi.mocked(getProfile).mockResolvedValue(null);

    expect(await AccountNav()).toBeNull();
  });
});
