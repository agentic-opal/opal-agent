import asyncio
import logging

from academy.manager import Manager
from appl_agent.academy_utils import async_run_tool
from appl_agent.backend.academy_master import AgentMaster
from appl_agent.configs import AGENT_HOST, AGENT_PORT


async def run():
    # ret = await async_run_tool("academy_tool", host=AGENT_HOST, port=AGENT_PORT)
    # print(ret)

    # ret = await async_run_tool("say_name", host=AGENT_HOST, port=AGENT_PORT)
    # print(ret)

    ret = await async_run_tool("academy_peer_tool2", host=AGENT_HOST, port=AGENT_PORT)
    print(ret)


if __name__ == "__main__":
    asyncio.run(run())
