"""
FastAPI server to bridge React ChatInterface with Python agent
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from pydantic import BaseModel

from mistralai import Mistral
from mistralai.extra.run.context import RunContext
from mcp import StdioServerParameters
from mistralai.extra.mcp.stdio import MCPClientSTDIO
from mistralai.types import BaseModel as MistralBaseModel

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="HR Assistant API", version="1.0.0")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Pydantic models for API
class ChatMessage(BaseModel):
    text: str
    sender: str = "user"
    timestamp: datetime = None

class ChatResponse(BaseModel):
    id: str
    text: str
    sender: str = "assistant"
    timestamp: datetime
    type: str = "response"

class AgentResult(MistralBaseModel):
    result: str

# Global variables for agent context
agent_context = None
client = None
cwd = Path(__file__).parent
MODEL = "mistral-medium-latest"

async def initialize_agent():
    """Initialize the HR agent with MCP client"""
    global agent_context, client
    
    try:
        client = Mistral(settings.MISTRAL_API_KEY)
        
        server_params = StdioServerParameters(
            command="python",
            args=[str((cwd / "mcp_server.py").resolve())],
            env=None,
        )

        # Create HR agent
        hr_agent = client.beta.agents.create(
            model=MODEL,
            name="Talan HR Assistant",
            instructions='''
            You are Talan's HR Assistant, an AI-powered agent that helps employees and HR professionals 
            manage HR-related tasks through the HR system.
            
            Core Responsibilities:
            1. Provide accurate and up-to-date HR information
            2. Assist with leave requests, employee data, and HR policy questions
            3. Guide users through HR processes and documentation
            4. Maintain strict data privacy and security standards
            
            Interaction Guidelines:
            - Be professional, empathetic, and concise
            - Verify all inputs before executing actions
            - Only use tools when necessary and with proper authorization
            - Clearly explain any errors and suggest solutions
            - Protect sensitive information and follow data protection policies
            - Escalate complex or sensitive issues to HR when appropriate
            
            When users ask about leave or absences, use the available tools to:
            - Check current absence status
            - Fill absence requests
            - Get week absence summaries
            - Submit weekly timesheets
            - Count absences in date ranges
            ''',
            description="Talan's AI-powered HR assistant that provides self-service HR capabilities through natural language interaction with the HR system. Handles employee queries, leave management, policy information, and HR process guidance.",
        )

        # Create run context
        run_ctx = RunContext(
            agent_id=hr_agent.id,
            output_format=AgentResult,
            continue_on_fn_error=True,
        )
        
        # Initialize MCP client
        mcp_client = MCPClientSTDIO(stdio_params=server_params)
        await run_ctx.__aenter__()
        await run_ctx.register_mcp_client(mcp_client=mcp_client)
        
        agent_context = run_ctx
        logger.info("HR Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize HR agent: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    await initialize_agent()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up agent context on shutdown"""
    global agent_context
    if agent_context:
        try:
            await agent_context.__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage) -> ChatResponse:
    """
    Handle chat messages from the React frontend
    """
    global agent_context, client
    
    if not agent_context or not client:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Process the message through the agent
        run_result = await client.beta.conversations.run_async(
            run_ctx=agent_context,
            inputs=message.text,
        )
        
        # Extract the response
        response_text = run_result.output_as_model.result
        
        return ChatResponse(
            id=f"msg_{datetime.now().timestamp()}",
            text=response_text,
            sender="assistant",
            timestamp=datetime.now(),
            type="response"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return ChatResponse(
            id=f"error_{datetime.now().timestamp()}",
            text=f"I apologize, but I encountered an error processing your request: {str(e)}",
            sender="assistant",
            timestamp=datetime.now(),
            type="error"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent_context is not None,
        "timestamp": datetime.now()
    }

@app.get("/api/agent/status")
async def agent_status():
    """Get agent status and available tools"""
    global agent_context
    
    if not agent_context:
        return {"status": "not_initialized", "tools": []}
    
    # List available tools from MCP server
    available_tools = [
        "fill_absence",
        "get_week_absences", 
        "submit_week",
        "is_absent",
        "get_absences",
        "count_absences"
    ]
    
    return {
        "status": "initialized",
        "tools": available_tools,
        "model": MODEL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
