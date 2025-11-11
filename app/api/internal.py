"""
Internal endpoints dla Cloud Tasks callbacks.
Nie eksponowane publicznie - tylko dla Google Cloud Tasks.

Security: Weryfikacja nagłówka X-CloudTasks-QueueName
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
import logging

from app.db.session import get_db
from app.services.workflows.execution import WorkflowExecutor

router = APIRouter(prefix="/internal", tags=["Internal"])
logger = logging.getLogger(__name__)


class ExecuteWorkflowPayload(BaseModel):
    """Payload dla wykonania workflow."""
    workflow_id: UUID
    user_id: UUID
    execution_id: UUID


@router.post("/workflows/execute")
async def execute_workflow_internal(
    payload: ExecuteWorkflowPayload,
    x_cloudtasks_queuename: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Internal endpoint dla Cloud Tasks - wykonanie workflow.

    Security:
    - Tylko callable przez Cloud Tasks (weryfikacja header)
    - Nie wymaga autentykacji użytkownika (task już zweryfikowany)

    Args:
        payload: Dane workflow do wykonania
        x_cloudtasks_queuename: Header z Cloud Tasks (weryfikacja)
        db: Database session

    Returns:
        Status wykonania: completed lub failed
    """
    # Weryfikacja requestu z Cloud Tasks
    if x_cloudtasks_queuename != "workflow-executions":
        logger.warning(
            f"Rejected internal call - invalid queue: {x_cloudtasks_queuename}"
        )
        raise HTTPException(status_code=403, detail="Forbidden")

    logger.info(
        f"Executing workflow via Cloud Task: workflow_id={payload.workflow_id}, "
        f"execution_id={payload.execution_id}"
    )

    # Wykonaj workflow
    executor = WorkflowExecutor(db)

    try:
        await executor.execute_workflow_sync(
            workflow_id=payload.workflow_id,
            user_id=payload.user_id,
            execution_id=payload.execution_id
        )

        logger.info(
            f"Workflow execution completed: execution_id={payload.execution_id}"
        )

        return {"status": "completed"}

    except Exception as e:
        logger.error(
            f"Workflow execution failed: execution_id={payload.execution_id}, "
            f"error={str(e)}"
        )

        # Executor powinien już zaktualizować status na failed
        # ale zwracamy error status dla Cloud Tasks
        return {"status": "failed", "error": str(e)}
