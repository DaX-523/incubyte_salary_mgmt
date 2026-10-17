import { CountryPicker } from "@/components/insights/country-picker";
import { PayByCountryTable } from "@/components/insights/pay-by-country-table";
import { PayByJobTitleTable } from "@/components/insights/pay-by-job-title-table";
import { getFilterOptions, getPayByCountry, getPayByJobTitle } from "@/lib/api";
import { firstParam, oneOf } from "@/lib/search-params";

export default async function InsightsPage({
  searchParams,
}: PageProps<"/insights">) {
  const [params, options, byCountry] = await Promise.all([
    searchParams,
    getFilterOptions(),
    getPayByCountry(),
  ]);
  const codes = options.countries.map((country) => country.code);
  const country = oneOf(firstParam(params.country), codes);
  const pay = country ? await getPayByJobTitle(country) : null;
  return (
    <main className="mx-auto grid max-w-6xl gap-10 px-4 py-8 sm:px-8">
      <header className="grid gap-1">
        <h1 className="text-2xl font-semibold">Pay insights</h1>
        <p className="text-muted-foreground">
          Salaries are paid in local currency, so each country is shown on its
          own and never added to another.
        </p>
      </header>
      <section aria-labelledby="by-country-heading" className="grid gap-4">
        <h2 id="by-country-heading" className="text-lg font-semibold">
          By country
        </h2>
        <PayByCountryTable data={byCountry} />
      </section>
      <section aria-labelledby="by-job-title-heading" className="grid gap-4">
        <div className="grid gap-1">
          <h2 id="by-job-title-heading" className="text-lg font-semibold">
            By job title
          </h2>
          <p className="text-sm text-muted-foreground">
            Rank a job title by salary to see who is paid well above or below
            their peers.
          </p>
        </div>
        <CountryPicker countries={options.countries} selected={country} />
        {pay ? (
          <PayByJobTitleTable data={pay} />
        ) : (
          <p className="text-sm text-muted-foreground">
            Choose a country to see its salary ranges.
          </p>
        )}
      </section>
    </main>
  );
}
