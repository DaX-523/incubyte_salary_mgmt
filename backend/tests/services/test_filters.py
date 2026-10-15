from app.db.models import PaymentMethod
from app.services.filters import filter_options


def test_lists_countries_sorted_by_code_with_their_currency() -> None:
    countries = filter_options().countries

    assert [country.code for country in countries] == [
        "AU", "BR", "CA", "DE", "FR", "GB", "IN", "JP", "SG", "US",
    ]  # fmt: skip
    assert countries[0].currency == "AUD"


def test_lists_job_titles_sorted_with_their_department() -> None:
    job_titles = filter_options().job_titles

    assert len(job_titles) == 20
    assert (job_titles[0].title, job_titles[0].department) == ("Account Executive", "Sales")
    assert [job.title for job in job_titles] == sorted(job.title for job in job_titles)


def test_lists_the_supported_payment_methods() -> None:
    assert filter_options().payment_methods == [
        PaymentMethod.BANK_TRANSFER,
        PaymentMethod.DIGITAL_WALLET,
    ]
