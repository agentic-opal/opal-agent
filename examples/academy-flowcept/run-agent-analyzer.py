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
from flowcept import Flowcept, flowcept_task
from flowcept.instrumentation.flowcept_decorator import flowcept


# factory = RedisExchangeFactory(
#     hostname="localhost",
#     port=6379,
# )
factory = RedisExchangeFactory(
    hostname="redis-stf053-demo.streamio.s3m.olcf.ornl.gov",
    port=443,
    username="stf053",
    password="VJVZafCVXmSvLEqN",
    ssl=True,
)

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
    simulation_data: Dict = None

    async def agent_on_startup(self) -> None:
        await self._register(self.agent_id.uid)

    async def _register(self, agentId: uuid.UUID) -> None:
        logging.info(f"[AgentAnalyzer] register {agentId}")
        master_id = await self._discover()
        response = await Handle(master_id[0]).register_agent(agentId)
        # response = await Handle(AgentId(uid=uuid.UUID(agent_master_id))).register_agent(agentId)
        logging.info(response)

    async def _discover(self) -> tuple[AgentId[Any], ...]:
        logging.info("Discovering...")
        master_id = await self.agent_exchange_client.discover(
                            agent=AgentMaster,
                            allow_subclasses=False)
        logging.info(f"[Discover] AgentMaster ID: {master_id}")
        return master_id

    @action
    #@flowcept_task
    async def consume_data(self, message: Dict) -> Dict:
        logging.info(f"Message from master: {message}")
        self.simulation_data = message
        resp = {
            "agent_id": str(self.agent_id.uid),
            "simulation_data": message
        }
        return resp

    @action
    async def get_simulation_data(self):
        return self.simulation_data

#@flowcept()
async def main():
    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:
        hdl = await manager.launch(AgentAnalyzer)
        # await manager.wait([hdl])
        while await hdl.get_simulation_data() == None:
            logging.info("Waiting for simulation results...")
            await asyncio.sleep(1)
        await hdl.shutdown()

if __name__ == "__main__":
    # raise SystemExit(asyncio.run(main()))
    asyncio.run(main())
    # Flowcept
    # prov_messages = Flowcept.read_buffer_file()
    # print(json.dumps(prov_messages, indent=2))

