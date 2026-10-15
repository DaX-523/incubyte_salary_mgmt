import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto grid max-w-6xl gap-4 px-4 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold">Not found</h1>
      <p className="text-muted-foreground">
        That employee or payroll does not exist.
      </p>
      <Link href="/" className="underline underline-offset-4">
        Back to the dashboard
      </Link>
    </main>
  );
}
