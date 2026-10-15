import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FormStatus } from "./form-status";

describe("FormStatus", () => {
  it("confirms a successful submission", () => {
    render(
      <FormStatus
        state={{ status: "success" }}
        successMessage="Changes saved."
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Changes saved.");
  });

  it("shows a problem with the whole form", () => {
    render(
      <FormStatus
        state={{ status: "error", message: "Employee 1 is inactive" }}
        successMessage="Changes saved."
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Employee 1 is inactive",
    );
  });

  it.each([
    ["before the first submission", { status: "idle" as const }],
    [
      "for field errors, which show next to their fields",
      { status: "error" as const },
    ],
  ])("shows nothing %s", (_, state) => {
    const { container } = render(
      <FormStatus state={state} successMessage="Changes saved." />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
