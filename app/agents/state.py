from typing import List, Dict, Any, Optional, TypedDict


class AgentTraceStep(TypedDict):
    agent: str
    action: str
    thought: str
    tool_called: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_result: Optional[Any]


class AgentState(TypedDict):
    """LangGraph State representation for the multi-agent conversation."""
    query: str
    customer_id: Optional[int]
    customer_name: Optional[str]
    history: List[Dict[str, str]]
    next_agent: Optional[str]
    active_agent: Optional[str]
    agent_trace: List[Dict[str, Any]]
    order_data: Optional[Dict[str, Any]]
    menu_matches: Optional[List[Dict[str, Any]]]
    final_response: Optional[str]
    intent: Optional[str]
