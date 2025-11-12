import asyncio
import logging
import uuid
from typing import Any

from academy.agent import Agent, action
from academy.handle import Handle
from academy.identifier import AgentId
from academy.manager import Manager
from flowcept.agents import ToolResult

from src.opal_agent.configs import AGENT_HOST, AGENT_PORT

from mcp.server.fastmcp import FastMCP

mcp_agent = FastMCP("MCPServerTest", stateless_http=True)


@mcp_agent.tool()
async def say_name() -> ToolResult:
    return ToolResult(code=201, result="My name is MCP Server! :)")


@mcp_agent.tool()
async def academy_tool() -> ToolResult:
    academy_agent_id = mcp_agent.academy_agent1_id
    response = await Handle(academy_agent_id).say_name()
    print(response)
    return response


@mcp_agent.tool()
async def academy_peer_tool() -> ToolResult:
    academy_agent_id = mcp_agent.academy_agent2_id
    response = await Handle(academy_agent_id).say_name_agent2()
    print(response)
    return response


@mcp_agent.tool()
async def academy_peer_tool2() -> ToolResult:
    academy_agent1_handle = mcp_agent.academy_agent1_handle
    while (peer_agent_id := await academy_agent1_handle.get_peer_agent_id()) == None:
        logging.info("Waiting for peer agent to register...")
        await asyncio.sleep(1)

    print("This is the peer id", peer_agent_id)
    setattr(mcp_agent, "academy_agent2_id", peer_agent_id)
    response = await Handle(peer_agent_id).say_name_agent2()
    print(response)
    return response


class Agent1(Agent):
    peer_agent_id: AgentId = None

    async def agent_on_startup(self) -> None:
        logging.info(f"Agent1 ID: {self.agent_id.uid}")
        await self._discover()

    async def get_agent_id(self) -> AgentId:
        return self.agent_id

    async def _discover(self) -> tuple[AgentId[Any], ...]:
        logging.info("Discovering...")
        master_ids = await self.agent_exchange_client.discover(
                            agent=Agent1,
                            allow_subclasses=False)
        logging.info(f"[Discover] AgentMaster IDs: {master_ids}")
        if len(master_ids) > 1:
            logging.warning("Too many masters. We killed them all. Start the whole thing. This is a temp workaround.")
            for m_id in master_ids:
                if self.agent_id != m_id:
                    await self.agent_exchange_client.terminate(m_id)

        elif not len(master_ids):
            raise Exception("There is no master.")
        #master_id = AgentId(uid=master_ids[0])

        #assert isinstance(master_id, AgentId), "Not expected ID type"
        master_id = master_ids[0]
        assert isinstance(master_id, AgentId), "Not expected ID type"

        assert master_id == self.agent_id, "Master ids are different!"
        logging.info(f"Master id is good! {master_id}")
        return master_id
    @action
    async def register_agent(self, agentId: AgentId) -> str:
        logging.info(f"register_agent: {agentId}")
        self.peer_agent_id = agentId
        logging.info(f"Type of Agent_id: {type(agentId)}; AgentId: "+ str(agentId))
        return f"{agentId}"

    @action
    async def get_peer_agent_id(self):
        return self.peer_agent_id

    @action
    async def say_name(self) -> ToolResult:
        return ToolResult(code=201, result="AcademyAgent")


async def main():
    from concurrent.futures import ThreadPoolExecutor
    from academy.logging import init_logging
    from academy.exchange import RedisExchangeFactory
    executor = ThreadPoolExecutor(
        max_workers=3,
        initializer=init_logging,
    )
    factory = RedisExchangeFactory(
        hostname="localhost",
        port=6379,
    )

    async with await Manager.from_exchange_factory(
            factory=factory,
            executors=executor,
    ) as manager:

        handle = await manager.launch(Agent1)
        while (agent1_id := handle.agent_id) == None:
            logging.info("Waiting to initialize...")
            await asyncio.sleep(1)

        # while (peer_agent_id := await handle.get_peer_agent_id()) == None:
        #     logging.info("Waiting for peer to register...")
        #     await asyncio.sleep(1)

        print("This is the master id", agent1_id)

        setattr(mcp_agent, "academy_agent1_id", agent1_id)
        setattr(mcp_agent, "academy_agent1_handle", handle)

        from uvicorn import Config, Server
        config = Config(
            app=mcp_agent.streamable_http_app,
            host=AGENT_HOST,
            port=AGENT_PORT,
            lifespan="on",
        )
        mcp_server = Server(config)
        await mcp_server.serve()


if __name__ == "__main__":
    asyncio.run(main())
