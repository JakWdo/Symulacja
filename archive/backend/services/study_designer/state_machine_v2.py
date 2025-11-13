"""
Study Designer State Machine V2 - Simplified Architecture

NOWA architektura z 3 nodes zamiast 7:
1. welcome → conversation_extractor → generate_plan

Zastępuje:
OLD (7 nodes): welcome → gather_goal → define_audience → select_method
               → configure_details → generate_plan → await_approval

NEW (3 nodes): welcome → conversation_extractor → generate_plan

Advantages:
- 5-9 LLM calls → 1-2 calls (-80% latency)
- Prostsza logika (mniej routing conditions)
- Gemini Pro dla critical extraction
- Lepsze JSON structured output

Usage:
    # W orchestrator.py
    from app.services.study_designer.state_machine_v2 import ConversationStateMachineV2

    state_machine = ConversationStateMachineV2()
    async for event in state_machine.process_message_stream(state):
        yield event
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal, AsyncGenerator, Any

from fastapi import HTTPException, status
from langgraph.graph import StateGraph, END
from app.services.study_designer.state_schema import ConversationState
from app.services.study_designer.nodes import (
    welcome_node,
    generate_plan_node,
)
from app.services.study_designer.nodes.conversation_extractor import (
    conversation_extractor_node,
)

logger = logging.getLogger(__name__)


class ConversationStateMachineV2:
    """
    LangGraph state machine V2 - Simplified architecture.

    Flow: welcome → conversation_extractor → generate_plan

    Attributes:
        graph: Skompilowany LangGraph StateGraph
        config: LangGraph config z timeout
    """

    # LangGraph config
    LANGGRAPH_CONFIG = {
        "recursion_limit": 25,  # Mniej niż v1 (50) bo prostszy graph
        "configurable": {},
    }

    # Timeout dla całego graph execution
    GRAPH_TIMEOUT = 60.0  # 60s (v1 miało 45s, ale teraz mamy caching więc można dać więcej)

    def __init__(self):
        """Inicjalizuje state machine V2 i buduje simplified graph."""
        self.graph = self._build_graph()
        logger.info(
            f"[State Machine V2] Initialized with {self.LANGGRAPH_CONFIG['recursion_limit']} recursion limit",
            extra={"version": "v2", "nodes": 3}
        )

    def _build_graph(self) -> StateGraph:
        """
        Buduje simplified LangGraph state graph.

        Nodes:
        - welcome: Powitalna wiadomość (bez LLM)
        - conversation_extractor: Multi-step extraction (1 LLM call)
        - generate_plan: Final plan generation (1 LLM call)

        Returns:
            Skompilowany StateGraph
        """
        workflow = StateGraph(ConversationState)

        # Add nodes
        workflow.add_node("welcome", welcome_node)
        workflow.add_node("conversation_extractor", conversation_extractor_node)
        workflow.add_node("generate_plan", generate_plan_node)

        # Set entry point
        workflow.set_entry_point("welcome")

        # Define edges
        # Welcome → conversation_extractor (always)
        workflow.add_edge("welcome", "conversation_extractor")

        # conversation_extractor → generate_plan OR loop back
        workflow.add_conditional_edges(
            "conversation_extractor",
            self._route_from_conversation_extractor,
            {
                "generate_plan": "generate_plan",
                "conversation_extractor": "conversation_extractor",  # Loop if extraction incomplete
            },
        )

        # generate_plan → END
        workflow.add_edge("generate_plan", END)

        # Compile
        compiled_graph = workflow.compile()

        logger.debug(
            "[State Machine V2] Graph compiled successfully",
            extra={
                "nodes": ["welcome", "conversation_extractor", "generate_plan"],
                "entry_point": "welcome"
            }
        )

        return compiled_graph

    def _route_from_conversation_extractor(
        self, state: ConversationState
    ) -> Literal["generate_plan", "conversation_extractor"]:
        """
        Routing decision z conversation_extractor node.

        Args:
            state: Aktualny stan konwersacji

        Returns:
            "generate_plan" jeśli extraction_complete
            "conversation_extractor" jeśli trzeba zadać follow-up
        """
        current_stage = state.get("current_stage", "conversation_extractor")

        logger.debug(
            f"[State Machine V2] Routing from conversation_extractor: stage={current_stage}"
        )

        if current_stage == "generate_plan":
            # Extraction complete → proceed to plan generation
            return "generate_plan"
        else:
            # Stay in conversation_extractor (need more info)
            return "conversation_extractor"

    async def process_message_stream(
        self, state: ConversationState
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Przetwarza wiadomość użytkownika i streamuje state updates.

        Args:
            state: Stan konwersacji z user message

        Yields:
            dict: State updates w formacie {node_name: state_delta}

        Raises:
            HTTPException: 500 jeśli graph execution failuje
            asyncio.TimeoutError: Jeśli przekroczono GRAPH_TIMEOUT
        """
        session_id = state["session_id"]

        logger.info(
            f"[State Machine V2] Processing message stream for session {session_id}",
            extra={
                "session_id": session_id,
                "current_stage": state.get("current_stage", "N/A")
            }
        )

        try:
            # Wrap graph execution w timeout
            async with asyncio.timeout(self.GRAPH_TIMEOUT):
                # Stream state updates from graph
                async for event in self.graph.astream(state, config=self.LANGGRAPH_CONFIG):
                    logger.debug(
                        f"[State Machine V2] Session {session_id}: Graph event",
                        extra={"event_keys": list(event.keys())}
                    )
                    yield event

            logger.info(
                f"[State Machine V2] Session {session_id}: Graph execution completed successfully"
            )

        except asyncio.TimeoutError:
            logger.error(
                f"[State Machine V2] Session {session_id}: TIMEOUT exceeded ({self.GRAPH_TIMEOUT}s)",
                extra={"session_id": session_id, "timeout": self.GRAPH_TIMEOUT}
            )
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail={
                    "error": "graph_timeout",
                    "message": f"Graph execution exceeded {self.GRAPH_TIMEOUT}s timeout",
                    "hint": "Try simplifying your request or breaking it into smaller parts"
                }
            )

        except Exception as e:
            logger.error(
                f"[State Machine V2] Session {session_id}: Graph execution failed: {e}",
                exc_info=True,
                extra={"session_id": session_id, "error_type": type(e).__name__}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "graph_execution_failed",
                    "message": "Failed to process message",
                    "hint": "Please try again or contact support if the problem persists"
                }
            )
