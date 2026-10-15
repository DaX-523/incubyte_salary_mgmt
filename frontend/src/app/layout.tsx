import type { Metadata } from "next";
import "./globals.css";
import { Geist } from "next/font/google";
import { SiteHeader } from "@/components/site-header";
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Salary Management",
  description:
    "Manage employee salaries and see how the organization pays people",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable)}>
      <body>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
