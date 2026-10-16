import Link from "next/link";
import { Suspense } from "react";

import { AccountNav } from "@/components/account-nav";
import { AccountNavBoundary } from "@/components/account-nav-boundary";

export function SiteHeader() {
  return (
    <header className="border-b">
      <nav
        aria-label="Main"
        className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-8"
      >
        <Link href="/" className="font-semibold">
          Salary Management
        </Link>
        {/* Streams in with the session, so the rest of the page doesn't wait for it. */}
        <AccountNavBoundary>
          <Suspense fallback={null}>
            <AccountNav />
          </Suspense>
        </AccountNavBoundary>
      </nav>
    </header>
  );
}
