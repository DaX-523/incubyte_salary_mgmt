import { notFound } from "next/navigation";

import { ApiError } from "@/lib/api";

/** Awaits an API read, showing the not-found page when the API answers 404. */
export async function loadOr404<Result>(
  load: Promise<Result>,
): Promise<Result> {
  try {
    return await load;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
