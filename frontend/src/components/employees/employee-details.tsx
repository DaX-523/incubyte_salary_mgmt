import type { Employee } from "@/lib/api";
import { countryName, formatMoney } from "@/lib/format";

export function EmployeeDetails({ employee }: { employee: Employee }) {
  const details = [
    ["Employee ID", employee.id],
    ["Email", employee.email],
    ["Country", `${countryName(employee.country)} (${employee.currency})`],
    ["Department", employee.department],
    ["Job title", employee.job_title],
    ["Monthly salary", formatMoney(employee.monthly_salary, employee.currency)],
    ["Status", employee.is_active ? "Active" : "Inactive"],
  ] as const;
  return (
    <dl className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
      {details.map(([label, value]) => (
        <div key={label}>
          <dt className="text-muted-foreground">{label}</dt>
          <dd className="font-medium">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
