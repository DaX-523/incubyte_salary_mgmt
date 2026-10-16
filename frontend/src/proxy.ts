import { type NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE } from "@/lib/session";

const LOGIN_PATH = "/login";

/**
 * Sends visitors without a session cookie to the login page. This only checks that the cookie
 * exists: the API verifies the token on every call. The login page stays reachable, so a stale
 * cookie can never cause a redirect loop.
 */
export function proxy(request: NextRequest) {
  if (
    request.cookies.has(SESSION_COOKIE) ||
    request.nextUrl.pathname === LOGIN_PATH
  ) {
    return NextResponse.next();
  }
  return NextResponse.redirect(new URL(LOGIN_PATH, request.url));
}

export const config = {
  // Every page, but not Next.js's own assets or the favicon.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
