import os
from threading import Thread
from time import sleep

import uvicorn

from src.opal_agent.agent_client import run_tool
from src.opal_agent.configs import AGENT_HOST, AGENT_PORT
from src.opal_agent.context_manager import mcp_agent
from src.opal_agent.tools import say_name


def main():
    """
    Start the MCP server.
    """
    def run():
        uvicorn.run(mcp_agent.streamable_http_app, host=AGENT_HOST, port=AGENT_PORT, lifespan="on")

    t = Thread(target=run)
    t.start()
    sleep(2)
    # Wake up tool call
    print(run_tool(say_name, host=AGENT_HOST, port=AGENT_PORT)[0])

    return t


if __name__ == "__main__":
    main()
