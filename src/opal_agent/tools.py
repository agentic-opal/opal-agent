from src.opal_agent.context_manager import mcp_agent


@mcp_agent.tool()
def say_name() -> str:
    return "My name is Opal Agent! :)"
