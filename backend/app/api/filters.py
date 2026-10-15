from fastapi import APIRouter

from app.schemas.filters import FilterOptions
from app.services.filters import filter_options

router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("")
def get_filter_options() -> FilterOptions:
    return filter_options()
