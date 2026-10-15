import Link from "next/link";

// The app name links to the dashboard, so it needs no separate link.
const LINKS = [
  { href: "/insights", label: "Pay by job title" },
  { href: "/employees/new", label: "Add employee" },
];

export function SiteHeader() {
  return (
    <header className="border-b">
      <nav
        aria-label="Main"
        className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-8"
      >
        <Link href="/" className="font-semibold">
          ACME Salary Management portal
        </Link>
        <ul className="flex flex-wrap gap-4 text-sm">
          {LINKS.map((link) => (
            <li key={link.href}>
              <Link
                href={link.href}
                className="text-muted-foreground hover:text-foreground"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
