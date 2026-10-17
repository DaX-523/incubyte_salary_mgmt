import Link from "next/link";

import { logoutAction } from "@/app/login/actions";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getProfile } from "@/lib/api";

// The app name links to the dashboard, so it needs no separate link.
const LINKS = [
  { href: "/insights", label: "Pay insights" },
  { href: "/employees/new", label: "Add employee" },
];

/** The signed-in part of the header: the sections, who is logged in, and logging out. */
export async function AccountNav() {
  const profile = await getProfile();
  if (!profile) {
    return null;
  }
  return (
    <>
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
      <div className="flex items-center gap-3 text-sm sm:ml-auto">
        <Badge variant="secondary">{profile.organization}</Badge>
        <span className="text-muted-foreground">{profile.name}</span>
        <form action={logoutAction}>
          <Button type="submit" variant="outline" size="sm">
            Log out
          </Button>
        </form>
      </div>
    </>
  );
}
