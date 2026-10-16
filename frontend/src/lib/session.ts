import { cookies } from "next/headers";

/** The cookie that holds the logged-in user's API token. */
export const SESSION_COOKIE = "session";

export async function getSessionToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

/**
 * Keeps the token where page scripts can't read it (HttpOnly) and other sites' forms can't send
 * it (SameSite=Lax). It expires with the token.
 */
export async function startSession(token: string, expiresAt: Date) {
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    // Local development runs on plain http://localhost.
    secure: process.env.NODE_ENV === "production",
    path: "/",
    expires: expiresAt,
  });
}

export async function endSession() {
  (await cookies()).delete(SESSION_COOKIE);
}
