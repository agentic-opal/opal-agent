import asyncio
import logging
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Tuple

from academy.agent import Agent
from academy.agent import action
from academy.handle import Handle
from academy.exchange import RedisExchangeFactory, HttpExchangeFactory
from academy.manager import Manager
from academy.logging import init_logging
from academy.identifier import AgentId

from flowcept.agents import ToolResult
from flowcept.flowcept_api.flowcept_controller import Flowcept
from flowcept.instrumentation.flowcept_decorator import flowcept
from flowcept.instrumentation.flowcept_task import flowcept_task

from academy_utils import async_run_tool

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
    peer_agent: uuid.UUID = None

    async def agent_on_startup(self) -> None:
        logging.info(f"AgentMaster ID: {self.agent_id.uid}")

    @action
    async def register_agent(self, agentId: uuid.UUID) -> str:
        logging.info(f"register_agent: {agentId}")
        self.peer_agent = agentId
        logging.info(f"Type of Agent_id: {type(agentId)}; AgentId: "+ str(agentId))
        return f"{agentId}"

    @action
    async def _get_peer_agent(self):
        return self.peer_agent

    @action
    async def say_name(self) -> ToolResult:
        logging.info(f"[Agent Master] Gonna execute my local tool 'say_name'...")
        tool_result = await async_run_tool(tool_name="say_name",
                                           kwargs=None,
                                           host=LOCAL_MCP_HOST,
                                           port=LOCAL_MCP_PORT)
        return tool_result

    @action
    async def echo(self, user_msg: str) -> ToolResult:
        logging.info(f"[Agent Master] Gonna execute my local tool 'echo'...")
        tool_result = await async_run_tool(tool_name="echo",
                                           kwargs={"user_msg": user_msg},
                                           host=LOCAL_MCP_HOST,
                                           port=LOCAL_MCP_PORT)
        return tool_result

    @flowcept_task
    async def execute_remote_tool(self, tool_name:str, remote_tool_kwargs: Dict=None, agent_uid=None) -> Dict:
        logging.info(f"AgentMaster will execute tool {tool_name} on peer agent.")
        handle = Handle(AgentId(uid=self.peer_agent))
        _tool_func = getattr(handle, tool_name)
        response: Dict = await _tool_func()
        logging.info(response)
        return response
        # return {
        #     "agent_id": str(self.agent_id.uid),
        #     "message": response
        # }

    async def start_interaction(self):
        logging.info("Started interaction")
        local_tool_result = await self.say_name()
        remote_tool_result = await self.execute_remote_tool(tool_name="say_name2", remote_tool_kwargs=None)
        logging.info(f"Remote Tool Result: {remote_tool_result}")

        logging.info(f"Sending Academy done to peer.")
        await self.execute_remote_tool(tool_name="academy_done", remote_tool_kwargs=None)

        return True



@flowcept
async def main():
    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:
        agent_master = AgentMaster()
        hdl = await manager.launch(agent_master)
        while await hdl._get_peer_agent() == None:
            logging.info("Waiting for peer to register...")
            await asyncio.sleep(1)
        await agent_master.start_interaction()

        logging.info("Waiting 5 s.")
        await asyncio.sleep(5)
        logging.info("Done waiting 5 s.")
        await hdl.shutdown()
        logging.info("Shutting down.")


if __name__ == "__main__":
    # Flowcept(save_workflow=False, start_persistence=False, check_safe_stops=False).start()
    asyncio.run(main())
    # Flowcept
    prov_messages = Flowcept.read_buffer_file()
    print(json.dumps(prov_messages, indent=2))

