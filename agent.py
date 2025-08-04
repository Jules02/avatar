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

cwd = Path(__file__).parent
MODEL = "mistral-medium-latest"

async def main() -> None:
    client = Mistral(settings.MISTRAL_API_KEY)

    server_params = StdioServerParameters(
        command="python",
        args=[str((cwd / "mcp_server.py").resolve())],
        env=None,
    )

    # Create an agent to interact with Kimble HR system
    kimble_agent = client.beta.agents.create(
        model=MODEL,
        name="Talan HR Assistant (Kimble Integration)",
        instructions='''
        You are Talan's HR Assistant, an AI-powered agent that helps employees and HR professionals 
        manage HR-related tasks through the Kimble HR system.
        
        Core Responsibilities:
        1. Provide accurate and up-to-date HR information from Kimble
        2. Assist with leave requests, employee data, and HR policy questions
        3. Guide users through HR processes and documentation
        4. Maintain strict data privacy and security standards
        
        Interaction Guidelines:
        - Be professional, empathetic, and concise
        - Verify all inputs before executing actions
        - Only use tools when necessary and with proper authorization
        - Clearly explain any errors and suggest solutions
        - Protect sensitive information and follow data protection policies
        - Escalate complex or sensitive issues to HR when appropriate''',
        description="Talan's AI-powered HR assistant that provides self-service HR capabilities through natural language interaction with the Kimble HR system. Handles employee queries, leave management, policy information, and HR process guidance.",
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