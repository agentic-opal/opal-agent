import asyncio
import logging
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

from academy.agent import Agent
from academy.agent import action
from academy.exchange import RedisExchangeFactory
from academy.manager import Manager
from academy.logging import init_logging

from flowcept.agents import ToolResult
from flowcept.flowcept_api.flowcept_controller import Flowcept
from flowcept.instrumentation.flowcept_decorator import flowcept
from flowcept.instrumentation.flowcept_task import flowcept_task

from academy_utils import async_run_tool, async_run_remote_tool

factory = RedisExchangeFactory(
    hostname="localhost",
    port=6379,
)

LOCAL_MCP_HOST = "localhost"
LOCAL_MCP_PORT = 8000

# factory = RedisExchangeFactory(
#     hostname="redis-stf053-demo.streamio.s3m.olcf.ornl.gov",
#     port=443,
#     username="stf053",
#     password="VJVZafCVXmSvLEqN",
#     ssl=True,
# )

# factory = HttpExchangeFactory(
#     "https://exchange.academy-agents.org",
#     auth_method="globus",
#     ssl_verify=True,
# )

executor = ThreadPoolExecutor(
    max_workers=3,
    initializer=init_logging,
)


class AgentMaster(Agent):
    peer_agent_uid: uuid.UUID = None

    async def agent_on_startup(self) -> None:
        logging.info(f"AgentMaster ID: {self.agent_id.uid}")

    @action
    async def register_agent(self, agentId: uuid.UUID) -> str:
        logging.info(f"register_agent: {agentId}")
        self.peer_agent_uid = agentId
        logging.info(f"Type of Agent_id: {type(agentId)}; AgentId: "+ str(agentId))
        return f"{agentId}"

    @action
    async def _get_peer_agent(self):
        return self.peer_agent_uid

    @flowcept_task
    @action
    async def say_name(self) -> ToolResult:
        logging.info(f"[Agent Master] Gonna execute my local tool 'say_name'...")
        tool_result = await async_run_tool(tool_name="say_name",
                                           kwargs=None,
                                           host=LOCAL_MCP_HOST,
                                           port=LOCAL_MCP_PORT)
        return tool_result

    @flowcept_task
    @action
    async def echo(self, user_msg: str) -> ToolResult:
        logging.info(f"[Agent Master] Gonna execute my local tool 'echo'... {user_msg}")
        tool_result = await async_run_tool(tool_name="echo",
                                           kwargs={"user_msg": user_msg},
                                           host=LOCAL_MCP_HOST,
                                           port=LOCAL_MCP_PORT)
        return tool_result

    async def start_interaction(self):
        logging.info("Started interaction")
        remote_tool_result = await async_run_remote_tool(remote_agent_uid=self.peer_agent_uid, tool_name="say_name")
        logging.info(f"SayName Remote Tool Result: {remote_tool_result}")
        remote_tool_result = await async_run_remote_tool(remote_agent_uid=self.peer_agent_uid,
                                                         tool_name="echo", remote_tool_kwargs={"user_msg": "hey!"})
        logging.info(f"Echo Remote Tool Result: {remote_tool_result}")

        logging.info(f"Sending Academy done to peer.")
        await async_run_remote_tool(remote_agent_uid=self.peer_agent_uid, tool_name="academy_done")

        return True


@flowcept
async def main():
    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:
        agent_master = AgentMaster()
        name = await agent_master.say_name()
        logging.info(f"Local say_name tool result: {name}")
        echo_msg = await agent_master.echo(user_msg="Local user msg text!")
        logging.info(f"Local echo tool result: {echo_msg}")

        hdl = await manager.launch(agent_master)
        while await hdl._get_peer_agent() == None:
            logging.info("Waiting for peer to register...")
            await asyncio.sleep(1)

        await agent_master.start_interaction()

        t = 1
        logging.info(f"Waiting {t} s.")
        await asyncio.sleep(t)
        await hdl.shutdown()
        logging.info("Shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
    # Flowcept
    prov_messages = Flowcept.read_buffer_file()
    print(json.dumps(prov_messages, indent=2))

