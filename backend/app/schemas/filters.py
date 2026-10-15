from pydantic import BaseModel

from app.db.models import PaymentMethod


class CountryOption(BaseModel):
    code: str
    currency: str


class JobTitleOption(BaseModel):
    title: str
    department: str


class FilterOptions(BaseModel):
    """Allowed values for the filters and forms, so clients never hard-code them."""

    countries: list[CountryOption]
    job_titles: list[JobTitleOption]
    payment_methods: list[PaymentMethod]
