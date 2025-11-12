import asyncio
import logging

from academy.manager import Manager
from appl_agent.academy_utils import async_run_tool
from appl_agent.backend.academy_master import AgentMaster
from appl_agent.configs import AGENT_HOST, AGENT_PORT


async def run():
    # ret = await async_run_tool("academy_tool", host=AGENT_HOST, port=AGENT_PORT)
    # print(ret)

    # ret = await async_run_tool("academy_tool", host=AGENT_HOST, port=AGENT_PORT)
    # print(ret)
    #
    # ret = await async_run_tool("say_name", host=AGENT_HOST, port=AGENT_PORT)
    # print(ret)

    ret = await async_run_tool("academy_peer_tool", host=AGENT_HOST, port=AGENT_PORT)
    print(ret)



# async def start_academy_master():
#     from concurrent.futures import ThreadPoolExecutor
#     from academy.logging import init_logging
#     from academy.exchange import RedisExchangeFactory
#     executor = ThreadPoolExecutor(
#         max_workers=3,
#         initializer=init_logging,
#     )
#
#     factory = RedisExchangeFactory(
#         hostname="localhost",
#         port=6379,
#     )
#
#     async with await Manager.from_exchange_factory(
#             factory=factory,
#             executors=executor,
#     ) as manager:
#         agent_master = AgentMaster()
#
#         # name = await agent_master.say_name()
#         # logging.info(f"Local say_name tool result: {name}")
#
#         hdl = await manager.launch(agent_master)
#         while await hdl._get_peer_agent() == None:
#             logging.info("Waiting for peer to register...")
#             await asyncio.sleep(1)
#
#         computational_workflow_plan = {
#             "plants": [21981, 21982],
#             "features": ["growth"],
#             "modality": "RGB1"
#         }
#         result = await agent_master.run_workflow_on_peer(computational_workflow_plan)
#         print(result)
#
#
#
#
#         # t = 1
#         # logging.info(f"Waiting {t} s.")
#         # await asyncio.sleep(t)
#         # await hdl.shutdown()
#         # logging.info("Shutting down.")


def main():
    """
    Start the MCP server.
    """

    asyncio.run(run())


if __name__ == "__main__":
    main()
