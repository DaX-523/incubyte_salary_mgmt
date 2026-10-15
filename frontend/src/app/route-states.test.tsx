import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ErrorPage from "./error";
import Loading from "./loading";
import NotFound from "./not-found";

describe("route states", () => {
  it("announces loading", () => {
    render(<Loading />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading…");
  });

  it("explains a failure and retries on request", async () => {
    const user = userEvent.setup();
    const retry = vi.fn();
    render(<ErrorPage error={new Error("fetch failed")} retry={retry} />);

    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(
      screen.getByRole("heading", { name: "Something went wrong" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Check that the API is running/),
    ).toBeInTheDocument();
    expect(retry).toHaveBeenCalledOnce();
  });

  it("links back to the dashboard from a missing record", () => {
    render(<NotFound />);

    expect(
      screen.getByRole("link", { name: "Back to the dashboard" }),
    ).toHaveAttribute("href", "/");
  });
});
