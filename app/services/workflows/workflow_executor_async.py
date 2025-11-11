"""
Async workflow execution via Cloud Tasks.
Production-ready background task execution.
"""

from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from datetime import datetime, timedelta
import json
from uuid import UUID
import os
import logging

from config import app as app_config

logger = logging.getLogger(__name__)


class AsyncWorkflowExecutor:
    """
    Wykonuje workflow asynchronicznie poprzez Google Cloud Tasks.

    Cloud Tasks zapewnia:
    - Reliable delivery (retry z exponential backoff)
    - Task scheduling (delay, rate limiting)
    - Dead-letter queues (failed tasks)
    - Monitoring & logging
    """

    def __init__(self):
        self.client = tasks_v2.CloudTasksClient()
        self.project = app_config.gcp.project_id
        self.location = app_config.gcp.region
        self.queue = "workflow-executions"

        self.queue_path = self.client.queue_path(
            self.project,
            self.location,
            self.queue
        )

        # Service URL (Cloud Run)
        self.service_url = os.getenv(
            "SERVICE_URL",
            "https://sight-xfabt2svwa-lm.a.run.app"  # Production URL
        )

    async def schedule_execution(
        self,
        workflow_id: UUID,
        user_id: UUID,
        execution_id: UUID,
        delay_seconds: int = 0
    ) -> str:
        """
        Zaplanuj wykonanie workflow jako Cloud Task.

        Args:
            workflow_id: ID workflow do wykonania
            user_id: ID użytkownika uruchamiającego
            execution_id: ID rekordu WorkflowExecution
            delay_seconds: Opóźnienie przed wykonaniem (default: 0)

        Returns:
            Task name (ID zadania w Cloud Tasks)
        """
        # Task payload
        payload = {
            "workflow_id": str(workflow_id),
            "user_id": str(user_id),
            "execution_id": str(execution_id)
        }

        # Task target URL (internal endpoint)
        target_url = f"{self.service_url}/internal/workflows/execute"

        # Create task
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": target_url,
                "headers": {
                    "Content-Type": "application/json",
                    "X-CloudTasks-QueueName": self.queue
                },
                "body": json.dumps(payload).encode()
            }
        }

        # Schedule time (jeśli delay)
        if delay_seconds > 0:
            d = datetime.utcnow() + timedelta(seconds=delay_seconds)
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(d)
            task["schedule_time"] = timestamp

        try:
            # Create task in Cloud Tasks
            response = self.client.create_task(
                request={
                    "parent": self.queue_path,
                    "task": task
                }
            )

            logger.info(
                f"Scheduled workflow execution: workflow_id={workflow_id}, "
                f"execution_id={execution_id}, task_name={response.name}"
            )

            return response.name

        except Exception as e:
            logger.error(
                f"Failed to schedule workflow execution: workflow_id={workflow_id}, "
                f"error={str(e)}"
            )
            raise

    async def cancel_execution(self, task_name: str) -> None:
        """
        Anuluj zaplanowane zadanie.

        Args:
            task_name: Nazwa zadania (zwrócona przez schedule_execution)
        """
        try:
            self.client.delete_task(name=task_name)
            logger.info(f"Cancelled task: {task_name}")
        except Exception as e:
            logger.error(f"Failed to cancel task {task_name}: {str(e)}")
            raise
