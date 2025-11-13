"""
Study Designer Nodes - LangGraph conversation nodes

Wszystkie nodes konwersacji Study Designer Chat.
Każdy node przyjmuje ConversationState i zwraca zaktualizowany state.

V1 (legacy): 7 nodes (welcome → gather_goal → define_audience → select_method
             → configure_details → generate_plan → await_approval)

V2 (new): 3 nodes (welcome → conversation_extractor → generate_plan)
"""

# V1 nodes (legacy)
from .welcome import welcome_node
from .gather_goal import gather_goal_node
from .define_audience import define_audience_node
from .select_method import select_method_node
from .configure_details import configure_details_node
from .generate_plan import generate_plan_node
from .await_approval import await_approval_node

# V2 nodes (new)
from .conversation_extractor import conversation_extractor_node

__all__ = [
    # V1 (legacy)
    "welcome_node",
    "gather_goal_node",
    "define_audience_node",
    "select_method_node",
    "configure_details_node",
    "generate_plan_node",
    "await_approval_node",
    # V2 (new)
    "conversation_extractor_node",
]
