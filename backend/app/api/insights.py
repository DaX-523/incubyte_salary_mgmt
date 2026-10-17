from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import InsightsRepositoryDep
from app.schemas.insights import (
    PayByCountry,
    PayByJobTitle,
    PayByJobTitleQuery,
    PayrollStatus,
    PayrollStatusQuery,
)
from app.services import insights as insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/payroll-status")
def get_payroll_status(
    query: Annotated[PayrollStatusQuery, Query()], insights: InsightsRepositoryDep
) -> PayrollStatus:
    """Paid vs total employees for a month: the dashboard chart."""
    return insights_service.payroll_status(insights, query)


@router.get("/pay-by-job-title")
def get_pay_by_job_title(
    query: Annotated[PayByJobTitleQuery, Query()], insights: InsightsRepositoryDep
) -> PayByJobTitle:
    """Salary range and average per job title within one country."""
    return insights_service.pay_by_job_title(insights, query)


@router.get("/pay-by-country")
def get_pay_by_country(insights: InsightsRepositoryDep) -> PayByCountry:
    """Headcount, average and total monthly salary per country, each in its own currency."""
    return insights_service.pay_by_country(insights)
