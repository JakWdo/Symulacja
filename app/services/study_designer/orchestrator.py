"""
Study Designer Orchestrator - Główny service layer

Zarządza sesjami konwersacji, integruje state machine z database,
i triggeruje execution po zatwierdzeniu planu.

Responsibilities:
- create_session() - rozpoczyna nową sesję
- process_user_message() - przetwarza wiadomości przez state machine
- approve_plan() - zatwierdza plan i triggeruje wykonanie
- get_session() - pobiera sesję z historią
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from config import features
from app.models.study_designer import StudyDesignerSession, StudyDesignerMessage
from app.services.study_designer.state_machine import ConversationStateMachine
from app.services.study_designer.state_machine_v2 import ConversationStateMachineV2
from app.services.study_designer.state_schema import (
    create_initial_state,
    serialize_state,
    deserialize_state,
)
from app.services.study_designer.study_executor import StudyExecutor

logger = logging.getLogger(__name__)


class StudyDesignerOrchestrator:
    """
    Główny orchestrator Study Designer Chat.

    Integruje LangGraph state machine z persistence layer (PostgreSQL).
    Wspiera v1 (old 7-node) i v2 (new 3-node) architecture via feature flag.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicjalizuje orchestrator.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

        # Feature flag: Choose v1 vs v2 architecture
        use_v2 = features.study_designer.use_v2_architecture

        if use_v2:
            logger.info("[Orchestrator] Using V2 architecture (3-node simplified graph)")
            self.state_machine = ConversationStateMachineV2()
            self.architecture_version = "v2"
        else:
            logger.info("[Orchestrator] Using V1 architecture (7-node legacy graph)")
            self.state_machine = ConversationStateMachine()
            self.architecture_version = "v1"
        logger.debug("StudyDesignerOrchestrator initialized")

    async def create_session(
        self, user_id: UUID, project_id: UUID | None = None
    ) -> StudyDesignerSession:
        """
        Rozpoczyna nową sesję projektowania badania.

        Args:
            user_id: UUID użytkownika
            project_id: UUID projektu (opcjonalne)

        Returns:
            StudyDesignerSession: Utworzona sesja z welcome message
        """
        logger.info(f"Creating new session for user {user_id}")

        # Create session in DB
        session = StudyDesignerSession(
            user_id=user_id,
            project_id=project_id,
            status="active",
            current_stage="welcome",
            conversation_state={},
        )

        self.db.add(session)
        await self.db.flush()  # Get session.id

        # Initialize conversation state
        initial_state = create_initial_state(
            session_id=str(session.id),
            user_id=str(user_id),
            project_id=str(project_id) if project_id else None,
        )

        # Run welcome node
        updated_state = await self.state_machine.initialize_session(initial_state)

        # Save state and welcome message
        session.conversation_state = serialize_state(updated_state)
        session.current_stage = updated_state["current_stage"]

        # Save welcome message to messages table
        for msg in updated_state["messages"]:
            message = StudyDesignerMessage(
                session_id=session.id,
                role=msg["role"],
                content=msg["content"],
                message_metadata={"stage": updated_state["current_stage"]},
            )
            self.db.add(message)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session {session.id} created successfully")

        return session

    async def process_user_message(
        self, session_id: UUID, user_message: str
    ) -> StudyDesignerSession:
        """
        Przetwarza wiadomość użytkownika przez state machine.

        Args:
            session_id: UUID sesji
            user_message: Treść wiadomości użytkownika

        Returns:
            StudyDesignerSession: Zaktualizowana sesja

        Raises:
            HTTPException: 404 jeśli sesja nie istnieje lub nie jest aktywna
        """
        logger.info(f"Processing message for session {session_id}")

        # Load session
        session = await self._load_session(session_id)

        if not session.is_active():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session {session_id} is not active (status={session.status})",
            )

        # Save user message to DB
        user_msg = StudyDesignerMessage(
            session_id=session.id,
            role="user",
            content=user_message,
            message_metadata={"stage": session.current_stage},
        )
        self.db.add(user_msg)

        # Deserialize state
        state = deserialize_state(session.conversation_state)

        # Process through state machine
        try:
            updated_state = await self.state_machine.process_message(state, user_message)
        except Exception as e:
            logger.error(f"State machine failed for session {session_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process message",
            )

        # Update session
        session.conversation_state = serialize_state(updated_state)
        session.current_stage = updated_state["current_stage"]

        # Save assistant messages
        # (new messages are those added after user message)
        new_messages = updated_state["messages"][len(state["messages"]) + 1 :]

        for msg in new_messages:
            if msg["role"] != "user":  # Skip user message (already saved)
                assistant_msg = StudyDesignerMessage(
                    session_id=session.id,
                    role=msg["role"],
                    content=msg["content"],
                    message_metadata={"stage": updated_state["current_stage"]},
                )
                self.db.add(assistant_msg)

        # If plan generated, save it
        if updated_state.get("generated_plan"):
            session.generated_plan = updated_state["generated_plan"]
            session.status = "plan_ready"

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"Session {session_id} updated, stage: {session.current_stage}, "
            f"status: {session.status}"
        )

        return session

    async def process_user_message_stream(
        self, session_id: UUID, user_message: str
    ):
        """
        Streaming version of process_user_message.
        Yields MessageChunk objects during processing dla SSE.

        Args:
            session_id: UUID sesji
            user_message: Treść wiadomości od użytkownika

        Yields:
            MessageChunk: Partial assistant messages during generation
        """
        from app.schemas.study_designer import MessageChunk
        from datetime import datetime

        # Load session
        session = await self._load_session(session_id)

        # Save user message immediately
        user_msg = StudyDesignerMessage(
            session_id=session_id,
            role="user",
            content=user_message,
            created_at=datetime.utcnow(),
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Deserialize conversation state
        state = deserialize_state(session.conversation_state)
        original_message_count = len(state.get("messages", []))

        # Stream from state machine
        final_state = None
        async for state_update in self.state_machine.process_message_stream(
            state, user_message
        ):
            final_state = state_update

            # Extract new messages
            new_messages = state_update.get("messages", [])[original_message_count:]

            for msg in new_messages:
                if msg["role"] == "assistant":
                    yield MessageChunk(
                        role="assistant",
                        content=msg["content"],
                        is_complete=False,
                    )

            # Update count for next iteration
            original_message_count = len(state_update.get("messages", []))

        # Save final state to DB
        if final_state:
            session.conversation_state = serialize_state(final_state)
            session.current_stage = final_state.get("current_stage", session.current_stage)
            session.status = final_state.get("status", session.status)

            # Check if plan was generated
            if final_state.get("generated_plan"):
                session.generated_plan = final_state["generated_plan"]
                session.status = "plan_ready"

            # Save new assistant messages
            new_messages = final_state.get("messages", [])[len(state.get("messages", [])):]
            for msg in new_messages:
                if msg["role"] == "assistant":
                    db_msg = StudyDesignerMessage(
                        session_id=session_id,
                        role="assistant",
                        content=msg["content"],
                        created_at=datetime.utcnow(),
                    )
                    self.db.add(db_msg)

            await self.db.commit()

        # Yield completion event
        yield MessageChunk(
            role="assistant",
            content="",
            is_complete=True,
        )

    async def approve_plan(self, session_id: UUID, user_id: UUID) -> StudyDesignerSession:
        """
        Zatwierdza plan i triggeruje wykonanie badania.

        Args:
            session_id: UUID sesji
            user_id: UUID użytkownika

        Returns:
            StudyDesignerSession: Zaktualizowana sesja

        Raises:
            HTTPException: Jeśli sesja nie ma planu lub nie może być zatwierdzona
        """
        logger.info(f"Approving plan for session {session_id}")

        session = await self._load_session(session_id)

        if not session.can_approve():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session cannot be approved (status={session.status}, "
                f"has_plan={session.generated_plan is not None})",
            )

        # Execute approved plan via StudyExecutor
        try:
            executor = StudyExecutor(self.db)
            workflow_id = await executor.execute_approved_plan(session, user_id)

            logger.info(
                f"Plan approved and workflow {workflow_id} created for session {session.id}"
            )

            # Add system message about successful execution
            system_msg = StudyDesignerMessage(
                session_id=session.id,
                role="system",
                content=f"✅ Plan zatwierdzony! Workflow został utworzony (ID: {str(workflow_id)[:8]}...) i rozpoczyna się wykonanie.",
                message_metadata={"event": "plan_approved", "workflow_id": str(workflow_id)},
            )
            self.db.add(system_msg)

            await self.db.commit()
            await self.db.refresh(session)

        except Exception as e:
            logger.error(
                f"Failed to execute approved plan for session {session.id}: {e}",
                exc_info=True,
            )

            # Rollback session to approved status (not executing) on error
            session.status = "approved"

            # Add error message
            system_msg = StudyDesignerMessage(
                session_id=session.id,
                role="system",
                content=f"⚠️ Plan zatwierdzony, ale wystąpił problem podczas tworzenia workflow: {str(e)}",
                message_metadata={"event": "execution_failed", "error": str(e)},
            )
            self.db.add(system_msg)

            await self.db.commit()
            await self.db.refresh(session)

            # Re-raise to return 500 to client
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute approved plan: {str(e)}",
            ) from e

        logger.info(f"Session {session_id} approved")

        return session

    async def get_session(self, session_id: UUID, user_id: UUID) -> StudyDesignerSession:
        """
        Pobiera sesję z pełną historią wiadomości.

        Args:
            session_id: UUID sesji
            user_id: UUID użytkownika (dla authorization)

        Returns:
            StudyDesignerSession: Sesja z załadowaną relacją messages

        Raises:
            HTTPException: 404 jeśli sesja nie istnieje lub user nie ma dostępu
        """
        session = await self._load_session(session_id, load_messages=True)

        # Check authorization
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session",
            )

        return session

    async def _load_session(
        self, session_id: UUID, load_messages: bool = False
    ) -> StudyDesignerSession:
        """
        Ładuje sesję z bazy danych.

        Args:
            session_id: UUID sesji
            load_messages: Czy załadować messages relation

        Returns:
            StudyDesignerSession

        Raises:
            HTTPException: 404 jeśli sesja nie istnieje
        """
        stmt = select(StudyDesignerSession).where(StudyDesignerSession.id == session_id)

        if load_messages:
            from sqlalchemy.orm import selectinload

            stmt = stmt.options(selectinload(StudyDesignerSession.messages))

        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        return session
