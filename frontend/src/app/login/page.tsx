import type { Metadata } from "next";

import { LoginForm } from "@/components/login-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";

import { loginAction } from "./actions";

export const metadata: Metadata = { title: "Log in · Salary Management" };

export default function LoginPage() {
  return (
    <main className="mx-auto grid max-w-sm gap-6 px-4 py-12">
      <Card>
        <CardHeader>
          <h1 className="text-xl font-semibold">Log in</h1>
          <CardDescription>
            Use your HR account to manage your organization&apos;s salaries.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm action={loginAction} />
        </CardContent>
      </Card>
    </main>
  );
}
