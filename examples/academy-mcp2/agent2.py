import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from academy.agent import Agent
from academy.agent import action
from academy.handle import Handle
from academy.exchange import RedisExchangeFactory
from academy.manager import Manager
from academy.logging import init_logging
from academy.identifier import AgentId

from flowcept.agents import ToolResult

factory = RedisExchangeFactory(
    hostname="localhost",
    port=6379,
)

LOCAL_MCP_HOST = "localhost"
LOCAL_MCP_PORT = 8001

executor = ThreadPoolExecutor(
    max_workers=3,
    initializer=init_logging,
)


class Agent1(Agent):
    pass


class Agent2(Agent):

    academy_done_flag = False

    async def get_agent_id(self):
        return self.agent.agent_id

    async def agent_on_startup(self) -> None:
        await self._register()

    async def _register(self) -> None:
        logging.info(f"[Agent2] registering...")
        master_id = await self._discover()
        response = await Handle(master_id).register_agent(self.agent_id)
        logging.info(response)

    async def _discover(self) -> tuple[AgentId[Any], ...]:
        logging.info("Discovering...")
        master_ids = await self.agent_exchange_client.discover(
                            agent=Agent1,
                            allow_subclasses=False)
        logging.info(f"[Discover] AgentMaster IDs: {master_ids}")
        if len(master_ids) > 1:
            for m_id in master_ids:
                await self.agent_exchange_client.terminate(m_id)
                logging.warning("Too many masters. We killed them all. Start the whole thing. This is a temp workaround.")
        elif not len(master_ids):
            raise Exception("There is no master.")

        return master_ids[0]

    @action
    async def say_name_agent2(self) -> ToolResult:
        logging.info(f"[Agent 2] exec say_name")
        return ToolResult(code=201, result="I'm agent 2.")

    @action
    async def academy_done(self) -> ToolResult:
        logging.info(f"[Agent 2] Received done signal!")
        self.academy_done_flag = True
        return ToolResult(code=201, result="true")

    @action
    async def get_academy_done_flag(self):
        return self.academy_done_flag

async def main():
    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:
        hdl = await manager.launch(Agent2)
        while not await hdl.get_academy_done_flag():
            logging.info("Waiting for Done signal from master...")
            await asyncio.sleep(1)
        await hdl.shutdown()

if __name__ == "__main__":
    # raise SystemExit(asyncio.run(main()))
    asyncio.run(main())
    # Flowcept
    # prov_messages = Flowcept.read_buffer_file()
    # print(json.dumps(prov_messages, indent=2))

