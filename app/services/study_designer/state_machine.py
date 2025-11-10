"""
Study Designer State Machine - LangGraph orchestration

Główny state machine zarządzający przepływem konwersacji.
Wykorzystuje LangGraph StateGraph do routing między nodes.

Flow:
welcome → gather_goal → define_audience → select_method
→ configure_details → generate_plan → await_approval → execute
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from fastapi import HTTPException, status
from langgraph.graph import StateGraph, END
from app.services.study_designer.state_schema import ConversationState
from app.services.study_designer.nodes import (
    welcome_node,
    gather_goal_node,
    define_audience_node,
    select_method_node,
    configure_details_node,
    generate_plan_node,
    await_approval_node,
)

logger = logging.getLogger(__name__)


class ConversationStateMachine:
    """
    LangGraph state machine dla Study Designer.

    Orchestruje przepływ konwersacji przez różne etapy zbierania informacji
    i generowania planu badania.

    Attributes:
        graph: Skompilowany LangGraph StateGraph
        config: LangGraph config z recursion_limit
    """

    # LangGraph config - zwiększony recursion_limit dla complex conversations
    LANGGRAPH_CONFIG = {
        "recursion_limit": 50,  # Zwiększono z domyślnych 25 → 50
        "configurable": {},
    }

    def __init__(self):
        """Inicjalizuje state machine i buduje graph."""
        self.graph = self._build_graph()
        logger.info(
            f"[State Machine] Initialized successfully with recursion_limit={self.LANGGRAPH_CONFIG['recursion_limit']}"
        )

    def _build_graph(self) -> StateGraph:
        """
        Buduje LangGraph state graph z nodes i transitions.

        Returns:
            Skompilowany StateGraph
        """
        # Create state graph
        workflow = StateGraph(ConversationState)

        # Add all nodes
        workflow.add_node("welcome", welcome_node)
        workflow.add_node("gather_goal", gather_goal_node)
        workflow.add_node("define_audience", define_audience_node)
        workflow.add_node("select_method", select_method_node)
        workflow.add_node("configure_details", configure_details_node)
        workflow.add_node("generate_plan", generate_plan_node)
        workflow.add_node("await_approval", await_approval_node)

        # Set entry point
        workflow.set_entry_point("welcome")

        # Define edges (transitions)
        # Welcome → gather_goal (zawsze)
        workflow.add_edge("welcome", "gather_goal")

        # gather_goal → define_audience LUB stay in gather_goal
        # (routing bazowany na state.current_stage ustawianym przez node)
        workflow.add_conditional_edges(
            "gather_goal",
            self._route_from_gather_goal,
            {
                "define_audience": "define_audience",
                "gather_goal": "gather_goal",  # Loop back if goal unclear
            },
        )

        # define_audience → select_method LUB stay
        workflow.add_conditional_edges(
            "define_audience",
            self._route_from_define_audience,
            {
                "select_method": "select_method",
                "define_audience": "define_audience",
            },
        )

        # select_method → configure_details LUB stay
        workflow.add_conditional_edges(
            "select_method",
            self._route_from_select_method,
            {
                "configure_details": "configure_details",
                "select_method": "select_method",
            },
        )

        # configure_details → generate_plan LUB stay
        workflow.add_conditional_edges(
            "configure_details",
            self._route_from_configure_details,
            {
                "generate_plan": "generate_plan",
                "configure_details": "configure_details",
            },
        )

        # generate_plan → await_approval (zawsze)
        workflow.add_edge("generate_plan", "await_approval")

        # await_approval → execute LUB configure_details LUB END
        workflow.add_conditional_edges(
            "await_approval",
            self._route_from_await_approval,
            {
                "execute": END,  # Kończymy graph, execution będzie w orchestrator
                "configure_details": "configure_details",  # Modyfikacja
                "end": END,  # Anulowanie
            },
        )

        # Compile graph
        compiled = workflow.compile()
        logger.info("[State Machine] Graph compiled successfully")

        return compiled

    def _route_from_gather_goal(
        self, state: ConversationState
    ) -> Literal["define_audience", "gather_goal"]:
        """Routing logic po gather_goal node."""
        next_stage = state.get("current_stage", "gather_goal")
        return "define_audience" if next_stage == "define_audience" else "gather_goal"

    def _route_from_define_audience(
        self, state: ConversationState
    ) -> Literal["select_method", "define_audience"]:
        """Routing logic po define_audience node."""
        next_stage = state.get("current_stage", "define_audience")
        return "select_method" if next_stage == "select_method" else "define_audience"

    def _route_from_select_method(
        self, state: ConversationState
    ) -> Literal["configure_details", "select_method"]:
        """Routing logic po select_method node."""
        next_stage = state.get("current_stage", "select_method")
        return (
            "configure_details" if next_stage == "configure_details" else "select_method"
        )

    def _route_from_configure_details(
        self, state: ConversationState
    ) -> Literal["generate_plan", "configure_details"]:
        """Routing logic po configure_details node."""
        next_stage = state.get("current_stage", "configure_details")
        return "generate_plan" if next_stage == "generate_plan" else "configure_details"

    def _route_from_await_approval(
        self, state: ConversationState
    ) -> Literal["execute", "configure_details", "end"]:
        """Routing logic po await_approval node."""
        next_stage = state.get("current_stage", "await_approval")

        if next_stage == "execute":
            return "execute"
        elif next_stage == "configure_details":
            return "configure_details"
        else:
            return "end"

    async def process_message(
        self, state: ConversationState, user_message: str
    ) -> ConversationState:
        """
        Przetwarza wiadomość użytkownika przez state machine.

        Args:
            state: Aktualny stan konwersacji
            user_message: Wiadomość od użytkownika

        Returns:
            ConversationState: Zaktualizowany stan po przetworzeniu

        Raises:
            Exception: Jeśli graph execution failuje
        """
        session_id = state.get("session_id", "unknown")
        current_stage = state.get("current_stage", "unknown")

        logger.info(
            f"[State Machine] Processing message for session {session_id}, "
            f"stage: {current_stage}"
        )

        try:
            # Dodaj user message do state (nodes będą go pobierać)
            state["messages"].append({"role": "user", "content": user_message})

            # Run graph from current stage with config (recursion_limit)
            # Timeout 45s (bezpiecznie poniżej Cloud Run 60s default timeout)
            try:
                result = await asyncio.wait_for(
                    self.graph.ainvoke(state, config=self.LANGGRAPH_CONFIG),
                    timeout=45.0
                )
            except asyncio.TimeoutError:
                logger.error(
                    f"[State Machine] Timeout exceeded (45s) for session {session_id}, "
                    f"stage: {current_stage}",
                    extra={"alert": True}
                )
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Przetwarzanie czatu przekroczyło limit czasu (45s). Spróbuj ponownie z prostszym pytaniem."
                )

            logger.info(
                f"[State Machine] Message processed, new stage: {result.get('current_stage')}"
            )

            return result

        except HTTPException:
            # Re-raise HTTPException (timeout error)
            raise
        except Exception as e:
            logger.error(
                f"[State Machine] Failed to process message for session {session_id}: {e}",
                exc_info=True,
            )
            raise

    async def process_message_stream(
        self, state: ConversationState, user_message: str
    ):
        """
        Streaming version using LangGraph .astream().
        Yields state updates after each node execution dla SSE.

        Args:
            state: Current conversation state
            user_message: User's message to process

        Yields:
            ConversationState: Partial state updates during graph execution

        Raises:
            HTTPException: Jeśli timeout exceeded (45s)
            Exception: Jeśli graph execution failuje
        """
        session_id = state.get("session_id", "unknown")
        current_stage = state.get("current_stage", "unknown")

        logger.info(
            f"[State Machine] STREAMING message for session {session_id}, "
            f"stage: {current_stage}"
        )

        try:
            # Add user message to state
            state["messages"].append({"role": "user", "content": user_message})

            # Stream with timeout - używamy .astream() zamiast .ainvoke()
            try:
                async for state_update in asyncio.wait_for(
                    self.graph.astream(
                        state,
                        config=self.LANGGRAPH_CONFIG,
                        stream_mode="updates"  # Yields deltas after each node
                    ),
                    timeout=45.0
                ):
                    logger.debug(f"[State Machine] Stream update: {list(state_update.keys())}")

                    # Merge update into state
                    for key, value in state_update.items():
                        state[key] = value

                    # Yield updated state
                    yield state

            except asyncio.TimeoutError:
                logger.error(
                    f"[State Machine] Stream timeout (45s) for session {session_id}",
                    extra={"alert": True}
                )
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Przetwarzanie czatu przekroczyło limit czasu (45s). Spróbuj ponownie."
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"[State Machine] Stream failed for session {session_id}: {e}",
                exc_info=True,
            )
            raise

    async def initialize_session(self, state: ConversationState) -> ConversationState:
        """
        Inicjalizuje nową sesję (wywołuje welcome node).

        Args:
            state: Początkowy stan konwersacji

        Returns:
            ConversationState: Stan po welcome message
        """
        session_id = state.get("session_id", "unknown")
        logger.info(f"[State Machine] Initializing session {session_id}")

        try:
            # Run tylko welcome node
            result = await welcome_node(state)
            logger.info(f"[State Machine] Session {session_id} initialized")
            return result

        except Exception as e:
            logger.error(f"[State Machine] Failed to initialize session {session_id}: {e}")
            raise
