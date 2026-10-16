import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AccountNavBoundary } from "./account-nav-boundary";

function Broken(): never {
  throw new Error("Could not reach the API");
}

describe("AccountNavBoundary", () => {
  it("shows its content when it loads", () => {
    render(
      <AccountNavBoundary>
        <p>ACME HR</p>
      </AccountNavBoundary>,
    );

    expect(screen.getByText("ACME HR")).toBeInTheDocument();
  });

  it("leaves the account details out when they fail to load", () => {
    // React reports the caught error to the console; keep the test output clean.
    vi.spyOn(console, "error").mockImplementation(() => {});

    const { container } = render(
      <AccountNavBoundary>
        <Broken />
      </AccountNavBoundary>,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
