import json
import logging
from typing import Any, Callable, Dict, List, Union

from academy.handle import Handle
from academy.identifier import AgentId
from flowcept.agents import ToolResult
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def async_run_remote_tool(remote_agent_uid: str, tool_name: str, remote_tool_kwargs: Dict = None) -> ToolResult:
    logging.info(f"AgentMaster will execute tool {tool_name} on peer agent.")
    handle = Handle(AgentId(uid=remote_agent_uid))
    _tool_func = getattr(handle, tool_name)
    tool_result: ToolResult = await _tool_func(**(remote_tool_kwargs or {}))
    logging.info(f"AgentMaster executed tool {tool_name} on peer agent.")
    logging.info(tool_result)
    return tool_result


async def async_run_tool(
    tool_name: Union[str, Callable],
    kwargs: Dict[str, Any] | None = None,
    host: str = "localhost",
    port: int = 8000,
) -> ToolResult:
    """
    Run a tool using an MCP client session via a local streamable HTTP connection.

    This version is async, so it can be awaited from other async functions.

    Parameters
    ----------
    tool_name : str or Callable
        The name of the tool to call within the MCP framework. If a callable is passed,
        its __name__ is used.
    kwargs : dict, optional
        Keyword arguments to pass to the tool.
    host : str
        MCP server host.
    port : int
        MCP server port.

    Returns
    -------
    list of str
        The tool response content flattened as strings.
    """
    if callable(tool_name):
        tool_name = tool_name.__name__

    if kwargs is None:
        kwargs = {}

    mcp_url = f"http://{host}:{port}/mcp"

    async with streamablehttp_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=kwargs)
            if hasattr(result, "content") and len(result.content) > 1:
                raise Exception("Not expected. Please make your tool return a ToolResult object.")

            item = result.content[0]
            actual_result = getattr(item, "text", str(item))
            return ToolResult(**json.loads(actual_result))


# example usage inside another async function:
# async def run_local_tool(self, tool_name: str, kwargs: Dict | None = None):
#     return await run_tool(tool_name=tool_name, kwargs=kwargs, host=AGENT_HOST, port=AGENT_PORT)
