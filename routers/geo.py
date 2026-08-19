from fastapi import APIRouter, Query
from pydantic import BaseModel

from qthgrid import qth_to_grid

router = APIRouter(prefix="/api/geo", tags=["geo"])


class QthGridOut(BaseModel):
    grid: str = ""
    matched: str = ""
    found: bool = False


@router.get("/qth-grid", response_model=QthGridOut)
def guess_grid(qth: str = Query("", description="QTH 地名，如「北京」「安徽合肥」")):
    """按 QTH 地名估算 4 位网格，供表单实时提示；识别不出返回 found=false。"""
    hit = qth_to_grid(qth)
    if not hit:
        return QthGridOut()
    return QthGridOut(grid=hit[0], matched=hit[1], found=True)
