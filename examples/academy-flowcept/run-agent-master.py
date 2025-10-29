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
from flowcept import flowcept_task
from flowcept.instrumentation.flowcept_decorator import flowcept
from flowcept.flowcept_api.flowcept_controller import Flowcept

factory = RedisExchangeFactory(
    hostname="localhost",
    port=6379,
)

# factory = HttpExchangeFactory(
#     "https://exchange.academy-agents.org",
#     auth_method="globus",
#     ssl_verify=False,
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
    @flowcept_task(output_names="agent_id")
    async def register_agent(self, agentId: uuid.UUID) -> str:
        logging.info(f"register_agent: {agentId}")
        self.registered_agent = agentId
        logging.info(f"Type of Agent_id: {type(agentId)}; AgentId: "+ str(agentId))
        return f"{agentId}"

    @action
    async def get_registered_agent(self):
        return self.registered_agent

    @flowcept_task
    async def send_message(self, message: Dict) -> Dict:
        logging.info(f"AgentMaster will send message to {self.registered_agent}")
        response = await Handle(AgentId(uid=self.registered_agent)).consume_data(message)
        logging.info(response)
        return {
            "agent_id": str(self.agent_id.uid),
            "message": response
        }

    @flowcept_task(output_names=["agent_id", "out_simulation"])
    async def start_simulation(self) -> Tuple[str, Dict]:
        logging.info("Simulation is running...")
        # self.agent_run_sync()
        await asyncio.sleep(3)
        sim_result = {"a": 1, "b": 2}
        logging.info("Simulation completed!")
        await self.send_message(sim_result)
        logging.info(f"Simulation result: {sim_result}")
        return str(self.agent_id.uid), sim_result

@flowcept
async def main():
    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:
        agent_manager = AgentMaster()
        hdl = await manager.launch(agent_manager)
        while await hdl.get_registered_agent() == None:
            logging.info("Waiting for peer to register...")
            await asyncio.sleep(1)
        await agent_manager.start_simulation()
        # agent_manager.agent_shutdown()
        await asyncio.sleep(5)
        await hdl.shutdown()
        # await manager.wait([hdl])


if __name__ == "__main__":
    # Flowcept(save_workflow=False, start_persistence=False, check_safe_stops=False).start()
    asyncio.run(main())
    # Flowcept
    prov_messages = Flowcept.read_buffer_file()
    print(json.dumps(prov_messages, indent=2))
