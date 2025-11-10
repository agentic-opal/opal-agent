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
    registered_agent: uuid.UUID = None

    async def agent_on_startup(self) -> None:
        logging.info(f"AgentMaster ID: {self.agent_id.uid}")

    @action
    #@flowcept_task(output_names="agent_id")
    async def register_agent(self, agentId: uuid.UUID) -> str:
        logging.info(f"register_agent: {agentId}")
        self.registered_agent = agentId
        logging.info(f"Type of Agent_id: {type(agentId)}; AgentId: "+ str(agentId))
        return f"{agentId}"

    @action
    async def get_registered_agent(self):
        return self.registered_agent

    async def execute_local_tool(self) -> ToolResult:
        logging.info(f"[Agent Master] Gonna run tool 'say_name'...")
        kwargs = None
        tool_result = await async_run_tool(tool_name="say_name", kwargs=kwargs, host=LOCAL_MCP_HOST, port=LOCAL_MCP_PORT)
        return tool_result

    @flowcept_task
    async def execute_remote_tool(self, tool_input_data: Dict) -> Dict:
        logging.info(f"AgentMaster will send data to {self.registered_agent}")
        response: Dict = await Handle(AgentId(uid=self.registered_agent)).agent_2_special_tool(tool_input_data)
        logging.info(response)
        return response
        # return {
        #     "agent_id": str(self.agent_id.uid),
        #     "message": response
        # }

    async def start_interaction(self) -> Tuple[str, Dict]:
        logging.info("Started interaction")
        # self.agent_run_sync()
        # await asyncio.sleep(3)
        local_tool_result = await self.execute_local_tool()
        data = {"msg_from_agent": local_tool_result.result}
        remote_tool_result = await self.execute_remote_tool(data)
        logging.info(f"Remote Tool Result: {remote_tool_result}")
        return str(self.agent_id.uid), remote_tool_result



@flowcept
async def main():
    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:
        agent_master = AgentMaster()
        hdl = await manager.launch(agent_master)
        while await hdl.get_registered_agent() == None:
            logging.info("Waiting for peer to register...")
            await asyncio.sleep(1)
        await agent_master.start_interaction()
        # agent_master.agent_shutdown()

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

