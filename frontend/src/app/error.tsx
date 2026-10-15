"use client";

import { Button } from "@/components/ui/button";

// Production hides server error messages from the browser, so this explains the likely cause
// instead of showing `error.message`.
export default function ErrorPage({
  retry,
}: {
  error: Error;
  retry: () => void;
}) {
  return (
    <main className="mx-auto grid max-w-6xl gap-4 px-4 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold">Something went wrong</h1>
      <p className="text-muted-foreground">
        The data could not be loaded. Check that the API is running, then try
        again.
      </p>
      <div>
        <Button onClick={() => retry()}>Try again</Button>
      </div>
    </main>
  );
}
