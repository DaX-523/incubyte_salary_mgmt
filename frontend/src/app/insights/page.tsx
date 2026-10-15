import { CountryPicker } from "@/components/insights/country-picker";
import { PayByJobTitleTable } from "@/components/insights/pay-by-job-title-table";
import { getFilterOptions, getPayByJobTitle } from "@/lib/api";
import { firstParam, oneOf } from "@/lib/search-params";

export default async function InsightsPage({
  searchParams,
}: PageProps<"/insights">) {
  const [params, options] = await Promise.all([
    searchParams,
    getFilterOptions(),
  ]);
  const codes = options.countries.map((country) => country.code);
  const country = oneOf(firstParam(params.country), codes);
  const pay = country ? await getPayByJobTitle(country) : null;
  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:px-8">
      <header className="grid gap-1">
        <h1 className="text-2xl font-semibold">Pay by job title</h1>
        <p className="text-muted-foreground">
          Salaries are paid in local currency, so each country is compared on
          its own. Rank a job title by salary to see who is paid well above or
          below their peers.
        </p>
      </header>
      <CountryPicker countries={options.countries} selected={country} />
      {pay ? (
        <PayByJobTitleTable data={pay} />
      ) : (
        <p className="text-sm text-muted-foreground">
          Choose a country to see its salary ranges.
        </p>
      )}
    </main>
  );
}
