import asyncio

import logging

from mistralai import Mistral
from mistralai.extra.run.context import RunContext
from mcp import StdioServerParameters
from mistralai.extra.mcp.stdio import MCPClientSTDIO
from pathlib import Path

from config import settings

from mistralai.types import BaseModel

logger = logging.getLogger(__name__)

# Set the current working directory and model to use
cwd = Path(__file__).parent
MODEL = "mistral-medium-latest"

async def main() -> None:
    # Initialize the Mistral client
    client = Mistral(settings.MISTRAL_API_KEY)

    print(cwd)

    # Define parameters for the local MCP server
    server_params = StdioServerParameters(
        command="python",
        args=[str((cwd / "mcp_server.py").resolve())],
        env=None,
    )

    # Create an agent to interact with Kimble
    kimble_agent = client.beta.agents.create(
        model=MODEL,
        name="Kimble agent",
        instructions='''
        You are a helpful HR assistant that helps users manage their HR tasks.
        You have access to Kimble HR system through the available tools.
        
        Guidelines:
        1. Be concise and professional
        2. Only use tools when necessary
        3. Verify inputs before execution
        4. Handle errors gracefully''',
        description="",
    )

    # Define the expected output format for results
    class AgentResult(BaseModel):
        result: str

    # Create a run context for the agent
    async with RunContext(
        agent_id=kimble_agent.id,
        output_format=AgentResult,
        continue_on_fn_error=True,
    ) as run_ctx:
        # Create and register an MCP client with the run context
        mcp_client = MCPClientSTDIO(stdio_params=server_params)
        await run_ctx.register_mcp_client(mcp_client=mcp_client)

        print("Type 'exit' to quit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                break

            run_result = await client.beta.conversations.run_async(
                run_ctx=run_ctx,
                inputs=user_input,
            )

            print("Kimble Agent:", run_result.output_as_model.result)

if __name__ == "__main__":
    asyncio.run(main())