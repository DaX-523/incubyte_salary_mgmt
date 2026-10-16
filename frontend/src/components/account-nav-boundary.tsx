"use client";

import { catchError } from "next/error";

/**
 * If the account details can't be loaded (for example, the API is down), the header leaves them
 * out instead of failing the whole page. The page itself then explains the problem.
 */
export const AccountNavBoundary = catchError(() => null);
