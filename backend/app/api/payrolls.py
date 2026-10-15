from fastapi import APIRouter

from app.api.dependencies import IdPath, PayrollRepositoryDep
from app.schemas.payrolls import PayrollOut, PayrollUpdate
from app.services import payrolls as payroll_service

router = APIRouter(prefix="/payrolls", tags=["payrolls"])


@router.get("/{payroll_id}")
def get_payroll(payroll_id: IdPath, payrolls: PayrollRepositoryDep) -> PayrollOut:
    return PayrollOut.from_model(payroll_service.get_payroll(payrolls, payroll_id))


@router.patch("/{payroll_id}")
def update_payroll(
    payroll_id: IdPath, body: PayrollUpdate, payrolls: PayrollRepositoryDep
) -> PayrollOut:
    return PayrollOut.from_model(payroll_service.update_payroll(payrolls, payroll_id, body))
