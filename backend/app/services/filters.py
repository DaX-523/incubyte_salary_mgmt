from app.db.models import PaymentMethod
from app.domain.catalog import COUNTRIES, JOB_TITLES
from app.schemas.filters import CountryOption, FilterOptions, JobTitleOption


def filter_options() -> FilterOptions:
    """Catalog values sorted for display in dropdowns."""
    return FilterOptions(
        countries=[
            CountryOption(code=country.code, currency=country.currency)
            for country in sorted(COUNTRIES, key=lambda country: country.code)
        ],
        job_titles=[
            JobTitleOption(title=job.title, department=job.department)
            for job in sorted(JOB_TITLES, key=lambda job: job.title)
        ],
        payment_methods=list(PaymentMethod),
    )
