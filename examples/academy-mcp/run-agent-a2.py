import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

import academy.exchange
from academy.agent import Agent
from academy.agent import action
from academy.handle import Handle
from academy.exchange import RedisExchangeFactory, HttpExchangeFactory
from academy.manager import Manager
from academy.logging import init_logging
from academy.identifier import AgentId
import json
#from flowcept import Flowcept, flowcept_task
from flowcept.agents import ToolResult
#from flowcept.instrumentation.flowcept_decorator import flowcept

from academy_utils import async_run_tool

factory = RedisExchangeFactory(
    hostname="localhost",
    port=6379,
)

LOCAL_MCP_HOST = "localhost"
LOCAL_MCP_PORT = 8001

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

# agent_master_id = "27f6216e-092f-4eb1-86d6-2bac58abdeed"

class AgentMaster(Agent):
    pass


class AgentAnalyzer(Agent):
    agent2_tool_input_data: Dict = None

    async def agent_on_startup(self) -> None:
        await self._register(self.agent_id.uid)

    async def _register(self, agentId: uuid.UUID) -> None:
        logging.info(f"[AgentAnalyzer] register {agentId}")
        master_id = await self._discover()
        response = await Handle(master_id).register_agent(agentId)
        # response = await Handle(AgentId(uid=uuid.UUID(agent_master_id))).register_agent(agentId)
        logging.info(response)

    async def _discover(self) -> tuple[AgentId[Any], ...]:
        logging.info("Discovering...")
        master_ids = await self.agent_exchange_client.discover(
                            agent=AgentMaster,
                            allow_subclasses=False)
        logging.info(f"[Discover] AgentMaster IDs: {master_ids}")
        if len(master_ids) > 1:
            raise Exception("Too many masters.")
        elif not len(master_ids):
            raise Exception("There is no master.")

        return master_ids[0]

    async def run_local_tool(self) -> ToolResult:
        logging.info(f"[Agent 2] Gonna run local tool 'say_name'...")
        kwargs = None
        tool_result = await async_run_tool(tool_name="say_name", kwargs=kwargs, host=LOCAL_MCP_HOST, port=LOCAL_MCP_PORT)
        return tool_result

    @action
    async def agent_2_special_tool(self, tool_input_data: str) -> Dict:
        logging.info(f"Message from master: {tool_input_data}")
        self.agent2_tool_input_data = tool_input_data

        local_tool_result = await self.run_local_tool()

        resp = {
            "agent_id": str(self.agent_id.uid),
            "agent2_tool_input_data": self.agent2_tool_input_data,
            "agent2_tool_output_data": local_tool_result.result
        }
        return resp

    @action
    async def get_agent2_tool_input_data(self):
        return self.agent2_tool_input_data

#@flowcept()
async def main():
    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:
        hdl = await manager.launch(AgentAnalyzer)
        # await manager.wait([hdl])
        while await hdl.get_agent2_tool_input_data() == None:
            logging.info("Waiting for agent2 input data from master...")
            await asyncio.sleep(1)
        await hdl.shutdown()

if __name__ == "__main__":
    # raise SystemExit(asyncio.run(main()))
    asyncio.run(main())
    # Flowcept
    # prov_messages = Flowcept.read_buffer_file()
    # print(json.dumps(prov_messages, indent=2))

