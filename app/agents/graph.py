from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.supervisor import SupervisorAgent
from app.agents.order_agent import OrderAgent
from app.agents.menu_agent import MenuAgent
from app.agents.support_agent import SupportAgent


supervisor = SupervisorAgent()
order_agent = OrderAgent()
menu_agent = MenuAgent()
support_agent = SupportAgent()


def supervisor_node(state: AgentState) -> AgentState:
    """Supervisor routing node."""
    return supervisor.route(state)


def order_agent_node(state: AgentState) -> AgentState:
    """Order specialist node."""
    return order_agent.execute(state)


def menu_agent_node(state: AgentState) -> AgentState:
    """Menu vector search specialist node."""
    return menu_agent.execute(state)


def support_agent_node(state: AgentState) -> AgentState:
    """Support & FAQ node."""
    return support_agent.execute(state)


def route_decision(state: AgentState) -> str:
    """Conditional edge router based on supervisor's intent decision."""
    next_agent = state.get("next_agent", "menu_agent")
    if next_agent == "order_agent":
        return "order_agent_node"
    elif next_agent == "support_agent":
        return "support_agent_node"
    else:
        return "menu_agent_node"


# Build the LangGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("order_agent_node", order_agent_node)
workflow.add_node("menu_agent_node", menu_agent_node)
workflow.add_node("support_agent_node", support_agent_node)

# Set Entry Point
workflow.set_entry_point("supervisor_node")

# Conditional routing from supervisor
workflow.add_conditional_edges(
    "supervisor_node",
    route_decision,
    {
        "order_agent_node": "order_agent_node",
        "menu_agent_node": "menu_agent_node",
        "support_agent_node": "support_agent_node"
    }
)

# Terminate after specialist agent completes
workflow.add_edge("order_agent_node", END)
workflow.add_edge("menu_agent_node", END)
workflow.add_edge("support_agent_node", END)

# Compile LangGraph application
agent_app = workflow.compile()


def run_multi_agent_chat(
    query: str,
    customer_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Main invocation entrypoint for the multi-agent chat assistant.
    Executes the LangGraph workflow and returns comprehensive response,
    agent execution traces, and structured UI components.
    """
    print("run_multi_agent_chat: called......")
    initial_state: AgentState = {
        "query": query,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "history": history or [],
        "next_agent": None,
        "active_agent": None,
        "agent_trace": [],
        "order_data": None,
        "menu_matches": None,
        "final_response": None,
        "intent": None
    }

    result_state = agent_app.invoke(initial_state)

    return {
        "response": result_state.get("final_response", "I have processed your request."),
        "active_agent": result_state.get("active_agent", "Assistant"),
        "intent": result_state.get("intent", "GENERAL"),
        "agent_trace": result_state.get("agent_trace", []),
        "order_data": result_state.get("order_data"),
        "menu_matches": result_state.get("menu_matches")
    }
