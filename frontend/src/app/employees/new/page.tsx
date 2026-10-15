import { EmployeeForm } from "@/components/employees/employee-form";
import { getFilterOptions } from "@/lib/api";

import { createEmployeeAction } from "../actions";

export default async function NewEmployeePage() {
  const options = await getFilterOptions();
  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold">Add employee</h1>
      <EmployeeForm
        action={createEmployeeAction}
        options={options}
        submitLabel="Add employee"
      />
    </main>
  );
}
