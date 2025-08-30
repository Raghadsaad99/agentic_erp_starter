# app/api/approvals.py

from typing       import Any, Dict, List, Optional
from fastapi      import APIRouter, HTTPException
from pydantic     import BaseModel

from services.sql import execute_query

router = APIRouter()


class ApprovalRecord(BaseModel):
    id: int
    module: str
    payload_json: str
    status: str
    requested_by: str
    decided_by: Optional[str]
    created_at: str
    decided_at: Optional[str]


class DecisionRequest(BaseModel):
    decision: str
    decided_by: str


@router.get("/", response_model=List[ApprovalRecord])
def list_approvals(status: Optional[str] = None):
    base_q = (
        "SELECT id, module, payload_json, status, requested_by, decided_by, "
        "created_at, decided_at FROM approvals"
    )
    params: tuple[Any, ...] = ()
    if status:
        base_q += " WHERE status = ?"
        params = (status,)

    rows = execute_query(base_q, params)
    return rows


@router.post("/{approval_id}/decision")
def decide_approval(
    approval_id: int,
    decision_req: DecisionRequest
) -> Dict[str, Any]:
    decision, decided_by = decision_req.decision, decision_req.decided_by

    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    q = """
    UPDATE approvals
       SET status = ?, decided_by = ?, decided_at = datetime('now')
     WHERE id = ?
    """
    execute_query(q, (decision, decided_by, approval_id))

    return {
        "id": approval_id,
        "status": decision,
        "decided_by": decided_by
    }
