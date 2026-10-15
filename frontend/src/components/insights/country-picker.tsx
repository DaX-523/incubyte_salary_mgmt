import Form from "next/form";

import { SelectField } from "@/components/form-fields";
import { Button } from "@/components/ui/button";
import { NativeSelectOption } from "@/components/ui/native-select";
import type { CountryOption } from "@/lib/api";
import { countryName } from "@/lib/format";

type Props = { countries: CountryOption[]; selected?: string };

export function CountryPicker({ countries, selected }: Props) {
  const sorted = [...countries].sort((a, b) =>
    countryName(a.code).localeCompare(countryName(b.code)),
  );
  return (
    <Form
      action="/insights"
      aria-label="Choose a country"
      className="flex items-end gap-2"
    >
      <div className="w-64">
        <SelectField
          label="Country"
          name="country"
          required
          defaultValue={selected ?? ""}
        >
          <NativeSelectOption value="" disabled>
            Choose a country
          </NativeSelectOption>
          {sorted.map((country) => (
            <NativeSelectOption key={country.code} value={country.code}>
              {countryName(country.code)} ({country.currency})
            </NativeSelectOption>
          ))}
        </SelectField>
      </div>
      <Button type="submit">Show salaries</Button>
    </Form>
  );
}
