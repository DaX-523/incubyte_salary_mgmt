import { refresh } from "next/cache";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, updatePayroll } from "@/lib/api";
import { ADA_OCTOBER_PAYROLL } from "@/test/fixtures";

import { updatePayrollAction } from "./actions";

vi.mock("next/cache", () => ({ refresh: vi.fn() }));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  updatePayroll: vi.fn(),
}));

const CHANGES = {
  base: "4780.00",
  bonus: "500",
  esops: "0",
  payment_method: "digital_wallet",
};

function formData(values: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    data.set(key, value);
  }
  return data;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("updatePayrollAction", () => {
  it("saves the corrected amounts and refreshes the page", async () => {
    vi.mocked(updatePayroll).mockResolvedValue(ADA_OCTOBER_PAYROLL);

    const state = await updatePayrollAction(
      12,
      { status: "idle" },
      formData(CHANGES),
    );

    expect(updatePayroll).toHaveBeenCalledWith(12, CHANGES);
    expect(refresh).toHaveBeenCalledOnce();
    expect(state).toEqual({ status: "success", values: CHANGES });
  });

  it("returns field errors without calling the API when the form is invalid", async () => {
    const state = await updatePayrollAction(
      12,
      { status: "idle" },
      formData({ ...CHANGES, bonus: "-1" }),
    );

    expect(state.fieldErrors).toEqual({
      bonus: "Bonus must be an amount like 5000 or 5000.50",
    });
    expect(updatePayroll).not.toHaveBeenCalled();
  });

  it("reports API failures and does not refresh", async () => {
    vi.mocked(updatePayroll).mockRejectedValue(
      new ApiError(404, "Payroll 12 not found"),
    );

    const state = await updatePayrollAction(
      12,
      { status: "idle" },
      formData(CHANGES),
    );

    expect(state).toMatchObject({
      status: "error",
      message: "Payroll 12 not found",
    });
    expect(refresh).not.toHaveBeenCalled();
  });
});
